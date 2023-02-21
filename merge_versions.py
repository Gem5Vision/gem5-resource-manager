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


def get_common_ind(fin_df, df):
    rows = len(fin_df)
    com_ind_df = []
    com_ind_df2 = []
    ind_map = {}

    for i in range(0, rows):
        com_ind_df = com_ind_df + \
            df.index[df['name'] == fin_df.iloc[i]['name']].tolist()
    # print(com_ind_df)
    for i in com_ind_df:
        com_ind_df2 = com_ind_df2 + \
            fin_df.index[fin_df['name'] == df.iloc[i]['name']].tolist()
    # print(com_ind_df)

    for i in range(0, len(com_ind_df)):
        ind_map[com_ind_df[i]] = com_ind_df2[i]
    return ind_map


def merge_df(dfs):
    fin_df = dfs[1]
    for df in dfs[3:4]:
        ind_map = get_common_ind(fin_df, df)
        # print(ind_map)
        for i in range(0, len(df)):
            if i in ind_map:
                for k, v in df.iloc[i].versions.items():
                    fin_df.iloc[ind_map[i]]['versions'][k] = v
                print(fin_df.iloc[ind_map[i]])
            else:
                fin_df =
                print(fin_df.iloc[len(fin_df)-1])
    with open('test.json', 'w') as f:
        f.write(json.dumps(fin_df.to_dict(), indent=4))


dfs = []
for k, v in ver_map.items():
    df = json_to_pd('resources_'+k+'.json', k, v)
    df = df.where((pd.notnull(df)), None)
    print(df.shape)
    dfs.append(df)

merge_df(dfs)
