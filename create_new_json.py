import json
import requests
import base64
import pandas as pd

# fetch file from google source at https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/resources.json
# and save it as resources.json
""" data = requests.get(
    'https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/develop/resources.json?format=TEXT').text
data = base64.b64decode(data).decode('utf-8') """
# read from test.json
data = open('test.json', 'r').read()

with open('resources.json', 'w') as newf:
    data = json.loads(data)
    df = pd.DataFrame(data)
    # get all categories
    categories = df['type'].unique()
    print(categories)
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
    # add author column and initialize it to empty list
    df['author'] = None
    # add downloads column and initialize it to 0
    # df['downloads'] = 0

    # add example_url column and initialize it to None
    # df['example_url'] = None

    # add documentation_url column and initialize it to None
    # df['documentation_url'] = None

    # add github_url column and initialize it to None
    df['github_url'] = None
    # print to json and replace Nan with None
    # remove columns contents
    df = df.where((pd.notnull(df)), None)
    resources = df.to_dict('records')
    # data['resources'] = resources
    newf.write(json.dumps(resources, indent=4))


with open('resources.json', 'r+') as f:
    data = json.load(f)
    for resource in data:
        if resource['source'] is not None:
            try:
                # print(resource['source'])
                resource['github_url'] = 'https://github.com/gem5/gem5-resources/tree/develop/' + \
                    str(resource['source'])
                request = requests.get(
                    'https://raw.githubusercontent.com/gem5/gem5-resources/develop/'+str(resource['source'])+'/README.md')
                content = request.text
                # get contnt between --- and ---
                content = content.split('---')[1]
                content = content.split('---')[0]
                if('tags:' in content):
                    # print('tags')
                    tags = content.split('tags:\n')[1]
                    tags = tags.split(':')[0]
                    # remove last line
                    tags = tags.split('\n')[:-1]
                    tags = [tag.strip().replace('- ', '') for tag in tags]
                    # print(tags)
                    if tags == ['']:
                        tags = None
                    if resource['tags'] is None:
                        resource['tags'] = tags
                    else:
                        resource['tags'].extend(tags)
                # get author
                author = content.split('author:')[1]
                author = author.split('\n')[0]
                # covert ["Name1", "Name2"] to a list of strings
                author = author.replace(
                    '[', '').replace(']', '').replace('"', '')
                author = author.split(',')
                author = [a.strip() for a in author]
                resource['author'] = author
                print(content)
                license = content.split('license:')[1]
                print("license:", license)
                resource['license'] = license
            except:
                pass
    f.seek(0)
    f.write(json.dumps(data, indent=4))
