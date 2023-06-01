import pandas as pd
import json
from datetime import timedelta
from shapely.geometry import Point
import requests
import time
import shapely
import pymongo
import geopandas as gpd
from os import listdir
from os.path import isfile, join
import json
from geopy.geocoders import OpenCage


with open('../src/private.json') as f:
    # Load the JSON data
    keys = json.load(f)


# set start and end date
# TODO set start according to already processed data
start = pd.to_datetime('2023-01-31 13:00:00.000000+00:00')
end = pd.to_datetime('2023-09-1 23:59:00.000000+00:00')

# get the semantic staypoint info from goole raw data


def get_semantic_info(path):
    pl_arr = []
    # read file path
    with open(path, 'r', encoding="utf8") as j:
        contents = json.loads(j.read())

    # sort activities and places
    places = []
    for obj in contents['timelineObjects']:
        if 'placeVisit' in obj.keys():
            places.append(obj['placeVisit'])

    for obj in places:
        try:
            lat = obj['centerLatE7']/10**7
            lon = obj['centerLngE7']/10**7
        except:
            try:
                lat = obj['location']['latitudeE7']/10**7
                lon = obj['location']['longitudeE7']/10**7
            except:
                lat = None
                lon = None
        try:
            name = obj['location']['name']
        except:
            name = ''
        try:

            place_id = obj['location']['placeId']
        except:
            place_id = None

        started_at = pd.to_datetime(obj['duration']['startTimestamp'])
        finished_at = pd.to_datetime(obj['duration']['endTimestamp'])
        if started_at > finished_at:
            print('error')
        # conf = obj['placeConfidence']
        conf = obj['location']['locationConfidence']
        try:
            address = obj['location']['address']
        except:
            print('address not found')
            address = None

        pl_arr.append([lat, lon, name, started_at,
                      finished_at, conf, address, place_id])

    df_pl = pd.DataFrame(data=pl_arr, columns=[
                         'lat', 'lon', 'name', 'started_at', 'finished_at', 'conf', 'address', 'place_id'])
    df_pl.dropna(subset=['lat', 'lon'], inplace=True)
    df_pl['duration_h'] = (df_pl['finished_at'] -
                           df_pl['started_at'])/timedelta(hours=1)

    return df_pl


# get all files in folder
mypath = "./raw_data/Semantic Location History/2023"
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

# loop through files in 2023 and merge
df_pl = pd.DataFrame()
for file in onlyfiles:
    df_pl = df_pl.append(get_semantic_info("{}/{}".format(mypath, file)))


# filter dfs by start- and enddate
df_pl = df_pl.loc[(df_pl['started_at'] >= start) &
                  (df_pl['finished_at'] <= end)]


# google returs town in local language
# get the town/city given latitude and longitude
geolocator = OpenCage(api_key=keys['openCageKey'])


def get_town_name(latitude, longitude):
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    if location:
        town = location.raw['components'].get('town', '')
        city = location.raw['components'].get('city', '')
        return town or city
    return None


df_pl['type'] = None
df_pl.reset_index(inplace=True)
all_types = []
for i, obj in df_pl.iterrows():
    if obj['place_id'] is not None:
        api_key = keys['google_api_key']
        fields = 'name%2Cformatted_address%2Curl%2Ctype%2Cicon_mask_base_uri'
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={obj['place_id']}&fields={fields}&key={api_key}"
        response = requests.get(url)
        # Handle errors
        if response.json()['status'] != 'OK':
            print('not found')
        else:
            result = response.json()['result']
            df_pl.at[i, 'address'] = result['formatted_address']
            df_pl.at[i, 'type'] = result['types']

            town = get_town_name(obj.lat, obj.lon)
            df_pl.at[i, 'town'] = town

            # test
            # df_pl.at[i, 'city'] = result['long_name']
            # df_pl.at[i, 'city_sh'] = result['short_name']

            if 'url' in result.keys():
                df_pl.at[i, 'url'] = result['url']
            else:
                df_pl.at[i, 'url'] = None
            if 'icon_mask_base_uri' in result.keys():
                df_pl.at[i, 'icon'] = result['icon_mask_base_uri']+'.svg'
            else:
                df_pl.at[i, 'icon'] = None
            all_types += result['types']
            if 'lodging' in result['types'] and obj['duration_h'] > 5:
                df_pl.at[i, 'sleep'] = True
            else:
                df_pl.at[i, 'sleep'] = False

# load pics
# import photos data
# photos = pd.read_csv('../data/pics.csv')
# photos['dt'] = pd.to_datetime(photos['dt'])

# df_pl['pic_ids'] = None
# df_pl['pic_dates'] = None
# for i, obj in df_pl.iterrows():
#     photos_in = photos.loc[(photos['dt']>=obj['started_at']) & (photos['dt']<=obj['finished_at'])]
#     df_pl.at[i, 'pic_ids'] = photos_in['id'].to_list()
#     df_pl.at[i, 'pic_dates'] = photos_in['dt'].to_list()

# create unix timestamps
df_pl['datetimes_unix'] = None
# df_pl['pics_dt_unix'] = None
for i, obj in df_pl.iterrows():
    df_pl.at[i, 'started'] = time.mktime(obj['started_at'].timetuple())
    df_pl.at[i, 'finished'] = time.mktime(obj['finished_at'].timetuple())
    # df_pl.at[i, 'pics_dt_unix'] = [time.mktime(dt.timetuple()) for dt in obj['pic_dates']]

df_pl['started'] = df_pl['started_at'].apply(
    lambda x: time.mktime(x.timetuple()))
df_pl['finished'] = df_pl['finished_at'].apply(
    lambda x: time.mktime(x.timetuple()))


geoms = [Point(obj['lon'], obj['lat']) for i, obj in df_pl.iterrows()]
gdf_pl = gpd.GeoDataFrame(df_pl, geometry=geoms)

# add icon name
icon_mapping = {
    'hotel_pinlet.svg': 'bed-solid.svg',
    'airport_pinlet.svg': 'plane-arrival-solid.svg',
    'generic_pinlet.svg': 'map-pin-solid.svg',
    'shopping_pinlet.svg': 'bag-shopping-solid.svg',
    'restaurant_pinlet.svg': 'utensils-solid.svg',
    'train_rail_1_pinlet.svg': 'train-solid.svg',
    'movie_pinlet.svg': 'clapperboard-solid.svg',
    'cafe_pinlet.svg': 'mug-saucer-solid.svg',
    'museum_pinlet.svg': 'building-columns-solid.svg',
    'bus_share_taxi_pinlet.svg': 'bus-solid.svg',
    'worship_hindu_pinlet.svg': 'place-of-worship-solid.svg',
    'school_pinlet.svg': 'school-solid.svg',
    'shoppingcart_pinlet.svg': 'bag-shopping-solid.svg',
    'bank-intl_pinlet.svg': 'piggy-bank-solid.svg',
    'parking_pinlet.svg': 'square-parking-solid.svg',
    'atm_pinlet.svg': 'piggy-bank-solid.svg',
    'bar_pinlet.svg': 'champagne-glasses-solid.svg',
    'civic-bldg_pinlet.svg': 'building-columns-solid.svg',
    'monument_pinlet.svg': 'building-columns-solid.svg',
    'gas_pinlet.svg': 'gas-pump-solid.svg',
    'tree_pinlet.svg': 'tree-solid.svg',
    'convenience_pinlet.svg': 'bag-shopping-solid.svg',
    'hospital-H_pinlet.svg': 'hospital-solid.svg'
}

gdf_pl['icon'] = gdf_pl['icon'].fillna('generic_pinlet.svg')
gdf_pl['icon2'] = gdf_pl['icon'].apply(
    lambda x: icon_mapping[x.split('/')[-1]])

# save as csv for debugging
gdf_pl.to_csv('./data/finished_sp.csv')

# create a json
json_arr = []
for i, obj in gdf_pl.iterrows():
    coords = [obj['lon'], obj['lat']]
    started = int(obj['started'])
    finished = int(obj['finished'])
    name = obj['name']
    finished = obj['finished']
    icon = obj['icon2']

    json_arr.append({'coords': coords, 'started': started,
                    'finished': finished, 'icon': icon})

# save json into src
with open("../src/data/sp.json", "w") as outfile:
    json.dump(json_arr, outfile)


""" # add to mongo_db

gdf_pl['geometry']=gdf_pl['geometry'].apply(lambda x:shapely.geometry.mapping(x))
gdf_pl['kind'] = 'staypoint'

data = gdf_pl.to_dict('records')

# Connect to the MongoDB instance using a connection string
connection_string = keys['mongo_connection_string']

client = pymongo.MongoClient(connection_string)
db = client["ademerci"]
collection = db["posts"]
collection.insert_many(data)
print('inserted') """
