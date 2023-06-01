import json
from flask import render_template, Flask, request, redirect, url_for, make_response
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

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import secrets

from cryptography.exceptions import InvalidSignature

from pathlib import Path

databases = {}

response = requests.get("https://resources.gem5.org/gem5-resources-schema.json")
if not response:
    schema = {}
    with open("schema/schema.json", "r") as f:
        schema = json.load(f)
else:
    schema = json.loads(response.content)



UPLOAD_FOLDER = Path("database/")
TEMP_UPLOAD_FOLDER = Path("database/.tmp/")
CONFIG_FILE = Path("instance/config.py")
SESSIONS_COOKIE_KEY = "sessions"
ALLOWED_EXTENSIONS = {"json"}
CLIENT_TYPES = ["mongodb", "json"]


app = Flask(__name__, instance_relative_config=True)


if not CONFIG_FILE.exists():
    CONFIG_FILE.parent.mkdir()
    with CONFIG_FILE.open("w+") as f:
        f.write(f"SECRET_KEY = {secrets.token_bytes(32)}")


app.config.from_pyfile(CONFIG_FILE.name)


# Sorts keys in any serialized dict
# Default = True
# Set False to persevere JSON key order
app.json.sort_keys = False


def startup_config_validation():
    if not app.secret_key:
        raise ValueError("SECRET_KEY not set")
    if not isinstance(app.secret_key, bytes):
        raise ValueError("SECRET_KEY must be of type 'bytes'")


def startup_dir_file_validation():
    for dir in [UPLOAD_FOLDER, TEMP_UPLOAD_FOLDER]:
        if not dir.is_dir():
            dir.mkdir()


with app.app_context():
    startup_config_validation()
    startup_dir_file_validation()


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
    try:
        databases[request.json["alias"]] = MongoDBClient(
            mongo_uri=request.json["uri"],
            database_name=request.json["database"],
            collection_name=request.json["collection"],
        )
    except Exception as e:
        return {"error": str(e)}, 400
    # print(f"\nDATABASES: {databases}\n")
    return redirect(
        url_for("editor", type=CLIENT_TYPES[0], alias=request.json["alias"]),
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
        url_for("editor", type=CLIENT_TYPES[1],
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
        return {"conflict": "existing file in server"}, 409
    file.save(path)
    global databases
    if filename in databases:
        return {"error": "alias already exists"}, 409
    try:
        databases[filename] = JSONClient(filename)
    except Exception as e:
        return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=CLIENT_TYPES[1],
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
            # print(e)
            return {"error": str(e)}, 400
    return redirect(
        url_for("editor", type=CLIENT_TYPES[1],
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
        # print("no resolution")
        return {"error": "empty"}, 400
    if resolution not in resolution_options:
        # print("invalid resolution")
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
        url_for("editor", type=CLIENT_TYPES[1],
                filename=filename, alias=filename),
        302,
    )


@app.route("/editor")
def editor():
    """
    Renders the editor page based on the specified database type.

    This route expects a GET request with specific query parameters:
    - "type": Specifies the type of the editor, which should be one of the values in the "CLIENT_TYPES" configuration.
    - "uri": The URI for the MongoDB database. This parameter is required if the editor type is MongoDB.
    - "alias": An optional alias for the MongoDB database.
    - "database": The name of the MongoDB database.
    - "collection": The name of the MongoDB collection.
    - "filename": The name of the JSON file. This parameter is required if the editor type is JSON.

    The function checks if the query parameters are present. If not, it returns a 404 error.

    The function determines the database type based on the "type" query parameter. If the type is not in the
    "CLIENT_TYPES" configuration, it returns a 404 error.

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
    # print("test")
    global databases
    if not request.args:
        return render_template("404.html"), 404
    alias = request.args.get("alias")
    if alias not in databases:
        return render_template("404.html"), 404
    """ if not (Path(UPLOAD_FOLDER) / alias).is_file():
        return render_template("404.html"), 404 """

    client_type = ""
    if isinstance(databases[alias], JSONClient):
        client_type = "json"
    elif isinstance(databases[alias], MongoDBClient):
        client_type = "mongodb"
    else:
        return render_template("404.html"), 404

    response = make_response(render_template(
        "editor.html", client_type=client_type, alias=alias))

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


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
    return database.find_resource(request.json)


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
    status = database.update_resource({
        "original_resource": original_resource,
        "resource": modified_resource,
    })
    database._add_to_stack({
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
    return database.get_versions(request.json)


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
    status = database.delete_resource(resource)
    database._add_to_stack({
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
    status = database.insert_resource(resource)
    database._add_to_stack({"operation": "insert", "resource": resource})
    return status


@app.route("/undo", methods=["POST"])
def undo():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.undo_operation()


@app.route("/redo", methods=["POST"])
def redo():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.redo_operation()


@app.route("/getRevisionStatus", methods=["POST"])
def get_revision_status():
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    database = databases[alias]
    return database.get_revision_status()


def fernet_instance_generation(password):
    """
    Generates Fernet instance for use in Saving/Loading Session. 

    Utilizes Scrypt Key Derivation Function with `SECRET_KEY` as salt value and recommended
    values for `length`, `n`, `r`, and `p` parameters. Derives key using `password`. Derived
    key is then used to initialize Fernet instance.

    :param password: User provided password
    :return: Fernet instance 
    """
    return Fernet(
        base64.urlsafe_b64encode(
            Scrypt(
                salt=app.secret_key,
                length=32,
                n=2**16,
                r=8,
                p=1).derive(password.encode())
        )
    )


@app.route("/saveSession", methods=["POST"])
def save_session():
    """
    Saves current session to file `SESSION_FILE`. 

    This route expects a POST request with a JSON payload containing the alias of the current session that is to be 
    saved and a password to be used in encrypting the session data. 

    The alias is used in retrieving the session from `databases`. The `save_session()` method is called to get 
    the necessary session data from the corresponding `Client` as a dictionary.

    A Fernet instance, using the user provided password, is instantiated. The session data is encrypted using this
    instance. If an Exception is raised, an error response is returned.

    The encrypted session data is then appended to `SESSION_FILE` and a success response is returned. 

    The result of the save_session operation is returned as a JSON response.

    :return: A JSON response containing the result of the save_session operation.
    """
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    session = databases[alias].save_session()
    try:
        fernet_instance = fernet_instance_generation(request.json["password"])
        ciphertext = fernet_instance.encrypt(json.dumps(session).encode())
    except (TypeError, ValueError):
        return {"error": "Failed to Encrypt Session!"}, 400
    return {"ciphertext": ciphertext.decode()}, 200


@app.route("/loadSession", methods=["POST"])
def load_session():
    """
    Loads selected session from file `SESSION_FILE`. 

    This route expects a POST request with a JSON payload containing the alias of the session that is to be 
    restored and the password associated with it. 

    The alias is used in retrieving the encrypted session data from `SESSION_FILE`. If the alias is not found
    an error is returned.

    A Fernet instance, using the user provided password, is instantiated. The session data is decrypted using this
    instance. If an Exception is raised, an error response is returned.

    The `Client` type is retrieved from the session data and a redirect to the correct login with the necessary 
    parameters from the session data is applied. 

    The result of the load_session operation is either returned as a JSON response containing the error message 
    or a redirect.

    :return: A JSON response containing the error of the load_session operation or a redirect.
    """
    alias = request.json["alias"]
    session = request.json["session"]
    try:
        fernet_instance = fernet_instance_generation(request.json["password"])
        ciphertext = json.loads(fernet_instance.decrypt(session))
    except (InvalidSignature, InvalidToken):
        return {"error": "Incorrect Password! Please Try Again!"}, 400
    client_type = ciphertext["client"]
    if client_type == CLIENT_TYPES[0]:
        try:
            databases[alias] = MongoDBClient(
                mongo_uri=ciphertext["uri"],
                database_name=ciphertext["database"],
                collection_name=ciphertext["collection"],
            )
        except Exception as e:
            return {"error": str(e)}, 400

        return redirect(
            url_for("editor", type=CLIENT_TYPES[0], alias=alias),
            302,
        )
    elif client_type == CLIENT_TYPES[1]:
        return redirect(
            url_for("existing_json", filename=ciphertext["filename"]),
            302,
        )
    else:
        return {"error": "Invalid Client Type!"}, 409


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
    return database.check_resource_exists(request.json)


@app.route("/logout", methods=["POST"])
def logout():
    """
    Logs the user out of the application.
    Deletes the alias from the `databases` dictionary.
    :param alias: The alias of the database to logout from.
    :return: A redirect to the index page.
    """
    alias = request.json["alias"]
    if alias not in databases:
        return {"error": "database not found"}, 400
    databases.pop(alias)
    return(redirect(url_for("index")), 302)


if __name__ == "__main__":
    app.run(debug=True)
