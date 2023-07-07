import pandas as pd
from datetime import timedelta
import re
import json
import ast


# load staypoints
sp = pd.read_csv('./data/finished_sp.csv')
sp.sort_values('started', inplace=True)
sp['started_at'] = pd.to_datetime(sp['started_at'])
sp['finished_at'] = pd.to_datetime(sp['finished_at'])


# groupy city and to find relevant place names
sp['duration'] = (sp['finished_at']-sp['started_at']) / timedelta(hours=1)
pl = sp.groupby('town', as_index=False).agg(
    {'started_at': 'min', 'finished_at': 'max', 'duration': 'sum', 'lat': 'mean', 'lon': 'mean'})
pl['duration_1'] = (pl['finished_at']-pl['started_at']) / timedelta(hours=1)
pl[['town', 'duration', 'duration_1']]
# pl = pl.loc[pl['duration_1'] > 1]
pl['unix_sta'] = pd.DatetimeIndex(pl['started_at']).astype(int) // 10**9
pl['unix_fin'] = pd.DatetimeIndex(pl['finished_at']).astype(int) // 10**9

pl['size'] = 1.1
pl.loc[pl.duration > 0.5, 'size'] = 1.6
pl.loc[pl.duration > 2.5, 'size'] = 2
pl.loc[pl.duration > 19, 'size'] = 3

deck_arr = []
for i, obj in pl.iterrows():
    coords = [obj['lon'], obj['lat']]
    started = int(obj['unix_sta'])
    finished = int(obj['unix_fin'])
    size = obj['size']

    name = obj['town'].replace('Amphoe ', '')

    # Replace all Vietnamese accented characters with their unaccented equivalents
    name = re.sub('[àáạảãâầấậẩẫăằắặẳẵ]', 'a', name)
    name = re.sub('[èéẹẻẽêềếệểễ]', 'e', name)
    name = re.sub('[ìíịỉĩ]', 'i', name)
    name = re.sub('[òóọỏõôồốộổỗơờớợởỡ]', 'o', name)
    name = re.sub('[ùúụủũưừứựửữ]', 'u', name)
    name = re.sub('[ỳýỵỷỹ]', 'y', name)
    name = re.sub('đ', 'd', name)

    # Replace individual Vietnamese combining accents with an empty string
    name = re.sub('[\u0300\u0301\u0303\u0309\u0323]',
                  '', name)  # Huyền sắc hỏi ngã nặng
    name = re.sub('[\u02C6\u0306\u031B]', '', name)

    deck_arr.append({'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/v2/cemetery_pinlet.svg',
                    'name': name, 'coords': coords, 'size': size, 'started': started, 'finished': finished})

with open("../src/data/place_names.json", "w") as outfile:
    json.dump(deck_arr, outfile)


# find touristic places in sp to create labels
sp.type = sp.type.fillna('[]')
sp['touri'] = sp.type.apply(
    lambda x: True if 'tourist_attraction' in ast.literal_eval(x) else False)

touri = sp.loc[sp['touri']]
touri = touri.groupby('name', as_index=False).agg(
    {'lat': 'mean', 'lon': 'mean', 'started_at': 'min', 'finished_at': 'max', 'duration': 'sum'})
touri['unix_sta'] = pd.DatetimeIndex(touri['started_at']).astype(int) // 10**9
touri['unix_fin'] = pd.DatetimeIndex(touri['finished_at']).astype(int) // 10**9

touri['size'] = 1.4
touri.loc[touri.duration > 0.44, 'size'] = 1.6
touri.loc[touri.duration > 0.86, 'size'] = 1.8
touri.loc[touri.duration > 1.16, 'size'] = 2

deck_arr = []
for i, obj in touri.iterrows():
    coords = [obj['lon'], obj['lat']]
    started = int(obj['unix_sta'])
    finished = int(obj['unix_fin'])
    size = obj['size']

    name = obj['name']
    # Replace all Vietnamese accented characters with their unaccented equivalents
    name = re.sub('[àáạảãâầấậẩẫăằắặẳẵ]', 'a', name)
    name = re.sub('[èéẹẻẽêềếệểễ]', 'e', name)
    name = re.sub('[ìíịỉĩ]', 'i', name)
    name = re.sub('[òóọỏõôồốộổỗơờớợởỡ]', 'o', name)
    name = re.sub('[ùúụủũưừứựửữ]', 'u', name)
    name = re.sub('[ỳýỵỷỹ]', 'y', name)
    name = re.sub('đ', 'd', name)

    # Replace individual Vietnamese combining accents with an empty string
    name = re.sub('[\u0300\u0301\u0303\u0309\u0323]',
                  '', name)  # Huyền sắc hỏi ngã nặng
    name = re.sub('[\u02C6\u0306\u031B]', '', name)

    deck_arr.append({'name': name, 'coords': coords,
                    'started': started, 'finished': finished, 'size': size})

with open("../src/data/attractions.json", "w") as outfile:
    json.dump(deck_arr, outfile)
