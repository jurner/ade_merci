import pandas as pd
import ast
from datetime import timedelta
from haversine import haversine, Unit
from scipy.ndimage import gaussian_filter1d
import numpy as np
import ast
import json



# read and sort data
tpl = pd.read_csv('./data/finished_tpl.csv')
sp = pd.read_csv('./data/finished_sp.csv')

tpl.sort_values('started', inplace=True)
sp.sort_values('started', inplace=True)


# create a linear df with every recorded coord and ts as one line
paths = []
dates = []
types = []
for i, obj in tpl.iterrows():
    path = ast.literal_eval(obj['path'])
    paths+=path
    dts = ast.literal_eval(obj['datetimes_unix'])
    dates+= dts
    types+= [obj['activity'] for i  in range(len(dts))]

for i, obj in sp.iterrows():
    paths.append([obj['lon'], obj['lat']])
    dates.append(obj['started'])
    types.append('sp')

    paths.append([obj['lon'], obj['lat']])
    dates.append(obj['finished'])
    types.append('sp')

df = pd.DataFrame({'date':dates, 'coords':paths, 'types':types})
df['lon'] = df['coords'].apply(lambda x: x[0])
df['lat'] = df['coords'].apply(lambda x: x[1])


# create a daterange from min to max and create a df
min_dt = int(df['date'].min())
max_dt = int(df['date'].max())
all_dts = [i for i in range(min_dt, max_dt+1)]
df_dt = pd.DataFrame({'all_dts':all_dts})


# merge the data to the daterange
merged = df_dt.merge(df, left_on='all_dts', right_on='date', how='left')
merged.drop(columns =['date', 'coords'], inplace=True)


# interpolate the missing valued
merged.sort_values('all_dts', inplace=True)
fin = merged.interpolate()


def calculate_speed_fast(df):
    # Calculate the time difference between consecutive rows in seconds
    df['time_diff'] = (df['timestamp'] - df['timestamp'].shift()).fillna(pd.Timedelta(seconds=0))
    df['time_diff'] = df['time_diff'].dt.total_seconds()
    
    # Convert latitude and longitude to radians
    lat1, lon1 = np.radians(df['lat'].shift()), np.radians(df['lon'].shift())
    lat2, lon2 = np.radians(df['lat']), np.radians(df['lon'])
    
    # Calculate the distance between consecutive rows using the Haversine formula
    R = 6371  # Earth's radius in km
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    df['distance'] = R * c
    
    # Calculate the speed in km/h
    df['speed'] = df['distance'] / (df['time_diff'] / 3600)
    
    return df

df = fin
df['timestamp'] = pd.to_datetime(df['all_dts'],unit='s')

df = calculate_speed_fast(df)


# resample the data
df = df.resample('3600S', on='timestamp')['speed'].median().reset_index()


def add_gaussian_filter(df, column_name, sigma=1, threshold=3):
    """
    Applies a Gaussian filter to a column in a Pandas DataFrame after removing outliers and adds the filtered result as a new column.

    Args:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): The name of the column to filter.
        sigma (float): The standard deviation of the Gaussian kernel. Defaults to 1.
        threshold (int or float): The number of standard deviations to use as a threshold for identifying outliers. Defaults to 3.

    Returns:
        pd.DataFrame: A new DataFrame with the filtered column added.
    """
    # Calculate the z-scores for the data in the specified column
    z_scores = np.abs((df[column_name] - df[column_name].mean()) / df[column_name].std())

    # Identify outliers based on the z-scores and the specified threshold
    is_outlier = z_scores > threshold

    # Replace outliers with NaN values
    df[column_name][is_outlier] = np.nan

    # Apply the Gaussian filter to the specified column
    filtered_data = gaussian_filter1d(df[column_name], sigma)

    # Add the filtered data as a new column to the DataFrame
    new_column_name = f"{column_name}_filtered"
    df[new_column_name] = filtered_data

    return df

df = add_gaussian_filter(df, 'speed')


def calculate_zoom_level(df):
    """
    Calculates the Mapbox zoom level based on the filtered speed in a DataFrame.
    The faster the speed, the more zoomed out the map should be.
    The slower the speed, the more zoomed in the map should be.
    The zoom level is calculated as a continuous value between 8 and 14.
    Adds a new column to the DataFrame called 'zoom_level'.
    """
    # Calculate zoom levels based on filtered speed
    df['speed_filtered'] = df['speed_filtered'].bfill()
    df['speed_filtered'] = df['speed_filtered'].ffill()
    speed_filtered = df['speed_filtered'].fillna(0)  # Fill NaN values with 0
    zoom_levels = np.interp(np.log(speed_filtered + 1), [0, np.log(df['speed_filtered'].max() + 1)], [13, 7])
    
    # Round zoom levels to two decimal places
    zoom_levels = np.round(zoom_levels, 2)
    
    # Add zoom levels to DataFrame
    df['zoom_level'] = zoom_levels
    
    return df


df = calculate_zoom_level(df)


# group column on type change
fin['types_new'] = fin['types'].ffill()
fin['change'] = fin['types_new']!=fin['types_new'].shift(-1)
fin['group'] = fin['change'].cumsum()


# get min and max and distance
min_max = fin.groupby('group', as_index=False).agg({'timestamp':['min', 'max'], 'distance':'sum'})
min_max['duration'] = min_max['timestamp']['max']-min_max['timestamp']['min']
min_max['duration'] = min_max['duration'] / timedelta(hours=1)
cols = ['group', 'duration', 'distance']
min_max = min_max[cols]
min_max.columns = cols

fin.drop(columns = ['distance'], inplace=True)
fin = fin.merge(min_max[['group', 'duration', 'distance']], on='group', how='left')

# merge data
df_new = df.merge(fin[['timestamp','all_dts', 'lon','lat', 'distance', 'speed','duration', 'types_new']], on='timestamp')

# remove zoom level of staypoint, interpolate between last and next and reduce by one
df_new.loc[df_new['types_new']=='sp', 'zoom_level'] = None
df_new['zoom_level'] = df_new['zoom_level'].interpolate()
df_new.loc[df_new['types_new']=='sp', 'zoom_level'] = df_new['zoom_level']+1

# rolling mean for zoom level
df_new['zoom_level_run'] = df_new['zoom_level'].rolling(12).mean()
df_new['zoom_level_run'] = df_new['zoom_level_run'].ffill()
df_new['zoom_level_run'] = df_new['zoom_level_run'].bfill()
df_new['zoom_level_run'] = df_new['zoom_level_run'].fillna(8)

# for trips longer than 2.5h set zoom to 8
df_new.loc[(df_new['types_new'].isin(['CYCLING', 'WALKING','IN_FERRY','sp'])==False) & (df_new['duration']>2.5) , 'zoom_level_run'] = 8

# set one hour in advance and smoothen lon lat
df_new['lat_old'] = df_new['lat']
df_new['lon_old'] = df_new['lon']

df_new['lon'] = df_new['lon'].shift(-1)
df_new['lat'] = df_new['lat'].shift(-1)

df_new['lon'] = df_new['lon'].rolling(3, center = True).mean()
df_new['lat'] = df_new['lat'].rolling(3, center = True).mean()

df_new.loc[df_new['lat'].isna(), 'lat'] = df_new['lat_old']
df_new.loc[df_new['lon'].isna(), 'lon'] = df_new['lon_old']

df_new.loc[df_new['lon'].isna(), 'lon'] = df_new['lon_old']
df_new.drop(columns=['lat_old', 'lon_old'], inplace=True)

# change camera for flights
flights = tpl.loc[tpl['activity']=='FLYING']
flights['started_at'] = pd.to_datetime(flights['started_at']).dt.tz_localize(None)
flights['finished_at'] = pd.to_datetime(flights['finished_at']).dt.tz_localize(None)
flights['started_hour'] = flights['started_at'].apply(lambda x: x.replace(microsecond=0, second=0, minute=0))
flights['finished_hour'] = flights['finished_at'].apply(lambda x: x.replace(microsecond=0, second=0, minute=0))
flights['finished_hour']  =  flights['finished_hour']+ timedelta(hours = 1)

df_chan = df_new
df_chan['timestamp'] = pd.to_datetime(df_chan['timestamp']).dt.tz_localize(None)
df_chan['duration'] = 3600
df_chan['pitch'] = 0
df_chan['curve'] = 0.1


for i, obj in flights.iterrows():
    lon = ast.literal_eval(obj['path'])[1][0]
    lat = ast.literal_eval(obj['path'])[1][1]

    started = obj['started_hour']
    finished = obj['finished_hour']
    hours = (finished-started) / timedelta(hours=1)

    df_chan = df_chan.loc[(df_chan['timestamp']<=started) | (df_chan['timestamp']>=finished)]
    df_chan.loc[df_chan['timestamp']==started, 'zoom_level_run'] = 11
    df_chan.loc[df_chan['timestamp']==started, 'pitch'] = 35
    df_chan.loc[df_chan['timestamp']==started, 'duration'] = hours*3600
    df_chan.loc[df_chan['timestamp']==started, 'lon'] = lon
    df_chan.loc[df_chan['timestamp']==started, 'lat'] = lat
    df_chan.loc[df_chan['curve']==started, 'lat'] = 5


# create deck_arr
deck_arr = []
for i, obj in df_chan.iterrows():
    js = {} 
    js['timestamp'] = obj['all_dts']
    js['go_to_coord'] = [obj['lon'], obj['lat']]
    js['duration'] = obj['duration']
    js['zoom']= obj['zoom_level_run']
    js['pitch'] = obj['pitch']
    js['distance'] = obj['distance']
    js['curve'] = obj['curve']
    

    deck_arr.append(js)

with open("../src/data/camera.json", "w") as outfile:
    json.dump(deck_arr, outfile)