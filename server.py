import json
from flask import render_template, Flask, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema
from database import Database
import mongo_db_api

schema = {}
with open("schema/test.json", "r") as f:
    schema = json.load(f)


database = Database("gem5-vision", "versions_test")
# collection = database.get_collection()


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/find", methods=["POST"])
def find():
    return mongo_db_api.findResource(database, request.json)


@app.route("/update", methods=["POST"])
def update():
    return mongo_db_api.updateResource(database, request.json)


@app.route("/versions", methods=["POST"])
def getVersions():
    return mongo_db_api.getVersions(database, request.json)


@ app.route("/categories", methods=["GET"])
def getCategories():
    return json.dumps(schema["properties"]["category"]["enum"])


@ app.route("/schema", methods=["GET"])
def getSchema():
    return json_util.dumps(schema)


@ app.route("/keys", methods=["POST"])
def getFields():
    empty_object = {
        "category": request.json["category"],
        "id": request.json["id"]
    }
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(empty_object))
    for error in errors:
        if "is a required property" in error.message:
            required = error.message.split("'")[1]
            empty_object[required] = error.schema["properties"][required]["default"]
        if "is not valid under any of the given schemas" in error.message:
            validator = validator.evolve(
                schema=error.schema["definitions"][request.json["category"]])
            for e in validator.iter_errors(empty_object):
                if "is a required property" in e.message:
                    required = e.message.split("'")[1]
                    if "default" in e.schema["properties"][required]:
                        empty_object[required] = e.schema["properties"][required]["default"]
                    else:
                        empty_object[required] = ""
    return json.dumps(empty_object)


@ app.route("/delete", methods=["POST"])
def delete():
    return mongo_db_api.deleteResource(database, request.json)


@app.route("/insert", methods=["POST"])
def insert():
    return mongo_db_api.insertResource(database, request.json)



@app.route("/checkExists", methods=["POST"])
def checkExists():
    return mongo_db_api.checkResourceExists(database, request.json)


if __name__ == "__main__":
    app.run(debug=True)
