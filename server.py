from flask import render_template, Flask, request, redirect, url_for, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import json
from bson import json_util

load_dotenv()
# read MONGO_URI from environment variable

MONGO_URI = os.getenv('MONGO_URI')


def get_database():
    CONNECTION_STRING = MONGO_URI
    client = MongoClient(CONNECTION_STRING)
    return client['gem5-vision']['resources_test']


collection = get_database()


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/find', methods=['POST'])
def find():
    resource = collection.find_one({'id': request.json['id']})
    print(resource)
    return json_util.dumps(resource)


@app.route('/update', methods=['POST'])
def update():
    print(request.json)
    # remove _id from request.json
    del request.json['_id']
    collection.update_one(
        {'id': request.json['id']}, {'$set': request.json})
    return {'status': "Updated"}


if __name__ == '__main__':
    app.run(debug=True)
