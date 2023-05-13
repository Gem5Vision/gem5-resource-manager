import json
from flask import render_template, Flask, request, redirect, url_for, Response
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema
from api.database import Database, DatabaseConnectionError
import requests

import urllib.parse
import markdown

from api import mongo_db_api, json_api

from werkzeug.utils import secure_filename

from pathlib import Path

schema = {}
with open("schema/schema.json", "r") as f:
    schema = json.load(f)


UPLOAD_FOLDER = Path("database/")
TEMP_UPLOAD_FOLDER = Path("database/.tmp/")
ALLOWED_EXTENSIONS = {"json"}

resources = None
isMongo = False

app = Flask(__name__)
# The database configuration for the Flask application.

# DATABASE: An instance of the Database class representing the MongoDB connection details and database/collection names.
# app.config["DATABASE"] = Database(
#     "mongodb+srv://admin:gem5vision_admin@gem5-vision.wp3weei.mongodb.net/?retryWrites=true&w=majority",
#     "gem5-vision",
#     "versions_test",
# )

app.config["DATABASE"] = None

# The folder path where uploaded files will be stored.
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# The temporary folder path where uploaded files will be temporarily stored before processing.
app.config["TEMP_UPLOAD_FOLDER"] = TEMP_UPLOAD_FOLDER

# The file path used in the application. Currently set to None.
app.config["FILEPATH"] = None

# The temporary file path used in the application. Currently set to None.
app.config["TEMP_FILEPATH"] = None

# The supported types of databases for login in the application.
app.config["DATABASE_TYPES"] = ["mongodb", "json"]


with app.app_context():
    if not Path(app.config["UPLOAD_FOLDER"]).is_dir():
        Path(app.config["UPLOAD_FOLDER"]).mkdir()
    if not Path(app.config["TEMP_UPLOAD_FOLDER"]).is_dir():
        Path(app.config["TEMP_UPLOAD_FOLDER"]).mkdir()


@app.route("/")
def index():
    """
    Renders the index HTML template.

    :return: The rendered index HTML template.
    """
    return render_template("index.html")


@app.route("/login/<string:database_type>")
def login(database_type):
    """
    Renders the login HTML template based on the provided database type.

    :param database_type: The type of the database for login. Must be one of the supported database types defined in the
                          Flask application configuration.
    :return: The rendered login HTML template corresponding to the database type. Returns a 404 error template if the
             database type is not supported.
    """
    if database_type not in app.config["DATABASE_TYPES"]:
        return render_template("404.html")
    if database_type == app.config["DATABASE_TYPES"][0]:
        return render_template("mongoDBLogin.html")
    if database_type == app.config["DATABASE_TYPES"][1]:
        return render_template("jsonLogin.html")


@app.route("/validateMongoDB", methods=["GET"])
def validate_mongodb():
    """
    Validates the MongoDB connection parameters and redirects to the editor route if successful.

    This route expects the following query parameters:
    - uri: The MongoDB connection URI.
    - collection: The name of the collection in the MongoDB database.
    - database: The name of the MongoDB database.
    - alias: An optional alias for the MongoDB configuration.

    If the 'uri' parameter is empty, a JSON response with an error message and status code 400 (Bad Request) is returned.
    If the connection parameters are valid, the route redirects to the 'editor' route with the appropriate query parameters.

    :return: A redirect response to the 'editor' route or a JSON response with an error message and status code 400.
    """
    uri = request.args.get("uri")
    collection = request.args.get("collection")
    database = request.args.get("database")
    alias = request.args.get("alias")
    if uri == "":
        return {"error": "Cannot proceed with empty URI"}, 400
    return redirect(
        url_for(
            "editor",
            type=app.config["DATABASE_TYPES"][0],
            uri=uri,
            collection=collection,
            database=database,
            alias=alias,
        ),
        302,
    )


@app.route("/validateJSON", methods=["GET"])
def validate_json_get():
    """
    Validates the provided JSON URL and redirects to the editor route if successful.

    This route expects the following query parameters:
    - q: The URL of the JSON file.
    - filename: An optional filename for the uploaded JSON file.

    If the 'q' parameter is empty, a JSON response with an error message and status code 400 (Bad Request) is returned.
    If the JSON URL is valid, the function retrieves the JSON content, saves it to a file, and redirects to the 'editor'
    route with the appropriate query parameters.

    :return: A redirect response to the 'editor' route or a JSON response with an error message and status code 400.
    """
    global resources
    url = request.args.get("q")
    if not url:
        return {"error": "empty"}, 400
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "invalid status"}, response.status_code
    filename = secure_filename(request.args.get("filename"))
    app.config["FILEPATH"] = Path(app.config["UPLOAD_FOLDER"]) / filename
    if (Path(app.config["UPLOAD_FOLDER"]) / filename).is_file():
        app.config["TEMP_FILEPATH"] = Path(
            app.config["TEMP_UPLOAD_FOLDER"]) / filename
        with Path(app.config["TEMP_FILEPATH"]).open("wb") as f:
            f.write(response.content)
        return {"conflict": "existing file in server"}, 409
    with Path(app.config["FILEPATH"]).open("wb") as f:
        f.write(response.content)
    return redirect(
        url_for(
            "editor", type=app.config["DATABASE_TYPES"][1], filename=filename), 302
    )


@app.route("/existingFiles", methods=["GET"])
def get_existing_files():
    """
    Retrieves the list of existing files in the upload folder.

    This route returns a JSON response containing the names of the existing files in the upload folder configured in the
    Flask application.

    :return: A JSON response with the list of existing files.
    """
    files = [f.name for f in Path(
        app.config["UPLOAD_FOLDER"]).iterdir() if f.is_file()]
    return json.dumps(files)


@app.route("/validateJSON", methods=["POST"])
def validate_json_post():
    global resources
    if "file" not in request.files:
        return {"error": "empty"}, 400
    file = request.files["file"]
    filename = secure_filename(file.filename)
    app.config["FILEPATH"] = Path(app.config["UPLOAD_FOLDER"]) / filename
    if Path(app.config["FILEPATH"]).is_file():
        app.config["TEMP_FILEPATH"] = Path(
            app.config["TEMP_UPLOAD_FOLDER"]) / filename
        file.save(app.config["TEMP_FILEPATH"])
        return {"conflict": "exisiting file in server"}, 409
    file.save(app.config["FILEPATH"])
    with Path(app.config["FILEPATH"]).open("r") as f:
        resources = json.load(f)
        return redirect(
            url_for(
                "editor",
                type=app.config["DATABASE_TYPES"][1],
                filename=Path(app.config["FILEPATH"]).name,
            ),
            302,
        )


@app.route("/resolveConflict", methods=["GET"])
def resolve_conflict():
    """
    Handles the resolution of conflicts when updating a JSON file.

    This route expects a GET request with specific query parameters:
    - "resolution": Specifies the resolution option for the conflict. Should be one of the following values:
        - "clearInput": Clear the input and reset the resources.
        - "openExisting": Open the existing file.
        - "overwrite": Overwrite the existing file with the updated content.
        - "newFilename": Save the updated content with a new filename.
    - "filename": The new filename to be used. This parameter is required if the resolution is "newFilename".

    The function checks if the "resolution" query parameter is present. If not, it returns a 400 error.

    The function validates the "resolution" against a list of valid resolution options. If the resolution is not valid,
    it returns a 400 error.

    Based on the resolution option, the function performs the following actions:
    - If the resolution is "clearInput", it unlinks the temporary file, clears the resources, and returns a success response.
    - If the resolution is "openExisting", it retrieves the filename from the FILEPATH configuration.
    - If the resolution is "overwrite", it replaces the FILEPATH configuration with the temporary file path and retrieves the filename.
    - If the resolution is "newFilename", it retrieves the new filename from the query parameters, replaces the FILEPATH configuration
      with the temporary file path, and retrieves the new filename.

    If the temporary file exists, it is unlinked. The TEMP_FILEPATH configuration is reset to None.

    The function reads the content of the updated file specified by the FILEPATH configuration and loads it into the resources variable.

    Finally, it redirects to the editor page with the JSON editor type and the resolved filename.

    :return: A redirect response to the editor page with the resolved filename.
    """
    global resources
    filename = None
    resolution = request.args.get("resolution")
    resolution_options = ["clearInput",
                          "openExisting", "overwrite", "newFilename"]
    if not resolution:
        return {"error": "empty"}, 400
    if resolution not in resolution_options:
        return {"error": "invalid resolution"}, 400
    if resolution == resolution_options[0]:
        Path(app.config["TEMP_FILEPATH"]).unlink()
        app.config["TEMP_FILEPATH"] = None
        resources = None
        return {"success": "input cleared"}, 204
    elif resolution == resolution_options[1]:
        filename = Path(app.config["FILEPATH"]).name
    elif resolution == resolution_options[2]:
        app.config["FILEPATH"] = Path(app.config["TEMP_FILEPATH"]).replace(
            app.config["FILEPATH"]
        )
        filename = Path(app.config["FILEPATH"]).name
    elif resolution == resolution_options[3]:
        filename = secure_filename(request.args.get("filename"))
        app.config["FILEPATH"] = Path(app.config["TEMP_FILEPATH"]).replace(
            Path(app.config["UPLOAD_FOLDER"]) / filename
        )
    if Path(app.config["TEMP_FILEPATH"]).is_file():
        Path(app.config["TEMP_FILEPATH"]).unlink()
    app.config["TEMP_FILEPATH"] = None
    with Path(app.config["FILEPATH"]).open("r") as f:
        resources = json.load(f)
    return redirect(
        url_for(
            "editor", type=app.config["DATABASE_TYPES"][1], filename=filename), 302
    )


@app.route("/editor")
def editor():
    """
    Renders the editor page based on the specified database type.

    This route expects a GET request with specific query parameters:
    - "type": Specifies the type of the editor, which should be one of the values in the "DATABASE_TYPES" configuration.
    - "uri": The URI for the MongoDB database. This parameter is required if the editor type is MongoDB.
    - "alias": An optional alias for the MongoDB database.
    - "database": The name of the MongoDB database.
    - "collection": The name of the MongoDB collection.
    - "filename": The name of the JSON file. This parameter is required if the editor type is JSON.

    The function checks if the query parameters are present. If not, it returns a 404 error.

    The function determines the database type based on the "type" query parameter. If the type is not in the
    "DATABASE_TYPES" configuration, it returns a 404 error.

    If the database type is MongoDB, the function sets the global variable "isMongo" to True, extracts the MongoDB
    URI, database name, and collection name from the query parameters, and updates the database configuration accordingly.
    It then renders the editor template with the MongoDB editor type and the provided tagline.

    If the database type is JSON, the function sets the global variable "isMongo" to False, retrieves the filename from
    the query parameters, and checks if the file exists in the upload folder. If the file does not exist, it returns a 404 error.
    It reads the JSON data from the file and sets the global variable "resources" to the loaded JSON data. If the FILEPATH
    configuration is not set or does not match the current file, it updates the FILEPATH configuration with the current file path.
    It then renders the editor template with the JSON editor type and the provided tagline.

    :return: The rendered editor template based on the specified database type.
    """
    if not request.args:
        return render_template("404.html"), 404
    global isMongo
    global resources
    type = request.args.get("type")
    if type not in app.config["DATABASE_TYPES"]:
        return render_template("404.html"), 404
    if type == app.config["DATABASE_TYPES"][0]:
        isMongo = True
        mongo_uri = urllib.parse.unquote(request.args.get("uri"))
        alias = request.args.get("alias")
        try:
            app.config["DATABASE"] = Database(
                mongo_uri, request.args.get(
                    "database"), request.args.get("collection")
            )
        except DatabaseConnectionError as e:
            return {"error": f"{e}"}, 400

        return render_template(
            "editor.html",
            editor_type=app.config["DATABASE_TYPES"][0],
            tagline=(mongo_uri if alias == "" else alias),
        )
    if type == app.config["DATABASE_TYPES"][1]:
        isMongo = False
        filename = request.args.get("filename")
        if not (Path(app.config["UPLOAD_FOLDER"]) / filename).is_file():
            return render_template("404.html"), 404
        filepath = Path(app.config["UPLOAD_FOLDER"]) / filename
        with filepath.open("r") as f:
            resources = json.load(f)
        # Set FILEPATH if editor accessed directly w/o login
        if not app.config["FILEPATH"] or not filepath.samefile(
            Path(app.config["FILEPATH"])
        ):
            app.config["FILEPATH"] = filepath
        return render_template(
            "editor.html", editor_type=app.config["DATABASE_TYPES"][1], tagline=filename
        )


@app.route("/help")
def help():
    """
    Renders the help page.

    This route reads the contents of the "help.md" file located in the "static" folder and renders it as HTML using the
    Markdown syntax. The rendered HTML is then passed to the "help.html" template for displaying the help page.

    :return: The rendered help page HTML.
    """
    with Path("static/help.md").open("r") as f:
        return render_template("help.html", rendered_html=markdown.markdown(f.read()))


@app.route("/toggleIsMongo", methods=["POST"])
def toggleIsMongo():
    # input is a json object with a single key "isMongo"
    # {"isMongo": true/false}
    isMongo = request.json["isMongo"]
    return {"isMongo": isMongo}


@app.route("/find", methods=["POST"])
def find():
    """
    Finds a resource based on the provided search criteria.

    This route expects a POST request with a JSON payload containing the search criteria. The route determines the
    appropriate method for finding the resource based on the value of the `isMongo` flag.

    If `isMongo` is True, the MongoDB API is used to find the resource by calling `mongo_db_api.findResource()` with the
    database configuration from the Flask application's configuration.

    If `isMongo` is False, the JSON API is used to find the resource by calling `json_api.findResource()` with the
    `resources` variable.

    The result of the find operation is returned as a JSON response.

    :return: A JSON response containing the result of the find operation.
    """
    if isMongo:
        return mongo_db_api.findResource(app.config["DATABASE"], request.json)
    return json_api.findResource(resources, request.json)


@app.route("/update", methods=["POST"])
def update():
    """
    Updates a resource based on the provided data.

    This route expects a POST request with a JSON payload containing the data for updating the resource. The route
    determines the appropriate method for updating the resource based on the value of the `isMongo` flag.

    If `isMongo` is True, the MongoDB API is used to update the resource by calling `mongo_db_api.updateResource()` with
    the database configuration from the Flask application's configuration.

    If `isMongo` is False, the JSON API is used to update the resource by calling `json_api.updateResource()` with the
    `resources` variable and the filepath from the Flask application's configuration.

    The result of the update operation is returned as a JSON response.

    :return: A JSON response containing the result of the update operation.
    """
    if isMongo:
        return mongo_db_api.updateResource(app.config["DATABASE"], request.json)
    return json_api.updateResource(resources, request.json, app.config["FILEPATH"])


@app.route("/versions", methods=["POST"])
def getVersions():
    """
    Retrieves the versions of a resource based on the provided search criteria.

    This route expects a POST request with a JSON payload containing the search criteria. The route determines the
    appropriate method for retrieving the versions based on the value of the `isMongo` flag.

    If `isMongo` is True, the MongoDB API is used to retrieve the versions by calling `mongo_db_api.getVersions()` with
    the database configuration from the Flask application's configuration.

    If `isMongo` is False, the JSON API is used to retrieve the versions by calling `json_api.getVersions()` with the
    `resources` variable.

    The result of the versions retrieval is returned as a JSON response.

    :return: A JSON response containing the versions of the resource.
    """
    if isMongo:
        return mongo_db_api.getVersions(app.config["DATABASE"], request.json)
    return json_api.getVersions(resources, request.json)


@app.route("/categories", methods=["GET"])
def getCategories():
    """
    Retrieves the categories of the resources.

    This route returns a JSON response containing the categories of the resources. The categories are obtained from the
    "enum" property of the "category" field in the schema.

    :return: A JSON response with the categories of the resources.
    """
    return json.dumps(schema["properties"]["category"]["enum"])


@app.route("/schema", methods=["GET"])
def getSchema():
    """
    Retrieves the schema definition of the resources.

    This route returns a JSON response containing the schema definition of the resources. The schema is obtained from the
    `schema` variable.

    :return: A JSON response with the schema definition of the resources.
    """
    return json_util.dumps(schema)


@app.route("/keys", methods=["POST"])
def getFields():
    """
    Retrieves the required fields for a specific category based on the provided data.

    This route expects a POST request with a JSON payload containing the data for retrieving the required fields.
    The function constructs an empty object `empty_object` with the "category" and "id" values from the request payload.

    The function then uses the JSONSchema validator to validate the `empty_object` against the `schema`. It iterates
    through the validation errors and handles two types of errors:

    1. "is a required property" error: If a required property is missing in the `empty_object`, the function retrieves
       the default value for that property from the schema and sets it in the `empty_object`.

    2. "is not valid under any of the given schemas" error: If a property is not valid under the current schema, the
       function evolves the validator to use the schema corresponding to the requested category. It then iterates
       through the validation errors again and handles any missing required properties as described in the previous
       step.

    Finally, the `empty_object` with the required fields populated (including default values if applicable) is returned
    as a JSON response.

    :return: A JSON response containing the `empty_object` with the required fields for the specified category.
    """
    empty_object = {
        "category": request.json["category"], "id": request.json["id"]}
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(empty_object))
    for error in errors:
        if "is a required property" in error.message:
            required = error.message.split("'")[1]
            empty_object[required] = error.schema["properties"][required]["default"]
        if "is not valid under any of the given schemas" in error.message:
            validator = validator.evolve(
                schema=error.schema["definitions"][request.json["category"]]
            )
            for e in validator.iter_errors(empty_object):
                if "is a required property" in e.message:
                    required = e.message.split("'")[1]
                    if "default" in e.schema["properties"][required]:
                        empty_object[required] = e.schema["properties"][required][
                            "default"
                        ]
                    else:
                        empty_object[required] = ""
    return json.dumps(empty_object)


@app.route("/delete", methods=["POST"])
def delete():
    """
    Deletes a resource based on the provided data.

    This route expects a POST request with a JSON payload containing the data for deleting the resource. The route
    determines the appropriate method for deleting the resource based on the value of the `isMongo` flag.

    If `isMongo` is True, the MongoDB API is used to delete the resource by calling `mongo_db_api.deleteResource()` with
    the database configuration from the Flask application's configuration.

    If `isMongo` is False, the JSON API is used to delete the resource by calling `json_api.deleteResource()` with the
    `resources` variable and the filepath from the Flask application's configuration.

    The result of the delete operation is returned as a JSON response.

    :return: A JSON response containing the result of the delete operation.
    """
    if isMongo:
        return mongo_db_api.deleteResource(app.config["DATABASE"], request.json)
    return json_api.deleteResource(resources, request.json, app.config["FILEPATH"])


@app.route("/insert", methods=["POST"])
def insert():
    """
    Inserts a new resource based on the provided data.

    This route expects a POST request with a JSON payload containing the data for inserting the resource. The route
    determines the appropriate method for inserting the resource based on the value of the `isMongo` flag.

    If `isMongo` is True, the MongoDB API is used to insert the resource by calling `mongo_db_api.insertResource()` with
    the database configuration from the Flask application's configuration.

    If `isMongo` is False, the JSON API is used to insert the resource by calling `json_api.insertResource()` with the
    `resources` variable and the filepath from the Flask application's configuration.

    The result of the insert operation is returned as a JSON response.

    :return: A JSON response containing the result of the insert operation.
    """
    if isMongo:
        return mongo_db_api.insertResource(app.config["DATABASE"], request.json)
    return json_api.insertResource(resources, request.json, app.config["FILEPATH"])


@app.errorhandler(404)
def handle404(error):
    """
    Error handler for 404 (Not Found) errors.

    This function is called when a 404 error occurs. It renders the "404.html" template and returns it as a response with
    a status code of 404.

    :param error: The error object representing the 404 error.
    :return: A response containing the rendered "404.html" template with a status code of 404.
    """
    return render_template("404.html"), 404


@app.route("/checkExists", methods=["POST"])
def checkExists():
    """
    Checks if a resource exists based on the provided data.

    This route expects a POST request with a JSON payload containing the data for checking the existence of the resource.
    The route determines the appropriate method for checking the existence based on the value of the `isMongo` flag.

    If `isMongo` is True, the MongoDB API is used to check the existence of the resource by calling
    `mongo_db_api.checkResourceExists()` with the database configuration from the Flask application's configuration.

    If `isMongo` is False, the JSON API is used to check the existence of the resource by calling
    `json_api.checkResourceExists()` with the `resources` variable.

    The result of the existence check is returned as a JSON response.

    :return: A JSON response containing the result of the existence check.
    """
    if isMongo:
        return mongo_db_api.checkResourceExists(app.config["DATABASE"], request.json)
    return json_api.checkResourceExists(resources, request.json)


if __name__ == "__main__":
    app.run(debug=True)
