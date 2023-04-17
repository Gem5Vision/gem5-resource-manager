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

schema = {}
with open("schema/test.json", "r") as f:
    schema = json.load(f)


def get_database():
    CONNECTION_STRING = MONGO_URI
    client = MongoClient(CONNECTION_STRING)
    return client["gem5-vision"]["resources_test"]


collection = get_database()


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("editor.html")


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
    return json.dumps(schema["properties"]["category"]["enum"])


@app.route("/schema", methods=["GET"])
def getSchema():
    return json_util.dumps(schema)


@app.route("/keys", methods=["POST"])
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
