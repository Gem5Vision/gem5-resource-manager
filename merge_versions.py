import json
import os
import pandas as pd

ver_map = {'21.2': "http://dist.gem5.org/dist/v21-2",
           '22.1': "http://dist.gem5.org/dist/v22-1",
           '22.0': "http://dist.gem5.org/dist/v22-0",
           'dev': "http://dist.gem5.org/dist/develop"}


def json_to_pd(filename, ver, url):
    ver_dict = {ver: url}
    with open(filename, 'r') as newf:
        data = json.load(newf)
        resources = data['resources']
        for resource in resources:
            resource['versions'] = ver_dict
        df = pd.DataFrame(resources)
        return df


def merge_df(dfs):
    fin_df = dfs[0]
    for df in dfs[1:]:
        print(df.iloc[0])


dfs = []
for k, v in ver_map.items():
    df = json_to_pd('resources_'+k+'.json', k, v)
    dfs.append(df)
merge_df(dfs)
