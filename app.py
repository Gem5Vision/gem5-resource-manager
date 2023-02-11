import json
import pandas as pd

with open('resources_test.json') as f:
    data = json.load(f)
    resources = data['resources']
    df = pd.DataFrame(resources)
    # get all categories
    categories = df['type'].unique()
    print(categories)
    # get names of all the groups
    groups = df[df['group'].notnull()]['group'].unique()
    print(groups)
    # get all types of architectures
    archs = df[df['architecture'].notnull()]['architecture'].unique()
    print(archs)

    print(df[df['type'] == 'resource']['name'])
    # print(df[df['architecture'] == 'ARM']['name'])

    # print to json and replace Nan with None
    df = df.where((pd.notnull(df)), None)
    resources = df.to_dict('records')
    data['resources'] = resources
    with open('resources_test1.json', 'w') as newf:
        newf.write(json.dumps(data))
