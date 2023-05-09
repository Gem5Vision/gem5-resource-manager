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

from werkzeug.utils import secure_filename

from pathlib import Path

schema = {}
with open("schema/test.json", "r") as f:
    schema = json.load(f)


with open("test_json_endpoint.json", "r") as f:
    resources = json.load(f)

UPLOAD_FOLDER = Path('database/')
TEMP_UPLOAD_FOLDER = Path('database/.tmp/')
ALLOWED_EXTENSIONS = {'json'}

resources = None
isMongo = True

app = Flask(__name__)
app.config['DATABASE'] = Database("mongodb+srv://admin:gem5vision_admin@gem5-vision.wp3weei.mongodb.net/?retryWrites=true&w=majority", "gem5-vision", "versions_test")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_UPLOAD_FOLDER'] = TEMP_UPLOAD_FOLDER

app.config['FILEPATH'] = None
app.config['TEMP_FILEPATH'] = None

app.config['DATABASE_TYPES'] = ["mongodb", "json"]


with app.app_context():
    if not Path(app.config['UPLOAD_FOLDER']).is_dir():
        Path(app.config['UPLOAD_FOLDER']).mkdir()
    if not Path(app.config['TEMP_UPLOAD_FOLDER']).is_dir():
        Path(app.config['TEMP_UPLOAD_FOLDER']).mkdir()


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
    app.config['FILEPATH'] = Path(app.config['UPLOAD_FOLDER']) / filename
    if (Path(app.config['UPLOAD_FOLDER']) / filename).is_file():
        app.config['TEMP_FILEPATH'] = Path(app.config['TEMP_UPLOAD_FOLDER']) / filename
        with Path(app.config['TEMP_FILEPATH']).open('wb') as f:
            f.write(response.content)
        return {"conflict" : "existing file in server"}, 409
    with Path(app.config['FILEPATH']).open('wb') as f:
        f.write(response.content)
    return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][1], filename=filename), 302)


@app.route('/existingFiles', methods=['GET'])
def get_existing_files():
    files = [f.name for f in Path(app.config['UPLOAD_FOLDER']).iterdir() if f.is_file()]
    return json.dumps(files)


@app.route("/validateJSON", methods=["POST"]) 
def validate_json_post():
    global resources
    if 'file' not in request.files:
        return {"error" : "empty"}, 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    app.config['FILEPATH'] = Path(app.config['UPLOAD_FOLDER']) / filename
    if Path(app.config['FILEPATH']).is_file(): 
        app.config['TEMP_FILEPATH'] = Path(app.config['TEMP_UPLOAD_FOLDER']) / filename
        file.save(app.config['TEMP_FILEPATH'])
        return {"conflict" : "exisitng file in server"}, 409
    file.save(app.config['FILEPATH'])
    with Path(app.config['FILEPATH']).open('r') as f:
        resources = json.load(f)
        return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][1], filename=Path(app.config['FILEPATH']).name), 302)


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
        Path(app.config['TEMP_FILEPATH']).unlink()
        app.config['TEMP_FILEPATH'] = None
        resources = None
        return {"success" : "input cleared"}, 204
    elif resolution == resolution_options[1]:
        filename = Path(app.config['FILEPATH']).name
    elif resolution == resolution_options[2]:
        app.config['FILEPATH'] = Path(app.config['TEMP_FILEPATH']).replace(app.config['FILEPATH'])
        filename = Path(app.config['FILEPATH']).name
    elif resolution == resolution_options[3]:
        filename = secure_filename(request.args.get("filename"))
        app.config['FILEPATH'] = Path(app.config['TEMP_FILEPATH']).replace(Path(app.config['UPLOAD_FOLDER']) / filename)
    if Path(app.config['TEMP_FILEPATH']).is_file(): 
        Path(app.config['TEMP_FILEPATH']).unlink()
    app.config['TEMP_FILEPATH'] = None
    with Path(app.config['FILEPATH']).open('r') as f:
        resources = json.load(f)
    return redirect(url_for("editor", type=app.config['DATABASE_TYPES'][1], filename=filename), 302) 


@app.route("/editor")
def editor():
    if not request.args:
        return render_template("404.html"), 404
    global isMongo
    global resources
    type = request.args.get("type")
    if type not in app.config['DATABASE_TYPES']:
        return render_template("404.html"), 404
    if type == app.config['DATABASE_TYPES'][0]:
        isMongo = True
        mongo_uri = urllib.parse.unquote(request.args.get('uri'))
        alias = request.args.get('alias')
        app.config['DATABASE'].change_database(mongo_uri, request.args.get('database'), request.args.get('collection'))
        return render_template("editor.html", editor_type=app.config['DATABASE_TYPES'][0], tagline=(mongo_uri if alias == "" else alias))
    if type == app.config['DATABASE_TYPES'][1]:
        isMongo = False
        filename = request.args.get('filename')
        if not (Path(app.config['UPLOAD_FOLDER']) / filename).is_file():
            return render_template("404.html"), 404
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        with filepath.open('r') as f:
            resources = json.load(f)
        #Set FILEPATH if editor accessed directly w/o login 
        if not app.config['FILEPATH'] or not filepath.samefile(Path(app.config['FILEPATH'])):
            app.config['FILEPATH'] = filepath
        return render_template("editor.html", editor_type=app.config['DATABASE_TYPES'][1], tagline=filename)


@app.route("/help")
def help():
    with Path('static/help.md').open('r') as f:
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
        return mongo_db_api.findResource(app.config['DATABASE'], request.json)
    return json_api.findResource(resources, request.json)


@app.route("/update", methods=["POST"])
def update():
    if isMongo:
        return mongo_db_api.updateResource(app.config['DATABASE'], request.json)
    return json_api.updateResource(resources, request.json,app.config['FILEPATH'])


@app.route("/versions", methods=["POST"])
def getVersions():
    if isMongo:
        return mongo_db_api.getVersions(app.config['DATABASE'], request.json)
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
        return mongo_db_api.deleteResource(app.config['DATABASE'], request.json)
    return json_api.deleteResource(resources, request.json, app.config['FILEPATH'])


@app.route("/insert", methods=["POST"])
def insert():
    # print("resource before insert:\n", resources)
    if isMongo:
        return mongo_db_api.insertResource(app.config['DATABASE'], request.json)
    return json_api.insertResource(resources, request.json, app.config['FILEPATH'])


@app.errorhandler(404)
def handle404(error):
    return render_template('404.html'), 404


@app.route("/checkExists", methods=["POST"])
def checkExists():
    if isMongo:
        return mongo_db_api.checkResourceExists(app.config['DATABASE'], request.json)
    return json_api.checkResourceExists(resources, request.json)


if __name__ == "__main__":
    app.run(debug=True)
