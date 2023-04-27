from bson import json_util

def findResource(resources, query):
    # print(resources)
    print("query:\n",query)
    for resource in resources:
        if query["resource_version"] == "" or query["resource_version"] == "Latest":
            if resource["id"] == query["id"]:
                print("Found resource")
                print(resource)

                return json_util.dumps([resource])
        else:
            
            if resource["id"] == query["id"] and resource["resource_version"] == query["resource_version"]:
                print("found resource with version")
                print(resource)
                return json_util.dumps([resource])
    
    return {"exists": False}

def getVersions(resources, query):
    versions = []
    for resource in resources:
        if resource["id"] == query["id"]:
            versions.append({"resource_version": resource["resource_version"]})
            print("Found version")
    return json_util.dumps(versions)

def updateResource(resources, query):
    print("before update:\n",resources)

    for resource in resources:
        if resource["id"] == query["id"] and resource["resource_version"] == query["resource"]["resource_version"]:
            resources.remove(resource)
            resources.append(query["resource"])
            
    print("after update:\n",resources)

    return {"status": "Updated"}

def checkResourceExists(resources, query):
    for resource in resources:
        if resource["id"] == query["id"] and resource["resource_version"] == query["resource_version"]:
            return {"exists": True}
    return {"exists": False}

def insertResource(resources, query):
    print("before insert:\n",resources)
    resources.append(query)
    print("after insert:\n",resources)
    return {"status": "Inserted"}

def deleteResource(resources, query):
    for resource in resources:
        if resource["id"] == query["id"] and resource["resource_version"] == query["resource_version"]:
            resources.remove(resource)
    return {"status": "Deleted"}

