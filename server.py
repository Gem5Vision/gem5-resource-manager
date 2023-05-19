import json
from flask import render_template, Flask, request, redirect, url_for
import os
from dotenv import load_dotenv
from bson import json_util
import jsonschema
import requests
from api.json_client import JSONClient
from api.mongo_client import MongoDBClient

import urllib.parse
import markdown

from werkzeug.utils import secure_filename

from pathlib import Path

databases = {}

schema = {}
with open("schema/schema.json", "r") as f:
    schema = json.load(f)


UPLOAD_FOLDER = Path("database/")
TEMP_UPLOAD_FOLDER = Path("database/.tmp/")
ALLOWED_EXTENSIONS = {"json"}
DATABASE_TYPES = ["mongodb", "json"]


app = Flask(__name__)


# Sorts keys in any serialized dict
# Default = True
# Set False to persevere JSON key order
app.json.sort_keys = False

with app.app_context():
    if not Path(UPLOAD_FOLDER).is_dir():
        Path(UPLOAD_FOLDER).mkdir()
    if not Path(TEMP_UPLOAD_FOLDER).is_dir():
        Path(TEMP_UPLOAD_FOLDER).mkdir()


@app.route("/")
def index():
    """
    Renders the index HTML template.

    :return: The rendered index HTML template.
    """
    return render_template("index.html")


@app.route("/login/mongodb")
def login_mongodb():
    """
    Renders the MongoDB login HTML template.

    :return: The rendered MongoDB login HTML template.
    """
    return render_template("login/login_mongodb.html")


@app.route("/login/json")
def login_json():
    """
    Renders the JSON login HTML template.

    :return: The rendered JSON login HTML template.
    """
    return render_template("login/login_json.html")


@app.route("/validateMongoDB", methods=["POST"])
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
    global databases
    print(request.json)
    # if request.json["alias"] in databases:
    #     return {"error": "alias already exists"}, 409
    try:
        databases[request.json["alias"]] = MongoDBClient(
            mongo_uri=request.json["uri"],
            database_name=request.json["database"],
            collection_name=request.json["collection"],
        )
    except Exception as e:
        return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=DATABASE_TYPES[0], alias=request.json["alias"]),
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
    filename = request.args.get("filename")
    url = request.args.get("q")
    if not url:
        return {"error": "empty"}, 400
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "invalid status"}, response.status_code
    filename = secure_filename(request.args.get("filename"))
    path = Path(UPLOAD_FOLDER) / filename
    if (Path(UPLOAD_FOLDER) / filename).is_file():
        temp_path = Path(TEMP_UPLOAD_FOLDER) / filename
        with Path(temp_path).open("wb") as f:
            f.write(response.content)
        return {"conflict": "existing file in server"}, 409
    with Path(path).open("wb") as f:
        f.write(response.content)
    global databases
    if filename in databases:
        return {"error": "alias already exists"}, 409
    try:
        databases[filename] = JSONClient(filename)
    except Exception as e:
        return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=DATABASE_TYPES[1],
                filename=filename, alias=filename),
        302,
    )


@app.route("/validateJSON", methods=["POST"])
def validate_json_post():
    temp_path = None
    if "file" not in request.files:
        return {"error": "empty"}, 400
    file = request.files["file"]
    filename = secure_filename(file.filename)
    path = Path(UPLOAD_FOLDER) / filename
    if Path(path).is_file():
        temp_path = Path(TEMP_UPLOAD_FOLDER) / filename
        file.save(temp_path)
        return {"conflict": "exisiting file in server"}, 409
    file.save(path)
    global databases
    if filename in databases:
        return {"error": "alias already exists"}, 409
    try:
        databases[filename] = JSONClient(filename)
    except Exception as e:
        return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=DATABASE_TYPES[1],
                filename=filename, alias=filename),
        302,
    )


@app.route("/existingJSON", methods=["GET"])
def existing_json():
    filename = request.args.get("filename")
    global databases
    if filename not in databases:
        try:
            databases[filename] = JSONClient(filename)
        except Exception as e:
            print(e)
            return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=DATABASE_TYPES[1],
                filename=filename, alias=filename),
        302,
    )


@app.route("/existingFiles", methods=["GET"])
def get_existing_files():
    """
    Retrieves the list of existing files in the upload folder.

    This route returns a JSON response containing the names of the existing files in the upload folder configured in the
    Flask application.

    :return: A JSON response with the list of existing files.
    """
    files = [f.name for f in Path(UPLOAD_FOLDER).iterdir() if f.is_file()]
    return json.dumps(files)


@app.route("/resolveConflict", methods=["GET"])
def resolve_conflict():
    filename = request.args.get("filename")
    resolution = request.args.get("resolution")
    resolution_options = ["clearInput",
                          "openExisting", "overwrite", "newFilename"]
    temp_path = Path(TEMP_UPLOAD_FOLDER) / filename
    if not resolution:
        print("no resolution")
        return {"error": "empty"}, 400
    if resolution not in resolution_options:
        print("invalid resolution")
        return {"error": "invalid resolution"}, 400
    if resolution == resolution_options[0]:
        temp_path.unlink()
        return {"success": "input cleared"}, 204
    if resolution in resolution_options[-2:]:
        filename = secure_filename(request.args.get("filename"))
        next(TEMP_UPLOAD_FOLDER.glob("*")).replace(Path(UPLOAD_FOLDER) / filename)
    if Path(temp_path).is_file():
        Path(temp_path).unlink()
    global databases
    if filename in databases:
        return {"error": "alias already exists"}, 409
    try:
        databases[filename] = JSONClient(filename)
    except Exception as e:
        return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=DATABASE_TYPES[1],
                filename=filename, alias=filename),
        302,
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
    global databases
    if not request.args:
        return render_template("404.html"), 404
    alias = request.args.get("alias")
    if alias not in databases:
        return render_template("404.html"), 404
    """ if not (Path(UPLOAD_FOLDER) / alias).is_file():
        return render_template("404.html"), 404 """

    database_type = ""
    if isinstance(databases[alias], JSONClient):
        database_type = "json"
    elif isinstance(databases[alias], MongoDBClient):
        database_type = "mongodb"
    else:
        return render_template("404.html"), 404
    return render_template("editor.html", editor_type=database_type, tagline=alias)


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
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.findResource(request.json)


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
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    original_resource = request.json["original_resource"]
    modified_resource = request.json["resource"]
    status = database.updateResource({
        "original_resource": original_resource,
        "resource": modified_resource,
    })
    database._addToStack({
        "operation": "update",
        "resource": {
            "original_resource": modified_resource,
            "resource": original_resource
        }})
    return status


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
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.getVersions(request.json)


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
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    resource = request.json["resource"]
    status = database.deleteResource(resource)
    database._addToStack({
        "operation": "delete",
        "resource": resource
    })
    return status


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
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    resource = request.json["resource"]
    status = database.insertResource(resource)
    database._addToStack({"operation": "insert", "resource": resource})
    return status


@app.route("/undo", methods=["POST"])
def undo():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.undoOperation()


@app.route("/redo", methods=["POST"])
def redo():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.redoOperation()


@app.route("/getRevisionStatus", methods=["POST"])
def get_revision_status():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.get_revision_status()


@app.route("/saveSession", methods=["POST"])
def save_session():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    session = database.save_session()
    session["alias"] = alias
    return session


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
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.checkResourceExists(request.json)


if __name__ == "__main__":
    app.run(debug=True)
