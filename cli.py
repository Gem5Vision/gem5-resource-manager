import json
import requests
from pymongo import MongoClient
import click
import click_spinner
from api.create_resources_json import ResourceJsonCreator
import os
from dotenv import load_dotenv

load_dotenv()
# read MONGO_URI from environment variable

MONGO_URI = os.getenv("MONGO_URI")


def get_database():
    """
    Retrieves the MongoDB database for gem5-vision.
    """
    CONNECTION_STRING = MONGO_URI
    client = MongoClient(CONNECTION_STRING)
    return client["gem5-vision"]["versions_test"]


collection = get_database()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("id")
def getResource(id):
    """
    Retrieves a resource from the collection based on the given ID.

    :param id: The ID of the resource to retrieve.
    """
    with click_spinner.spinner():
        resource = collection.find_one({"id": id})
        print(resource)


@cli.command()
@click.argument("id")
@click.argument("tags", nargs=-1)
def addTags(id, tags):
    """
    Adds tags to a resource in the collection based on the given ID.

    :param id: The ID of the resource to add tags to.
    :param tags: The tags to add to the resource. Accepts multiple tags as arguments.
    """
    with click_spinner.spinner():
        collection.update_one(
            {"id": id}, {"$push": {"tags": {"$each": list(tags)}}})
        print("Added ", tags, " to ", id)


@cli.command()
@click.argument("id")
@click.argument("tags", nargs=-1)
def removeTags(id, tags):
    """
    Removes tags from a resource in the collection based on the given ID.

    :param id: The ID of the resource to remove tags from.
    :param tags: The tags to remove from the resource. Accepts multiple tags as arguments.
    """
    with click_spinner.spinner():
        collection.update_one(
            {"id": id}, {"$pull": {"tags": {"$in": list(tags)}}})
        print("Removed ", tags, " from ", id)

@cli.command()
@click.argument("file")
def backupMongoDB(file):
    """
    Backs up the MongoDB collection to a JSON file.
    
    :param file: The JSON file to back up the MongoDB collection to.
    """
    with click_spinner.spinner():
        # get all the data from the collection
        resources = collection.find({}, {"_id": 0})
        # write to resources.json
        with open(file, "w") as f:
            json.dump(list(resources), f, indent=4)
            click.echo("Backed up the database to " + file)

@cli.command()
@click.argument("file")
def updateMongoDB(file):
    """
    Updates the MongoDB collection with new data from a JSON file.

    This function reads the data from a JSON file, clears the collection, and inserts the new data into the collection.

    Note: The JSON file should follow the structure expected by the collection.

    :param file: The JSON file to update MongoDB with.
    """
    with click_spinner.spinner():
        # read from resources.json
        with open(file) as f:
            resources = json.load(f)
            # clear the collection
            collection.delete_many({})
            # push the new data
            collection.insert_many(resources)
            click.echo("Updated the database")


@cli.command()
@click.argument("versions", nargs=-1)
@click.option("--output", "-o", default="resources.json")
@click.option("--debug", "-d", is_flag=True)
@click.option("--source", "-s", default="")
def createResourcesJson(versions, output, debug, source):
    """
    Creates a JSON file containing resource information based on the provided versions.

    :param versions: The versions of the resources to include in the JSON file. Accepts multiple versions as arguments.
    :param output: The output file name for the JSON file. By default, it is set to "resources.json".
    :param debug: If specified, enables debug mode for creating the JSON file.
    :param source: The source (as in "source code") for the resources. This string should provide information about the
                   source of the resources. By default, it is an empty string.
    """
    with click_spinner.spinner():
        creator = ResourceJsonCreator(list(versions), debug)
        creator.create_json(source, output)
        click.echo("Created " + output)


if __name__ == "__main__":
    cli()
