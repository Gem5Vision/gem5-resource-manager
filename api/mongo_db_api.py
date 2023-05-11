from flask import request
from bson import json_util


def findResource(database, json):
    """
    Find a resource in the database

    :param: database: Database object
    :param: json: JSON object with id and resource_version[optional]
    :return: json_resource: JSON object with request resource or error message
    """
    if request.json["resource_version"] == "":
        resource = (
            database.get_collection()
            .find({"id": json["id"]}, {"_id": 0})
            .sort("resource_version", -1)
            .limit(1)
        )
    else:
        resource = (
            database.get_collection()
            .find(
                {"id": json["id"], "resource_version": json["resource_version"]},
                {"_id": 0},
            )
            .sort("resource_version", -1)
            .limit(1)
        )
    # check if resource is empty list
    json_resource = json_util.dumps(resource)
    if json_resource == "[]":
        return {"exists": False}
    # print(json_resource)
    return json_resource


def updateResource(database, json):
    """
    This function updates a resource in the database by first checking if the resource version in the request matches the resource version stored in the database.
    If they match, the resource is updated in the database. If they do not match, the update is rejected.

    :param: database: Database object
    :param: json: JSON object with id, resource object, and resource_version
    :return: json_response: JSON object with status message
    """
    # remove all keys that are not in the request
    database.get_collection().replace_one(
        {"id": json["id"], "resource_version": json["resource"]["resource_version"]},
        json["resource"],
    )
    return {"status": "Updated"}


def getVersions(database, json):
    """
    This function retrieves all versions of a resource with the given ID from the database.
    It takes two arguments, the database object and a JSON object containing the 'id' key of the resource to be retrieved.

    :param: database: Database object
    :param: json: JSON object with id
    :return: json_resource: JSON object with all resource versions
    """
    versions = (
        database.get_collection()
        .find({"id": json["id"]}, {"resource_version": 1, "_id": 0})
        .sort("resource_version", -1)
    )
    json_resource = json_util.dumps(versions)
    return json_resource


def deleteResource(database, json):
    """
    This function deletes a resource from the database by first checking if the resource version in the request matches the resource version stored in the database.
    If they match, the resource is deleted from the database. If they do not match, the delete operation is rejected

    :param: database: Database object
    :param: json: JSON object with id and resource_version
    :return: json_response: JSON object with status message
    """
    database.get_collection().delete_one(
        {"id": json["id"], "resource_version": json["resource_version"]}
    )
    return {"status": "Deleted"}


def insertResource(database, json):
    """
    This function inserts a new resource into the database using the 'insert_one' method of the MongoDB client.
    The function takes two arguments, the database object and the JSON object representing the new resource to be inserted.

    :param: database: Database object
    :param: json: JSON object representing the new resource to be inserted
    :return: json_response: JSON object with status message
    """
    database.get_collection().insert_one(json)
    return {"status": "Inserted"}


def checkResourceExists(database, json):
    """
    This function checks if a resource exists in the database by searching for a resource with a matching 'id' and 'resource_version' in the database.
    The function takes two arguments, the database object and a JSON object containing the 'id' and 'resource_version' keys.

    :param: json: JSON object with id and resource_version
    :return: json_response: JSON object with boolean 'exists' key
    """
    resource = (
        database.get_collection()
        .find(
            {"id": json["id"], "resource_version": json["resource_version"]}, {"_id": 0}
        )
        .sort("resource_version", -1)
        .limit(1)
    )
    json_resource = json_util.dumps(resource)
    if json_resource == "[]":
        return {"exists": False}
    return {"exists": True}
