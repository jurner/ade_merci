import pandas as pd
import ast
from datetime import timedelta
import numpy as np
import ast
from shapely.geometry import Point, LineString
from geopy.distance import geodesic

# read and sort data
tpl = pd.read_csv('./data/finished_tpl.csv')
sp = pd.read_csv('./data/finished_sp.csv')

tpl.sort_values('started', inplace=True)
sp.sort_values('started', inplace=True)
sp['duration'] = (sp.finished-sp.started)/60


# create a linear df with every recorded coord and ts as one line
for i, obj in tpl.iterrows():
    path = ast.literal_eval(obj['path'])
    tpl.at[i, 'start_lon'] = path[0][0]
    tpl.at[i, 'start_lat'] = path[0][1]
    tpl.at[i, 'end_lon'] = path[-1][0]
    tpl.at[i, 'end_lat'] = path[-1][1]
tpl['type'] = 'tpl'


sp['start_lon'] = sp['lon']
sp['start_lat'] = sp['lat']
sp['end_lon'] = sp['lon']
sp['end_lat'] = sp['lat']
sp['type'] = 'sp'

cols = ['started_at', 'finished_at', 'start_lon',
        'start_lat', 'end_lon', 'end_lat', 'type']
df = sp[cols].append(tpl[cols])

df['started_at'] = pd.to_datetime(df['started_at'])
df['finished_at'] = pd.to_datetime(df['finished_at'])
df.sort_values('started_at', inplace=True)


# get temporal gap
df['temp_gap'] = (df['started_at'].shift(-1) -
                  df['finished_at'])/timedelta(hours=1)

# get data from next row
df['next_type'] = df['type'].shift(-1)
df['next_start'] = df['started_at'].shift(-1)

df['next_st_lon'] = df['start_lon'].shift(-1)
df['next_st_lat'] = df['start_lat'].shift(-1)

for i, obj in df.iterrows():
    start_pt = Point(obj['end_lon'], obj['end_lat'])
    end_pt = Point(obj['next_st_lon'], obj['next_st_lat'])
    try:
        df.at[i, 'gap_geom'] = LineString([start_pt, end_pt])
        df.at[i, 'types'] = obj['type'] + ' ' + obj['next_type']

    except:
        df.at[i, 'gap_geom'] = LineString()
        df.at[i, 'types'] = 'nothing'

df.dropna(inplace=True)

# Calculate the distance between consecutive rows using geodesic function
df['gap_distance'] = df.apply(
    lambda row: geodesic(
        (row['end_lat'], row['end_lon']),
        (row['next_st_lat'], row['next_st_lon'])
    ).meters,
    axis=1
)

# Create gaps and export as csv
df['path'] = df.apply(lambda row: [[row['end_lon'], row['end_lat']], [
                      row['next_st_lon'], row['next_st_lat']]], axis=1)
df_new = df[['finished_at', 'next_start',
             'temp_gap', 'gap_distance', 'gap_geom', 'path']]
df_new.columns = ['started_at', 'finished_at',
                  'gap_minutes', 'gap_distance', 'geometry', 'path']
df_new.loc[(df_new['gap_distance'] > 500) | (
    df_new['gap_minutes'] > 0)].to_csv('./data/gaps_finished.csv')
