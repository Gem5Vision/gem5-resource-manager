from pymongo import MongoClient


class Database:
    def __init__(self, mongo_uri, database_name, collection_name):
        self.mongo_uri = mongo_uri
        self.collection_name = collection_name
        self.database_name = database_name
        self.collection = self.__get_database(
            self.mongo_uri, self.database_name, self.collection_name)

    def __get_database(self, mongo_uri, database_name, collection_name,):
        client = MongoClient(mongo_uri)
        return client[database_name][collection_name]
    def change_collection(self, collection_name):
        self.collection_name = collection_name
        self.collection = self.__get_database(
            self.mongo_uri, self.database_name, self.collection_name)
    def change_database(self, mongo_uri, database_name, collection_name):
        self.mongo_uri = mongo_uri
        self.collection_name = collection_name
        self.database_name = database_name
        self.collection = self.__get_database(
            self.mongo_uri, self.database_name, self.collection_name)
    def get_collection(self):
        return self.collection

    def delete_collection(self):
        self.collection.drop()
