from bson import json_util

def findResource(resources, query):
    for resource in resources:
        if query["resource_version"] == "":
            if resource["id"] == query["id"]:
                print("Found resource")
                return json_util.dumps([resource])
        else:
            if resource["id"] == query["id"] and resource["resource_version"] == query["resource_version"]:
                print("Found resource")
                return json_util.dumps([resource])
    return {"exists": False}