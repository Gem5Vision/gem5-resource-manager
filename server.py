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

import shutil
from werkzeug.utils import secure_filename

schema = {}
with open("schema/test.json", "r") as f:
    schema = json.load(f)



database = Database("mongodb+srv://admin:gem5vision_admin@gem5-vision.wp3weei.mongodb.net/?retryWrites=true&w=majority", "gem5-vision", "versions_test")

with open("test_json_endpoint.json", "r") as f:
    resources = json.load(f)

UPLOAD_FOLDER = 'database/'
TEMP_UPLOAD_FOLDER = 'database/.tmp/'
ALLOWED_EXTENSIONS = {'json'}

resources = None
isMongo = True

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_UPLOAD_FOLDER'] = TEMP_UPLOAD_FOLDER

app.config['FILEPATH'] = None
app.config['TEMP_FILEPATH'] = None

app.config['DATABASE_TYPES'] = ["mongodb", "json"]

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login/<string:database_type>")
def login(database_type):
    if database_type not in app.config['DATABASE_TYPES']:
        return render_template("404.html")
    if database_type == app.config['DATABASE_TYPES'][0]:
        return render_template("mongoDBLogin.html")
    if database_type == app.config['DATABASE_TYPES'][1]:
        return render_template("jsonLogin.html")
     

@app.route("/validateMongoDB", methods=['GET'])
def validate_mongodb():
    uri = request.args.get('uri')
    collection = request.args.get('collection')
    database = request.args.get('database')
    alias = request.args.get('alias')
    if uri == "":
        return {"error" : "empty"}, 400
    return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][0], uri=uri, collection=collection, database=database, alias=alias), 302)


@app.route("/validateJSON", methods=["GET"])
def validate_json_get():
    global resources
    url = request.args.get('q')
    if not url:
        return {"error" : "empty"}, 400    
    response = requests.get(url)
    if response.status_code != 200:
        return {"error" : "invalid status"}, response.status_code
    filename = secure_filename(request.args.get('filename'))
    app.config['FILEPATH'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        app.config['TEMP_FILEPATH'] = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], filename)
        with open(app.config['TEMP_FILEPATH'], 'wb') as f:
            f.write(response.content)
        return {"conflict" : "existing file in server"}, 409
    with open(app.config['FILEPATH'], 'wb') as f:
        f.write(response.content)
    return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][1], filename=filename), 302)


@app.route('/existingFiles', methods=['GET'])
def get_exisitng_files():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return json.dumps(files)


@app.route("/validateJSON", methods=["POST"]) 
def validate_json_post():
    global resources
    if 'file' not in request.files:
        return {"error" : "empty"}, 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    app.config['FILEPATH'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.isfile(app.config['FILEPATH']): 
        app.config['TEMP_FILEPATH'] = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], filename)
        file.save(app.config['TEMP_FILEPATH'])
        return {"conflict" : "exisitng file in server"}, 409
    file.save(app.config['FILEPATH'])
    with open(app.config['FILEPATH'], 'r') as f:
        resources = json.load(f)
        return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][1], filename=os.path.basename(app.config['FILEPATH'])), 302)


@app.route("/resolveConflict", methods=["GET"])
def resolve_conflict():
    global resources
    filename = None
    resolution = request.args.get("resolution")
    resolution_options = ["clearInput", "openExisting", "overwrite", "newFilename"]
    if not resolution:
        return {"error" : "empty"}, 400 
    if resolution not in resolution_options:
        return {"error" : "invalid resolution"}, 400
    if resolution == resolution_options[0]:
        os.remove(app.config['TEMP_FILEPATH'])
        app.config['TEMP_FILEPATH'] = None
        resources = None
        return {"success" : "input cleared"}, 204
    elif resolution == resolution_options[1]:
        filename = os.path.basename(app.config['FILEPATH'])
    elif resolution == resolution_options[2]:
        os.remove(app.config['FILEPATH'])
        shutil.move(app.config['TEMP_FILEPATH'], app.config['UPLOAD_FOLDER'])
        app.config['FILEPATH'] = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(app.config['TEMP_FILEPATH']))
        filename = os.path.basename(app.config['FILEPATH'])
    elif resolution == resolution_options[3]:
        new_filename = secure_filename(request.args.get("filename"))
        new_temp_filepath = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], new_filename)
        os.rename(app.config['TEMP_FILEPATH'], new_temp_filepath)
        app.config['FILEPATH'] = shutil.move(new_temp_filepath, app.config['UPLOAD_FOLDER'])
        filename = new_filename
    if os.path.isfile(app.config['TEMP_FILEPATH']): 
        os.remove(app.config['TEMP_FILEPATH'])
    app.config['TEMP_FILEPATH'] = None
    with open(app.config['FILEPATH'], 'r') as f:
        resources = json.load(f)
    return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][1], filename=filename), 302) 


@app.route("/editor")
def editor():
    if not request.args:
        return render_template("404.html"), 404
    global isMongo
    global database
    global resources
    type = request.args.get("type")
    if type not in app.config['DATABASE_TYPES']:
        return render_template("404.html"), 404
    if type == app.config['DATABASE_TYPES'][0]:
        isMongo = True
        mongo_uri = urllib.parse.unquote(request.args.get('uri'))
        alias = request.args.get('alias')
        database.change_database(mongo_uri, request.args.get('database'), request.args.get('collection'))
        return render_template("editor.html", editor_type=app.config['DATABASE_TYPES'][0], tagline=(mongo_uri if alias == "" else alias))
    if type == app.config['DATABASE_TYPES'][1]:
        isMongo = False
        filename = request.args.get('filename')
        if not os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)): 
            return render_template("404.html"), 404
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'r') as f:
            resources = json.load(f)
        return render_template("editor.html", editor_type=app.config['DATABASE_TYPES'][1], tagline=filename)


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
