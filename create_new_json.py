import json


def change_type(resource):
    if resource['type'] == 'workload':
        return resource
    if 'kernel' in resource['name']:
        resource['type'] = 'kernel'
    elif 'bootloader' in resource['name']:
        resource['type'] = 'bootloader'
    elif 'benchmark' in resource['documentation']:
        resource['type'] = 'benchmark'
    elif resource['url'] is not None and '.img.gz' in resource['url']:
        resource['type'] = 'disk image'
    elif 'binary' in resource['documentation']:
        resource['type'] = 'binary'
    return resource


# create new json file
with open('resources_test.json', 'w') as newf:
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
                    group = change_type(group)
                    newf.write(json.dumps(group))
                    newf.write(',')
            # write to file
            else:
                resource = change_type(resource)
                newf.write(json.dumps(resource))
                newf.write(',')
    newf.write(']}')
