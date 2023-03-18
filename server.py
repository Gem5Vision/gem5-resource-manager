import json
from flask import render_template, Flask, request
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema

load_dotenv()
# read MONGO_URI from environment variable

MONGO_URI = os.getenv("MONGO_URI")


def get_database():
    CONNECTION_STRING = MONGO_URI
    client = MongoClient(CONNECTION_STRING)
    return client["gem5-vision"]["resources_test"]


collection = get_database()


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/find", methods=["POST"])
def find():
    resource = collection.find_one({"id": request.json["id"]})
    return json_util.dumps(resource)


@app.route("/update", methods=["POST"])
def update():
    # remove all keys that are not in the request
    collection.replace_one({"id": request.json["id"]}, request.json)
    return {"status": "Updated"}


@app.route("/categories", methods=["GET"])
def getCategories():
    with open("schema/resource.json", "r") as f:
        schema = json.load(f)
    return json.dumps(schema["properties"]["category"]["enum"])


@app.route("/schema", methods=["GET"])
def getSchema():
    with open("schema/resource.json", "r") as f:
        schema = json.load(f)
    return json_util.dumps(schema)


@app.route("/keys", methods=["POST"])
def getFields():
    # use the /schema/resource.json file to get the keys and types for the category
    with open("schema/resource.json", "r") as f:
        schema = json.load(f)
    empty_object = {
        "category": request.json["category"],
    }
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(empty_object))
    for error in errors:
        required = error.message.split("'")[1]
        empty_object[required] = error.schema["properties"][required]["default"]
    return json.dumps(empty_object)


@app.route("/delete", methods=["POST"])
def delete():
    collection.delete_one({"id": request.json["id"]})
    return {"status": "Deleted"}


@app.route("/insert", methods=["POST"])
def insert():
    collection.insert_one(request.json)
    return {"status": "Inserted"}


if __name__ == "__main__":
    app.run(debug=True)
