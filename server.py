import json
from flask import render_template, Flask, request, redirect, url_for, Response
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema
from database import Database


schema = {}
with open("schema/test.json", "r") as f:
    schema = json.load(f)


# database = Database("gem5-vision", "versions_test")
# collection = database.get_collection()
database = ""

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login/<string:database_type>")
def login(database_type):
    if database_type == "mongodb":
        return render_template("mongoDBLogin.html")
    else:
        return render_template("404.html")
    

@app.route("/validateURI", methods=['GET'])
def validateURI():
    uri = request.args.get('uri')
    if uri == "":
        return {"error" : "empty"}, 400
    #TODO: URI Validation
    return redirect(url_for("editor", uri=uri), 302)


@app.route("/editor")
def editor():
    mongo_uri = request.args.get('uri')
    global database
    database = Database(mongo_uri, "gem5-vision", "versions_test")
    return render_template("editor.html", database="MongoDB", uri=mongo_uri)


@app.route("/find", methods=["POST"])
def find():
    if request.json["resource_version"] == "":
        resource = database.get_collection().find({"id": request.json["id"]}, {"_id": 0}).sort(
            "resource_version", -1).limit(1)
    else:
        resource = database.get_collection().find({"id": request.json["id"], "resource_version": request.json["resource_version"]}, {"_id": 0}).sort(
            "resource_version", -1).limit(1)
    # check if resource is empty list
    json_resource = json_util.dumps(resource)
    if json_resource == "[]":
        return {"exists": False}
    return json_resource


@app.route("/update", methods=["POST"])
def update():
    # remove all keys that are not in the request
    database.get_collection().replace_one(
        {"id": request.json["id"], "resource_version": request.json["resource"]["resource_version"]}, request.json["resource"])
    return {"status": "Updated"}


@app.route("/versions", methods=["POST"])
def getVersions():
    versions = database.get_collection().find({"id": request.json["id"]}, {
        "resource_version": 1, "_id": 0}).sort("resource_version", -1)
    json_resource = json_util.dumps(versions)
    return json_resource


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
    database.get_collection().delete_one(
        {"id": request.json["id"], "resource_version": request.json["resource_version"]})
    return {"status": "Deleted"}


@app.route("/insert", methods=["POST"])
def insert():
    database.get_collection().insert_one(request.json)
    return {"status": "Inserted"}


@app.errorhandler(404)
def handle404(error):
    return render_template('404.html'), 404
@app.route("/checkExists", methods=["POST"])
def checkExists():
    resource = database.get_collection().find_one(
        {"id": request.json["id"], "resource_version": request.json["resource_version"]})
    if resource == None:
        return {"exists": False}
    else:
        return {"exists": True}


if __name__ == "__main__":
    app.run(debug=True)
