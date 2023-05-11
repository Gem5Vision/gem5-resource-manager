# gem5 Resources Manager

This repository contains the code to convert the JSON file to a MongoDB database. This also contains tools to manage the database as well as the JSON file.
# Table of Contents
- [gem5 Resources Manager](#gem5-resources-manager)
- [Table of Contents](#table-of-contents)
- [Resources Manager](#resources-manager)
  - [Setup](#setup)
  - [Selecting a database](#selecting-a-database)
    - [MongoDB](#mongodb)
    - [JSON File](#json-file)
  - [Adding a Resource](#adding-a-resource)
  - [Updating a Resource](#updating-a-resource)
  - [Deleting a Resource](#deleting-a-resource)
  - [Adding a New Version](#adding-a-new-version)
  - [Validation](#validation)
- [CLI tool](#cli-tool)
  - [createresourcesjson](#createresourcesjson)
  - [updatemongodb](#updatemongodb)
- [Changes to Structure of JSON](#changes-to-structure-of-json)

# Resources Manager

This is a tool to manage the resources JSON file and the MongoDB database. This tool is used to add, delete, update, view, and search for resources.

## Setup

First, install the requirements:

```bash
pip3 install -r requirements.txt
```

Then run the flask server:

```bash
python3 app.py
```

Then, you can access the server at `http://localhost:5000`.

## Selecting a database

The Resource Manager currently supports 2 database options: MongoDB and JSON file.

Select the database you want to use by clicking on the button on home page.

### MongoDB

The MongoDB database is hosted on MongoDB Atlas. To use this database, you need to have the MongoDB URI, collection name, and database name.  Once you have the information, enter it into the form and click "login" or "save and login" to login to the database.

Another way to use the MongoDB database is to switch to the Generate URI tab and enter the information there. This would generate a URI that you can use to login to the database.

### JSON File

There are currently 3 ways to use the JSON file:

1. Adding a URL to the JSON file
2. Uploading a JSON file
3. Using an existing JSON file

## Adding a Resource

Once you are logged in, you can use the search bar to search for resources. If the ID doesn't exist, it would be prefilled with the required fields. You can then edit the fields and click "add" to add the resource to the database.

## Updating a Resource

If the ID exists, the form would be prefilled with the existing data. You can then edit the fields and click "update" to update the resource in the database.

## Deleting a Resource

If the ID exists, the form would be prefilled with the existing data. You can then click "delete" to delete the resource from the database.

## Adding a New Version

If the ID exists, the form would be prefilled with the existing data. Change the `resource_version` field to the new version and click "add" to add the new version to the database. You will only be able to add a new version if the `resource_version` field is different from any of the existing versions.

## Validation

The Resource Manager validates the data before adding it to the database. If the data is invalid, it would show an error message and not add the data to the database. The validation is done using the [schema](schema/schema.json) file. The Monaco editor automatically validates the data as you type and displays the errors in the editor.

To view the schema, click on the "Show Schema" button on the left side of the page.
# CLI tool

```bash
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  addtags
  createresourcesjson
  getresource
  removetags
  updatemongodb
```

## createresourcesjson

This command is used to create a new JSON file from the old JSON file. This is used to make the JSON file "parseable" by removing the nested JSON and adding the new fields.

```bash
Usage: cli.py createresourcesjson [OPTIONS] [VERSIONS]...

Options:
  -o, --output TEXT
  -d, --debug
  -s, --source TEXT
  --helpShow this message and exit.
```

A sample command to run this is:

```bash
python3 cli.py createresourcesjson -o resources_new.json -s ./gem5
```

## updatemongodb

This command is used to update the MongoDB database with the new JSON file. This is used to update the database with the new JSON file.

```bash
Usage: cli.py updatemongodb [OPTIONS] FILE

  Updates the MongoDB collection with new data from a JSON file.

  This function reads the data from a JSON file, clears the collection, and
  inserts the new data into the collection.

  Note: The JSON file should follow the structure expected by the collection.

Options:
  --help  Show this message and exit.
```
# Changes to Structure of JSON

To view the new schema, see [schema.json](schema/schema.json).
