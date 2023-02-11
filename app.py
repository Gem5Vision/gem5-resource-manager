import json

with open('resources_new.json') as f:
    data = json.load(f)
    resources = data['resources']
    for resource in resources:
        print(resource['type'])
