import json
import pandas as pd

with open('resources_new.json', "r+") as f:
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

    # rename name column to id
    df.rename(columns={'name': 'id'}, inplace=True)

    # rename type column to category
    df.rename(columns={'type': 'category'}, inplace=True)

    # rename url column to download_url
    df.rename(columns={'url': 'download_url'}, inplace=True)

    # rename documentation column to description
    df.rename(columns={'documentation': 'description'}, inplace=True)

    # add new column for name and initialize it with id but replace all - with space
    df['name'] = df['id'].str.replace('-', ' ')

    # add new column for gem5_version and initialize it with 22.1
    df['gem5_version'] = '22.1'

    # add downloads column and initialize it to 0
    df['downloads'] = 0

    # add example_url column and initialize it to None
    df['example_url'] = None

    # add documentation_url column and initialize it to None
    df['documentation_url'] = None

    # add github_url column and initialize it to None
    df['github_url'] = None
    # print to json and replace Nan with None
    df = df.where((pd.notnull(df)), None)
    resources = df.to_dict('records')
    data['resources'] = resources
    # make the json file pretty
    f.seek(0)
    f.truncate()
    f.write(json.dumps(data, indent=4))
