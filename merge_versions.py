import json
import os
import pandas as pd

ver_map = {
    'dev': "http://dist.gem5.org/dist/develop",
           '22.1': "http://dist.gem5.org/dist/v22-1",
           '22.0': "http://dist.gem5.org/dist/v22-0",
           '21.2': "http://dist.gem5.org/dist/v21-2"
}


def change_type(resource):
    if resource['type'] == 'workload':
        # get the architecture from the name and remove 64 from it
        resource['architecture'] = resource['name'].split(
            '-')[0].replace('64', '').upper()
        return resource
    if 'kernel' in resource['name']:
        resource['type'] = 'kernel'
    elif 'bootloader' in resource['name']:
        resource['type'] = 'bootloader'
    elif 'benchmark' in resource['documentation']:
        resource['type'] = 'benchmark'
    elif resource['url'] is not None and '.img.gz' in resource['url']:
        resource['type'] = 'diskimage'
    elif 'binary' in resource['documentation']:
        resource['type'] = 'binary'
    elif 'checkpoint' in resource['documentation']:
        resource['type'] = 'checkpoint'
    elif 'simpoint' in resource['documentation']:
        resource['type'] = 'simpoint'
    return resource


def json_to_pd(filename, ver, url):
    with open(filename, 'r') as newf:
        data = json.load(newf)
        resources = data['resources']
        new_resources = []
        for resource in resources:
            if resource['type'] == 'group':
                for group in resource['contents']:
                    group['group'] = resource['name']
                    group['versions'] = {ver: url}
                    group = change_type(group)
                    new_resources.append(group)
            else:
                resource = change_type(resource)
                resource['versions'] = {ver: url}
                new_resources.append(resource)
        df = pd.DataFrame(new_resources)
        return df


def merge_df1(dfs):
    fin_df = dfs[0]
    for df in dfs[1:]:
        # merge the 2 dataframes on name
        # keep the left column values if there is a conflict
        fin_df = pd.merge(fin_df, df, on='name', how='inner')
    fin_df['dev'] = fin_df[['dev', '22.1', '22.0', '21.2']].apply(
        lambda x: dict(x.dropna()), axis=1)
    # rename name dev to versions
    fin_df.rename(columns={'dev': 'versions'}, inplace=True)
    # remove dev, 22.1, 22.0, 21.2 columns
    fin_df.drop(['22.1', '22.0', '21.2'], axis=1, inplace=True)
    fin_df = fin_df.where((pd.notnull(fin_df)), None)
    resources = fin_df.to_dict('records')
    with open('test.json', 'w') as f:
        json.dump(resources, f, indent=4)


def merge_df(dfs):
    fin_df = dfs[0]
    # go through all the rows in the first dataframe
    for row in fin_df.itertuples():
        # get the name of the resource
        name = row.name
        # get the versions dictionary
        versions = row.versions
        # go through all the other dataframes
        for df in dfs[1:]:
            # get the row with the same name
            temp = df[df['name'] == name]
            # if the row exists
            if not temp.empty:
                # get the versions dictionary
                temp = temp.iloc[0]
                temp_versions = temp.versions
                # add the versions dictionary to the final versions dictionary
                versions.update(temp_versions)
            else:
                # add the row to the final dataframe
                fin_df = pd.concat([fin_df, temp])

    fin_df = fin_df.where((pd.notnull(fin_df)), None)
    resources = fin_df.to_dict('records')
    with open('test.json', 'w') as f:
        json.dump(resources, f, indent=4)


dfs = []
for k, v in ver_map.items():
    df = json_to_pd('resources_'+k+'.json', k, v)
    df = df.where((pd.notnull(df)), None)
    print(df.shape)
    dfs.append(df)

merge_df(dfs)
