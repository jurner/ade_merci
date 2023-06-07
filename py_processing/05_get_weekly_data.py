import pandas as pd
import json


# read and sort data
tpl = pd.read_csv('./data/finished_tpl.csv')
sp = pd.read_csv('./data/finished_sp.csv')

tpl.sort_values('started', inplace=True)
sp.sort_values('started', inplace=True)

sp['started_at'] = pd.to_datetime(sp['started_at'])
sp['finishe_at'] = pd.to_datetime(sp['finished_at'])

tpl['started_at'] = pd.to_datetime(tpl['started_at'])
tpl['finishe_at'] = pd.to_datetime(tpl['finished_at'])

# merge sp and tpl
tpl.rename(columns={'activity': 'type'}, inplace=True)
tpl['name'] = ''
all_dta = sp[['started_at', 'finished_at', 'started', 'finished', 'name', 'type']].append(
    tpl[['started_at', 'finished_at', 'started', 'finished', 'name', 'type']])
all_dta['week'] = all_dta['started_at'].dt.isocalendar().week - 4
all_dta.sort_values('started_at', inplace=True)
all_dta.reset_index(inplace=True)

# add distances and sum of dist per tpl
tpl.loc[tpl['distance_new'].isna() == False, 'distance'] = tpl.distance_new
tpl.loc[tpl.type.isin(['IN_TAXI']), 'type'] = 'IN_PASSENGER_VEHICLE'
tpl.loc[tpl.type.isin(['IN_SUBWAY']), 'type'] = 'IN_TRAIN'
tpl_new = tpl[['started_at', 'finished_at', 'type', 'distance']]
types = tpl_new.type.unique()
unstacked_tpl = tpl_new.set_index(['started_at', 'finished_at', 'type'])[
    'distance'].unstack().reset_index()
unstacked_tpl.fillna(0, inplace=True)
for t in types:
    unstacked_tpl[t+'_sum'] = unstacked_tpl[t].cumsum()


# group by week and create dict
group_dta = all_dta.groupby('week', as_index=False).agg(
    {'started': 'min', 'finished': 'max', 'started_at': 'min', 'finished_at': 'max'})
wk_dict = {}
for i, obj in group_dta.iterrows():
    wk_data = all_dta.loc[all_dta['week'] == obj.week]
    wk_data = wk_data.merge(unstacked_tpl, on=['started_at', 'finished_at'])
    data = wk_data.to_json(orient='records')
    infos = {'started': obj.started, 'finished': obj.finished, 'data': data}
    wk_dict[obj.week] = infos

with open("../src/data/weekly_data.json", "w") as outfile:
    json.dump(wk_dict, outfile)
