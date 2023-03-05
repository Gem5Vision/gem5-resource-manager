import requests
from pymongo import MongoClient
import click
import click_spinner
from create_resources_json import ResourceJsonCreator


def get_database():
    CONNECTION_STRING = "mongodb+srv://admin:gem5vision_admin@gem5-vision.wp3weei.mongodb.net/?retryWrites=true&w=majority"
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
        res = requests.get(
            'https://raw.githubusercontent.com/Gem5Vision/json-to-mongodb/main/resources.json')
        resources = res.json()
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
