import json
from flask import render_template, Flask, request, redirect, url_for, Response
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema
from database import Database
import requests

import urllib.parse
import markdown

import mongo_db_api
import json_api

schema = {}
with open("schema/test.json", "r") as f:
    schema = json.load(f)



database = Database("mongodb+srv://admin:gem5vision_admin@gem5-vision.wp3weei.mongodb.net/?retryWrites=true&w=majority", "gem5-vision", "versions_test")


resources = None
with open("test_json_endpoint.json", "r") as f:
    resources = json.load(f)

isMongo = True
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login/<string:database_type>")
def login(database_type):
    if database_type == "mongodb":
        return render_template("mongoDBLogin.html")
    elif database_type == "json":
        return render_template("jsonLogin.html")
    else:
        return render_template("404.html")


@app.route("/validateURI", methods=['GET'])
def validateURI():
    uri = request.args.get('uri')
    collection = request.args.get('collection')
    database = request.args.get('database')
    alias = request.args.get('alias')
    if uri == "":
        return {"error" : "empty"}, 400
    return redirect(url_for("editor", isMongo="true", uri=uri, collection=collection, database=database, alias=alias), 302)


@app.route("/validateJSON", methods=["GET", "POST"]) 
def validateJSON():
    if request.method == 'GET':
        url = request.args.get('q')
        if url == "":
            return {"error" : "empty"}, 400
    else:
        if 'file' not in request.files:
            return {"error" : "empty"}, 400
        file = request.files['file']


@app.route("/editor")
def editor():
    global isMongo
    if not request.args:
        return render_template("404.html"), 404
    elif request.args.get('isMongo') == 'true':
        isMongo = True
        mongo_uri = urllib.parse.unquote(request.args.get('uri'))
        alias = request.args.get('alias')
        global database
        database.change_database(mongo_uri, request.args.get('database'), request.args.get('collection'))
        return render_template("editor.html", editor_type="MongoDB", tagline=(mongo_uri if alias == "" else alias))
    elif request.args.get('isMongo') == 'false':
        isMongo = False
        return render_template("editor.html", editor_type="JSON")
    else:
        return render_template("404.html"), 404

@app.route("/help")
def help():
    with open('static/help.md', 'r') as f:
        return render_template("help.html", rendered_html=markdown.markdown(f.read()))


@app.route("/toggleIsMongo", methods=["POST"])
def toggleIsMongo():
    # input is a json object with a single key "isMongo"
    # {"isMongo": true/false}
    isMongo = request.json["isMongo"]
    return {"isMongo": isMongo}

@app.route("/find", methods=["POST"])
def find():
    print("resource before find:\n", resources)
    if isMongo:
        return mongo_db_api.findResource(database, request.json)
    return json_api.findResource(resources, request.json)


@app.route("/update", methods=["POST"])
def update():
    if isMongo:
        return mongo_db_api.updateResource(database, request.json)
    return json_api.updateResource(resources, request.json)


@app.route("/versions", methods=["POST"])
def getVersions():
    if isMongo:
        return mongo_db_api.getVersions(database, request.json)
    return json_api.getVersions(resources, request.json)


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
    if isMongo:
        return mongo_db_api.deleteResource(database, request.json)
    return json_api.deleteResource(resources, request.json)


@app.route("/insert", methods=["POST"])
def insert():
    print("resource before insert:\n", resources)
    if isMongo:
        return mongo_db_api.insertResource(database, request.json)
    return json_api.insertResource(resources, request.json)



@app.errorhandler(404)
def handle404(error):
    return render_template('404.html'), 404

@app.route("/checkExists", methods=["POST"])
def checkExists():
    if isMongo:
        return mongo_db_api.checkResourceExists(database, request.json)
    return json_api.checkResourceExists(resources, request.json)


if __name__ == "__main__":
    app.run(debug=True)
