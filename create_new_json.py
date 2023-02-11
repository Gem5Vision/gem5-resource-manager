import json

# create new json file
with open('resources_new.json', 'w') as newf:
    with open('resources.json') as f:
        data = json.load(f)
        newf.write('''{
    "version": "22.1",
    "url_base": "http://dist.gem5.org/dist/v22-1",
    "previous-versions": {
        "develop": "https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/develop/resources.json?format=TEXT",
        "21.2": "http://resources.gem5.org/prev-resources-json/resources-21-2.json",
        "22.0": "http://resources.gem5.org/prev-resources-json/resources-22-0.json"
    },
    "resources": [''')
        resources = data['resources']
        for resource in resources:
            if resource['type'] == 'group':
                for group in resource['contents']:
                    group['group'] = resource['name']
                    newf.write(json.dumps(group))
                    newf.write(',')
            # write to file
            else:
                newf.write(json.dumps(resource))
                newf.write(',')
    newf.write(']}')
