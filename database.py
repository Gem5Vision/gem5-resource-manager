from pymongo import MongoClient
from dotenv import load_dotenv
import os


class Database:
    def __init__(self,  database_name, collection_name):
        load_dotenv()
        self.MONGO_URI = os.getenv("MONGO_URI")
        self.collection_name = collection_name
        self.database_name = database_name
        self.collection = self.__get_database(
            self.database_name, self.collection_name)

    def __get_database(self, database_name, collection_name,):
        client = MongoClient(self.MONGO_URI)
        return client[database_name][collection_name]
    def change_collection(self, collection_name):
        self.collection_name = collection_name
        self.collection = self.__get_database(
            self.database_name, self.collection_name)
    def get_collection(self):
        return self.collection

    def delete_collection(self):
        self.collection.drop()
