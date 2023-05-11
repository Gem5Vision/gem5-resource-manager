from pymongo import MongoClient


class Database:
    """
    The `Database` class is used to create a connection to a MongoDB database collection. It has several methods to modify the connection and access the collection.

    - `__get_database(mongo_uri, database_name, collection_name)` - Private method that returns a MongoDB database object for the specified collection.
    It takes three arguments: `mongo_uri`, `database_name`, and `collection_name`.
    - `change_collection(collection_name)` - Method that changes the collection to be accessed by the database object.
    It takes one argument: `collection_name`.
    - `change_database(mongo_uri, database_name, collection_name)` - Method that changes the database and collection associated with the `Database` object.
    It takes three arguments: `mongo_uri`, `database_name`, and `collection_name`.
    - `get_collection()` - Method that returns the collection object associated with the database.
    - `delete_collection()` - Method that deletes the entire collection in the database.
    Note that this method permanently removes all documents in the collection, so use it with caution.
    """

    def __init__(self, mongo_uri, database_name, collection_name):
        self.mongo_uri = mongo_uri
        self.collection_name = collection_name
        self.database_name = database_name
        self.collection = self.__get_database(
            self.mongo_uri, self.database_name, self.collection_name
        )

    def __get_database(
        self,
        mongo_uri,
        database_name,
        collection_name,
    ):
        """
        This function returns a MongoDB database object for the specified collection.
        It takes three arguments: 'mongo_uri', 'database_name', and 'collection_name'.

        :param: mongo_uri: URI of the MongoDB instance
        :param: database_name: Name of the database
        :param: collection_name: Name of the collection
        :return: database: MongoDB database object
        """

        client = MongoClient(mongo_uri)
        return client[database_name][collection_name]

    def change_collection(self, collection_name):
        """
        This function changes the collection to be accessed by the database object by updating the 'collection_name' attribute of the object and
        calling the '__get_database' method to update the 'collection' attribute with the new collection.

        :param: collection_name: name of the new collection
        :return: None
        """
        self.collection_name = collection_name
        self.collection = self.__get_database(
            self.mongo_uri, self.database_name, self.collection_name
        )

    def change_database(self, mongo_uri, database_name, collection_name):
        """
        This method changes the database and collection associated with the Database object.

        :param: mongo_uri: The MongoDB connection URI.
        :param: database_name: The name of the new database.
        :param: collection_name: The name of the new collection.
        :return: None
        """
        self.mongo_uri = mongo_uri
        self.collection_name = collection_name
        self.database_name = database_name
        self.collection = self.__get_database(
            self.mongo_uri, self.database_name, self.collection_name
        )

    def get_collection(self):
        """
        This method returns the collection object associated with the database.

        :return: collection: The collection object representing the database collection.
        """
        return self.collection

    def delete_collection(self):
        """
        This method deletes the entire collection in the database.

        Note: Be cautious when using this method as it permanently removes all documents in the collection.
        """
        self.collection.drop()
