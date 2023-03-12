from flask import render_template, Flask, request, redirect, url_for, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import Code, json_util

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
    # remove _id from request.json
    collection.update_one({"id": request.json["id"]}, {"$set": request.json})
    return {"status": "Updated"}


@app.route("/keys", methods=["GET"])
def getFields():
    # get all keys and types in the form of "key": "type"
    keys = collection.aggregate(
        [
            {
                "$project": {
                    "keys": {"$objectToArray": "$$ROOT"},
                }
            },
            {"$unwind": "$keys"},
            {"$project": {"keys": {"k": "$keys.k", "v": {"$type": "$keys.v"}}}},
            {
                "$group": {
                    "_id": None,
                    "keys": {
                        "$addToSet": "$keys",
                    },
                }
            },
        ]
    )
    keys = list(keys)[0]["keys"]
    print(keys)
    columns = {}
    for key in keys:
        if key["v"] == "array":
            columns[key["k"]] = []
        elif key["v"] == "string":
            columns[key["k"]] = ""
        elif key["v"] == "int":
            columns[key["k"]] = 0
        elif key["v"] == "object":
            columns[key["k"]] = {}
        elif key["v"] == "bool":
            columns[key["k"]] = False
        else:
            columns[key["k"]] = None
    return json_util.dumps(columns)


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
