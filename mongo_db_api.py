import json
from flask import render_template, Flask, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema
from database import Database

def findResource(database, json):
    if request.json["resource_version"] == "":
        resource = database.get_collection().find({"id": json["id"]}, {"_id": 0}).sort(
            "resource_version", -1).limit(1)
    else:
        resource = database.get_collection().find({"id": json["id"], "resource_version": json["resource_version"]}, {"_id": 0}).sort(
            "resource_version", -1).limit(1)
    # check if resource is empty list
    json_resource = json_util.dumps(resource)
    if json_resource == "[]":
        return {"exists": False}
    print(json_resource)
    return json_resource

def updateResource(database, json):
    # remove all keys that are not in the request
    database.get_collection().replace_one(
        {"id": json["id"], "resource_version": json["resource"]["resource_version"]}, json["resource"])
    return {"status": "Updated"}

def getVersions(database, json):
    versions = database.get_collection().find({"id": json["id"]}, {
        "resource_version": 1, "_id": 0}).sort("resource_version", -1)
    json_resource = json_util.dumps(versions)
    return json_resource

def deleteResource(database, json):
    database.get_collection().delete_one(
        {"id": json["id"], "resource_version": json["resource_version"]})
    return {"status": "Deleted"}

def insertResource(database, json):
    database.get_collection().insert_one(json)
    return {"status": "Inserted"}

def checkResourceExists(database, json):
    resource = database.get_collection().find({"id": json["id"]}, {"_id": 0}).sort(
        "resource_version", -1).limit(1)
    json_resource = json_util.dumps(resource)
    if json_resource == "[]":
        return {"exists": False}
    return {"exists": True}