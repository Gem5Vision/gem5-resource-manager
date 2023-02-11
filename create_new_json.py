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
    elif 'checkpoint' in resource['documentation']:
        resource['type'] = 'checkpoint'
    elif 'simpoint' in resource['documentation']:
        resource['type'] = 'simpoint'
    return resource


# create new json file
with open('resources_new.json', 'w') as newf:
    with open('resources.json') as f:
        data = json.load(f)
        new_resources = []
        resources = data['resources']
        for resource in resources:
            if resource['type'] == 'group':
                for group in resource['contents']:
                    group['group'] = resource['name']
                    group = change_type(group)
                    new_resources.append(group)
            else:
                resource = change_type(resource)
                new_resources.append(resource)
        data['resources'] = new_resources
        newf.write(json.dumps(data))
