import json
import requests
from pymongo import MongoClient
import click
import click_spinner
from create_resources_json import ResourceJsonCreator
import os
from dotenv import load_dotenv

load_dotenv()
# read MONGO_URI from environment variable

MONGO_URI = os.getenv('MONGO_URI')


def get_database():
    CONNECTION_STRING = MONGO_URI
    client = MongoClient(CONNECTION_STRING)
    return client['gem5-vision']['resources_test']


collection = get_database()


@click.group()
def cli():
    pass


@cli.command()
@click.argument('id')
def getResource(id):
    with click_spinner.spinner():
        resource = collection.find_one({'id': id})
        print(resource)


@cli.command()
@click.argument('id')
@click.argument('tags', nargs=-1)
def addTags(id, tags):
    with click_spinner.spinner():
        collection.update_one(
            {'id': id}, {'$push': {'tags': {'$each': list(tags)}}})
        print("Added ", tags, " to ", id)


@cli.command()
@click.argument('id')
@click.argument('tags', nargs=-1)
def removeTags(id, tags):
    with click_spinner.spinner():
        collection.update_one(
            {'id': id}, {'$pull': {'tags': {'$in': list(tags)}}})
        print("Removed ", tags, " from ", id)


@cli.command()
def updateMongoDB():
    with click_spinner.spinner():
        # read from resources.json
        with open('resources.json') as f:
            resources = json.load(f)
            """ res = requests.get(
                'https://raw.githubusercontent.com/Gem5Vision/json-to-mongodb/main/resources.json')
            resources = res.json() """
            # clear the collection
            collection.delete_many({})
            # push the new data
            collection.insert_many(resources)
            click.echo("Updated the database")


@cli.command()
@click.argument('versions', nargs=-1)
@click.option('--output', '-o', default='resources.json')
@click.option('--debug', '-d', is_flag=True)
@click.option('--source', '-s', default='')
def createResourcesJson(versions, output, debug, source):
    with click_spinner.spinner():
        creator = ResourceJsonCreator(list(versions), debug)
        creator.create_json(source, output)
        click.echo("Created " + output)


if __name__ == '__main__':
    cli()
