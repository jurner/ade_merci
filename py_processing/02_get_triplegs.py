from math import atan2, degrees
import pandas as pd
import json
from shapely.geometry import Point, LineString
import geopandas as gpd
import json
import requests
import pandas as pd
import numpy as np
import json
from datetime import datetime as dt, timedelta
import time
import shapely
import pymongo
from os import listdir
from os.path import isfile, join

with open('../src/private.json') as f:
    # Load the JSON data
    keys = json.load(f)

# set start and end date
start = pd.to_datetime('2023-01-31 13:00:00.000000+00:00')
end = pd.to_datetime('2023-09-1 23:59:00.000000+00:00')

# get semantic info from google raw data


def get_semantic_info(path):
    act_arr = []
    # read file path
    with open(path, 'r', encoding="utf8") as j:
        contents = json.loads(j.read())
    # sort activities and places
    activity = []
    for obj in contents['timelineObjects']:
        if 'activitySegment' in obj.keys():
            activity.append(obj['activitySegment'])

    # create a df with start, end, activity_type and duration
    for obj in activity:
        start_dt = pd.to_datetime(obj['duration']['startTimestamp'])
        end_dt = pd.to_datetime(obj['duration']['endTimestamp'])
        activity = obj['activityType']
        try:
            distance = obj['distance']
        except:
            distance = 0

        if activity == 'FLYING':
            start_pt = Point(obj['startLocation']['longitudeE7'] /
                             10**7, obj['startLocation']['latitudeE7']/10**7)
            end_pt = Point(obj['endLocation']['longitudeE7'] /
                           10**7, obj['endLocation']['latitudeE7']/10**7)
            fly_geom = LineString([start_pt, end_pt])
        else:
            fly_geom = LineString()
        act_arr.append([start_dt, end_dt, activity, distance, fly_geom])

    df_act = pd.DataFrame(data=act_arr, columns=[
                          'started_at', 'finished_at', 'activity', 'distance', 'fly_geom'])

    return df_act


# get all files names in 2023 folder
mypath = "./raw_data/Semantic Location History/2023"
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print(onlyfiles)
df_act = pd.DataFrame()

# loop through files in 2023 folder
for file in onlyfiles:
    df_act = df_act.append(get_semantic_info("{}/{}".format(mypath, file)))

df_act = df_act.loc[(df_act['started_at'] >= start) &
                    (df_act['finished_at'] <= end)]
df_act['path'] = None
df_act['datetime'] = None

# merge two activities if data error
# def merge_two(time_of_first):
#     to_merge = df_act.loc[df_act['started_at']>=pd.to_datetime(time_of_first)][0:2]
#     first_ind = to_merge.index[0]
#     second_ind = to_merge.index[1]
#     df_act.at[first_ind, 'finished_at']  = df_act.at[second_ind, 'finished_at']
#     df_act.drop(second_ind, inplace = True)
#     return df_act

# train overnight
# df_act = merge_two('2022-11-07 18:00:02.331000+00:00')

# prepare gps logs from google raw_data


def prepare_records_json(path):
    df_gps = pd.read_json(path)
    print('There are {:,} rows in the location history dataset'.format(
        len(df_gps)))

    # enrich - get attributes
    df_gps['lat'] = df_gps['locations'].map(
        lambda x: x['latitudeE7'] if 'latitudeE7' in x.keys() else None)
    df_gps['lon'] = df_gps['locations'].map(
        lambda x: x['longitudeE7'] if 'longitudeE7' in x.keys() else None)
    df_gps.dropna(subset=['lat', 'lon'], inplace=True)

    df_gps['accuracy'] = df_gps['locations'].map(lambda x: x['accuracy'])

    df_gps['lat'] = df_gps['lat'] / 10.**7
    df_gps['lon'] = df_gps['lon'] / 10.**7
    df_gps['timestamp'] = df_gps['locations'].map(lambda x: x['timestamp'])
    df_gps['datetime'] = pd.to_datetime(df_gps['timestamp'])
    df_gps['seconds'] = df_gps['datetime'].apply(
        lambda x: x.hour*60*60+x.minute*60+x.second)
    df_gps['date'] = df_gps['datetime'].dt.date
    return df_gps


# add geometries to df
rec_path = "./raw_data/Records.json"
rec_path_gina = "./raw_data/Records_gina.json"

# load
df_gps = prepare_records_json(rec_path)
df_gps_g = prepare_records_json(rec_path_gina)


# calculate azimuth


def get_azimuth(lat1, lon1, lat2, lon2):
    dlon = lon2 - lon1
    y = np.sin(dlon) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * \
        np.cos(lat2) * np.cos(dlon)
    azimuth = degrees(atan2(y, x))
    return (azimuth + 360) % 360


def remove_outliers(df):
    # Shift the latitude and longitude columns by one row to get the next point's coordinates
    try:
        df['lat_shifted'] = df['lat'].shift(-1)
        df['lon_shifted'] = df['lon'].shift(-1)

        # Calculate azimuth between consecutive points row by row
        df['azimuth'] = df.apply(lambda row: get_azimuth(
            row['lat'], row['lon'], row['lat_shifted'], row['lon_shifted']), axis=1)

        # Remove the last row since there is no next point for it
        df['azimuth'].fillna(method='ffill', inplace=True)

        # Remove the intermediate shifted columns
        df.drop(['lat_shifted', 'lon_shifted'], axis=1, inplace=True)

        df['azimuth_last'] = df['azimuth'].shift()
        df['azimuth_last'].fillna(method='bfill', inplace=True)

    except:
        df['azimuth'] = 0
        df['azimuth_last'] = 0

    df['az_diff'] = abs(df.azimuth - df.azimuth_last)
    df = df.loc[(df['az_diff'] > 165) & (df['az_diff'] < 195)]

    # Return the DataFrame with azimuth values
    return df


def get_record_data(df, path, accuracy):

    line_string_arr = []
    df.reset_index(inplace=True)
    ct = 0

    for i, obj in df.iterrows():

        # filter objects
        df_p = df_gps.loc[(df_gps['datetime'] >= obj['started_at']) & (
            df_gps['datetime'] <= obj['finished_at']) & (df_gps['accuracy'] <= accuracy)]

        # if gina_data has more entries replace mine
        df_p_g = df_gps_g.loc[(df_gps_g['datetime'] >= obj['started_at']) & (
            df_gps_g['datetime'] <= obj['finished_at']) & (df_gps_g['accuracy'] <= accuracy)]
        if len(df_p_g) > len(df_p):
            first_ = df_p[:1]
            last_ = df_p[-1:]
            df_p_g = df_p_g.append(last_)
            df_p_g = df_p_g.append(first_)
            df_p = df_p_g
            df_p.sort_values('datetime', inplace=True)
            ct += 1

        # TODO imporve outlier detection
        df_p = remove_outliers(df_p)

        path = [list(i)
                for i in zip(df_p['lon'].to_list(), df_p['lat'].to_list())]
        df.at[i, 'path'] = path
        df.at[i, 'datetime'] = df_p['datetime'].to_list()
        geometry = [Point(xy) for xy in path]
        if len(geometry) > 1:
            line_string_arr.append(LineString(geometry))
        else:
            line_string_arr.append(LineString())

    print('replaced {} triplegs with data from gina'.format(ct))

    geo_df = gpd.GeoDataFrame(df, geometry=line_string_arr)
    return geo_df


df_geo = get_record_data(df_act, rec_path, 200)

# replace geometry for flights with fly_geom
df_geo.loc[df_geo['activity'] == 'FLYING', 'geometry'] = df_geo['fly_geom']

df = df_geo.loc[df_geo['activity'] == 'FLYING']
print(df_geo.head())
print(df)


def f(frame):
    xy = frame.geometry.xy
    longs = xy[0].tolist()
    lats = xy[1].tolist()
    print(longs)
    print(lats)
    print([list(z) for z in zip(longs, lats)])
    return [list(z) for z in zip(longs, lats)]


df['coords'] = df.apply(f, axis=1)
df_geo.loc[df_geo['activity'] == 'FLYING', 'path'] = df['coords']
df_geo.loc[df_geo['activity'] == 'FLYING', 'datetime'] = df_geo.loc[df_geo['activity']
                                                                    == 'FLYING'].apply(lambda x: [x.started_at, x.finished_at], axis=1)


# do mapmatching
def get_match(coordinates, radius, profile, timestamps):
    access_token = keys['mapboxToken']
    url = f"https://api.mapbox.com/matching/v5/mapbox/{profile}/{coordinates}?geometries=geojson&radiuses={radius}&timestamps={timestamps}&annotations=duration&overview=full&access_token={access_token}"
    response = requests.get(url)
    # Handle errors
    if response.json()['code'] != 'Ok':
        print(f"{response.json()['code']} - {response.json()['message']}.\n\nFor more information: https://docs.mapbox.com/api/navigation/map-matching/#map-matching-api-errors")
        return None
    # Get the coordinates from the response
    coords = response.json()['matchings'][0]['geometry']
    return response.json()


def get_timestamps(dur_all, coords, data_obj):
    df = pd.DataFrame({'durations': dur_all, 'coords': coords})

    # real duration
    total_dur = (data_obj['finished_at'] -
                 data_obj['started_at'])/timedelta(seconds=1)
    # get the time diff factor
    time_factor = total_dur/df['durations'].sum()
    # adjust time per leg
    df['dur_adj'] = df['durations']*time_factor
    df['dur_adj'] = df['dur_adj'].cumsum()
    # calc timstamp of each fix
    try:
        df['dt'] = df['dur_adj'].apply(
            lambda x: timedelta(seconds=x)+data_obj['started_at'])
    except:
        df['dur_adj'] = df['dur_adj'].fillna(0)
        df['dt'] = df['dur_adj'].apply(
            lambda x: timedelta(seconds=x)+data_obj['started_at'])

    return df['dt'].to_list()


def update_route(obj, profile):
    length = 1000
    coords = []
    ts = []
    start = 0
    end = 99
    distance = 0
    map_match = False

    while start < len(obj['path']):
        if start > 0:
            print('________________________________________')
        geom_str = ';'.join(str(e[0])+','+str(e[1])
                            for e in obj['path'][start:end])
        timestamp_str = ';'.join(str(time.mktime(e.timetuple()))
                                 for e in obj['datetime'][start:end])

        radius = [50] * len(obj['path'][start:end])
        radius = ';'.join(str(r) for r in radius)
        profile = profile

        match_res = get_match(geom_str, radius, profile, timestamp_str)

        if match_res == None:
            return obj['path'], obj['datetime'], False, obj['distance']
        if match_res != None:
            coords += match_res['matchings'][0]['geometry']['coordinates']
            distance += match_res['matchings'][0]['distance']
            dur_all = [0]
            for leg in match_res['matchings'][0]['legs']:
                dur_all += leg['annotation']['duration']
            ts += dur_all
        start += length
        end += length

    # only if not to much is cut off
    if distance >= obj['distance']*0.6:
        datetimes = get_timestamps(ts, coords, obj)
        map_match = True
        return coords, datetimes, map_match, distance

    else:
        print('orig_dist')
        print(obj['distance'])
        print('routed_dist')
        return obj['path'], obj['datetime'], False, obj['distance']


df_geo['map_match'] = None
for i, obj in df_geo.iterrows():
    if obj['activity'] in ['IN_PASSENGER_VEHICLE', 'IN_BUS', 'IN_TRAIN', 'MOTORCYCLING']:
        coords, datetimes, map_match, distance = update_route(obj, 'driving')
        df_geo.at[i, 'map_match'] = map_match
        df_geo.at[i, 'path'] = coords
        df_geo.at[i, 'distance'] = distance
        geom = [Point(coord) for coord in coords]
        if len(geom) > 1:
            df_geo.at[i, 'geometry'] = LineString(geom)
        else:
            df_geo.at[i, 'geometry'] = LineString()
        df_geo.at[i, 'datetime'] = datetimes

        if map_match:
            print('Geometries updated!')

    elif obj['activity'] in ['WALKING']:

        coords, datetimes, map_match, distance = update_route(obj, 'walking')
        df_geo.at[i, 'map_match'] = map_match
        df_geo.at[i, 'path'] = coords
        df_geo.at[i, 'distance'] = distance

        geom = [Point(coord) for coord in coords]
        if len(geom) > 1:
            df_geo.at[i, 'geometry'] = LineString(geom)
        else:
            df_geo.at[i, 'geometry'] = LineString()
        df_geo.at[i, 'datetime'] = datetimes

        if map_match:
            print('Geometries updated!')

    else:
        # boat, ski,fly etc
        print('other activity: {}'.format(obj['activity']))
        df_geo.at[i, 'map_match'] = False
        continue


# routing
access_token = keys['mapboxToken']


def get_route(start, end):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start[0]},{start[1]};{end[0]},{end[1]}?steps=true&geometries=geojson&access_token={access_token}"
    response = requests.get(url)
    json = response.json()

    try:
        data = json["routes"][0]
        route = data["geometry"]["coordinates"]
        distance = data['distance']
    except:
        print(json)
        return None, None
    return route, distance


geoms = []
df_geo['routed'] = False
for i, obj in df_geo.iterrows():
    if (obj['map_match'] == False) & (obj['distance'] > 4000) & (obj['activity'] not in ['WALKING', 'FLYING', 'BOATING', 'IN_FERRY']):
        x = obj['path']
        if len(x) > 1:
            start = x[0]
            end = x[-1]
            route, distance = get_route(start, end)
            if route != None:
                routed = True
                print('worked')
                geometry = [Point(xy) for xy in route]
                df_geo.at[i, 'geometry'] = LineString(geometry)
                df_geo.at[i, 'routed'] = True
                df_geo.at[i, 'distance_new'] = distance


# load pics
# import photos data
# photos = pd.read_csv('../data/pics.csv')
# photos['dt'] = pd.to_datetime(photos['dt'])

# df_geo['pic_ids'] = None
# df_geo['pic_dates'] = None
# for i, obj in df_geo.iterrows():
#     photos_in = photos.loc[(photos['dt']>=obj['started_at']) & (photos['dt']<=obj['finished_at'])]
#     df_geo.at[i, 'pic_ids'] = photos_in['id'].to_list()
#     df_geo.at[i, 'pic_dates'] = photos_in['dt'].to_list()

# create unix timestamps
df_geo['datetimes_unix'] = None
# df_geo['pics_dt_unix'] = None
for i, obj in df_geo.iterrows():
    df_geo.at[i, 'started'] = time.mktime(obj['started_at'].timetuple())
    df_geo.at[i, 'finished'] = time.mktime(obj['finished_at'].timetuple())
    df_geo.at[i, 'datetimes_unix'] = [time.mktime(
        dt.timetuple()) for dt in obj['datetime']]
    # df_geo.at[i, 'pics_dt_unix'] = [time.mktime(dt.timetuple()) for dt in obj['pic_dates']]

# remove fly geoms
df_geo.drop(columns=['fly_geom'], inplace=True)

# drop empty geoms
df_geo = df_geo.loc[df_geo['geometry'].is_empty == False]

df_geo.to_csv('./data/finished_tpl.csv')


# write jsons
df = pd.read_csv('./data/finished_tpl.csv')
deck_arr = []
flight_arr = []
df.sort_values('started', inplace=True)
df.activity.unique()
df.loc[df['activity'] == 'FLYING']

for i, obj in df.iterrows():
    import ast
    path = ast.literal_eval(obj['path'])
    timestamps = ast.literal_eval(obj['datetimes_unix'])
    new_ts = []
    for t in timestamps:
        new_ts.append(int(t/60))
    if obj['activity'] != 'FLYING':
        deck_arr.append({'vendor': 1, 'path': path,
                        'timestamps': timestamps, 'new_ts': new_ts})
    else:
        flight_arr.append({'vendor': 1, 'path': path,
                          'timestamps': timestamps, 'new_ts': new_ts})


with open("../src/data/tpl.json", "w") as outfile:
    json.dump(deck_arr, outfile)
with open("../src/data/flights.json", "w") as outfile:
    json.dump(flight_arr, outfile)

""" #add to mongo_db


# convert to geojson
df_geo['geometry']=df_geo['geometry'].apply(lambda x:shapely.geometry.mapping(x))

# sp vs tpl
df_geo['kind'] = 'tripleg'
data = df_geo.to_dict('records')
connection_string = keys['mongo_connection_string']

client = pymongo.MongoClient(connection_string)
db = client["ademerci"]
collection = db["posts"]
collection.insert_many(data)
print('inserted') """
