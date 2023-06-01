#!/usr/bin/env python3
import json
from pymongo import MongoClient
from api.create_resources_json import ResourceJsonCreator
import os
from dotenv import load_dotenv
import argparse
from itertools import cycle
from shutil import get_terminal_size
from threading import Thread
from time import sleep

load_dotenv()
# read MONGO_URI from environment variable

MONGO_URI = os.getenv("MONGO_URI")


class Loader:
    def __init__(self, desc="Loading...", end="Done!", timeout=0.1):
        """
        A loader-like context manager

        Args:
            desc (str, optional): The loader's description. Defaults to "Loading...".
            end (str, optional): Final print. Defaults to "Done!".
            timeout (float, optional): Sleep time between prints. Defaults to 0.1.
        """
        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
        self._thread.start()
        return self

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.end}", flush=True)

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()


def get_database(collection="versions_test", uri=MONGO_URI, db="gem5-vision"):
    """
    Retrieves the MongoDB database for gem5-vision.
    """
    CONNECTION_STRING = uri
    try:
        client = MongoClient(CONNECTION_STRING)
        client.server_info()
    except:
        print("\nCould not connect to MongoDB")
        exit(1)
    return client[db][collection]


collection = None


def cli():
    parser = argparse.ArgumentParser(
        description="CLI for gem5-resources.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-u", "--uri",
        help="The URI of the MongoDB database.",
        type=str,
        default=MONGO_URI
    )
    parser.add_argument(
        "-m", "--mongodb_database",
        help="The MongoDB database to use.",
        type=str,
        default="gem5-vision"
    )
    parser.add_argument(
        "-c", "--collection",
        help="The MongoDB collection to use.",
        type=str,
        default="versions_test"
    )

    subparsers = parser.add_subparsers(
        help="The command to run.",
        dest="command",
        required=True
    )

    parser_get_resource = subparsers.add_parser(
        "get_resource",
        help=(
            f"Retrieves a resource from the collection based on the given ID."
            f"\n if a resource version is provided, it will retrieve the resource with the given ID and version."
        )
    )
    req_group = parser_get_resource.add_argument_group(
        title="required arguments"
    )
    req_group.add_argument(
        "-i",
        "--id",
        help="The ID of the resource to retrieve.",
        type=str,
        required=True
    )
    parser_get_resource.add_argument(
        "-v",
        "--version",
        help="The version of the resource to retrieve.",
        type=str,
        required=False
    )
    parser_get_resource.set_defaults(func=get_resource)

    parser_backup_mongodb = subparsers.add_parser(
        "backup_mongodb",
        help="Backs up the MongoDB collection to a JSON file."
    )
    req_group = parser_backup_mongodb.add_argument_group(
        title="required arguments"
    )
    req_group.add_argument(
        "-f",
        "--file",
        help="The JSON file to back up the MongoDB collection to.",
        type=str,
        required=True
    )
    parser_backup_mongodb.set_defaults(func=backup_mongodb)

    parser_update_mongodb = subparsers.add_parser(
        "restore_backup",
        help="Restores a backup of the MongoDB collection from a JSON file."
    )
    req_group = parser_update_mongodb.add_argument_group(
        title="required arguments")
    req_group.add_argument(
        "-f",
        "--file",
        help="The JSON file to restore the MongoDB collection from.",
        type=str
    )
    parser_update_mongodb.set_defaults(func=restore_backup)

    parser_create_resources_json = subparsers.add_parser(
        "create_resources_json",
        help="Creates a JSON file of all the resources in the collection.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    req_group = parser_create_resources_json.add_argument_group(
        title="required arguments"
    )
    req_group.add_argument(
        "-v",
        "--versions",
        help="The versions of the resources to include in the JSON file. Accepts multiple versions as arguments.",
        nargs=-1,
        required=True
    )
    parser_create_resources_json.add_argument(
        "-o",
        "--output",
        help="The JSON file to create.",
        type=str,
        default="resources.json"
    )
    parser_create_resources_json.add_argument(
        "-d",
        "--debug",
        help="Prints debug information.",
        action="store_true",
        default=False
    )
    parser_create_resources_json.add_argument(
        "-s",
        "--source",
        help="The path to the gem5 source code.",
        type=str,
        default=""
    )
    parser_create_resources_json.set_defaults(func=create_resources_json)

    args = parser.parse_args()
    if args.collection:
        global collection
        with Loader("Connecting to MongoDB...", end="Connected to MongoDB"):
            collection = get_database(
                args.collection,
                args.uri,
                args.mongodb_database
            )
    args.func(args)


def get_resource(args):
    # set the end after the loader is created
    loader = Loader("Retrieving resource...").start()
    resource = None
    if args.version:
        resource = collection.find_one(
            {
                "id": args.id,
                "resource_version": args.version
            },
            {
                "_id": 0
            }
        )
    else:
        resource = collection.find(
            {
                "id": args.id
            },
            {
                "_id": 0
            }
        )
        resource = list(resource)
    if resource:
        loader.end = json.dumps(resource, indent=4)
    else:
        loader.end = "Resource not found"
    
    loader.stop()


def backup_mongodb(args):
    """
    Backs up the MongoDB collection to a JSON file.

    :param file: The JSON file to back up the MongoDB collection to.
    """
    with Loader("Backing up the database...", end="Backed up the database to " + args.file):
        # get all the data from the collection
        resources = collection.find({}, {"_id": 0})
        # write to resources.json
        with open(args.file, "w") as f:
            json.dump(list(resources), f, indent=4)


def restore_backup(args):
    with Loader("Restoring backup...", end="Updated the database\n"):
        with open(args.file) as f:
            resources = json.load(f)
            # clear the collection
            collection.delete_many({})
            # push the new data
            collection.insert_many(resources)


def create_resources_json(args):
    with Loader("Creating resources JSON...", end="Created " + args.output):
        creator = ResourceJsonCreator(list(args.versions), args.debug)
        creator.create_json(args.source, args.output)


if __name__ == "__main__":
    cli()
