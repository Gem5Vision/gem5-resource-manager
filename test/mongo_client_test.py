import flask
import contextlib
import unittest
from server import app, databases
import json
from bson import json_util
import mongomock
from unittest.mock import patch
from api.mongo_client import MongoDBClient




class TestApi(unittest.TestCase):
    """This is a test class that tests the API."""

    API_URL = "http://127.0.0.1:5000"

    # @classmethod
    # def setUpClass(cls):
    #     cls._collection_name = app.config["DATABASE"].collection_name
    #     app.config["DATABASE"].change_collection("test_test")

    # @classmethod
    # def tearDownClass(cls):
    #     app.config["DATABASE"].delete_collection()
    #     app.config["DATABASE"].change_collection(cls._collection_name)

    @patch.object(
        MongoDBClient,
        "_MongoDBClient__get_database",
        return_value=mongomock.MongoClient().db.collection,
    )
    def setUp(self, mock_get_database):
        """This method sets up the test environment."""
        objects = []
        with open("./test/refs/resources.json", "rb") as f:
            objects = json.loads(f.read(), object_hook=json_util.object_hook)
        self.collection = mock_get_database()
        for obj in objects:
            self.collection.insert_one(obj)
        self.mongo_client = MongoDBClient("mongodb://localhost:27017", "test", "test")
        # print(mongo_client.insertResource({"id": "test"}))
        # print(mongo_client.findResource({"id": "test-kernel"}))

    def tearDown(self):
        """This method tears down the test environment."""
        self.collection.drop()

    def test_insertResource(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        ret_value = self.mongo_client.insert_resource(test_resource)
        self.assertEqual(ret_value, {"status": "Inserted"})
        self.assertEqual(
            self.collection.find({"id": "test-resource"})[0], test_resource
        )
        self.collection.delete_one({"id": "test-resource"})

    def test_insertResource_duplicate(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        self.collection.insert_one(test_resource)
        ret_value = self.mongo_client.insert_resource(test_resource)
        self.assertEqual(ret_value, {"status": "Resource already exists"})

    def test_findResource_no_version(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        self.collection.insert_one(test_resource.copy())
        ret_value = self.mongo_client.find_resource({"id": "test-resource"})
        self.assertEqual(ret_value, test_resource)
        self.collection.delete_one({"id": "test-resource"})

    def test_findResource_with_version(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        self.collection.insert_one(test_resource.copy())
        test_resource["resource_version"] = "2.0.0"
        test_resource["description"] = "test-description2"
        self.collection.insert_one(test_resource.copy())
        ret_value = self.mongo_client.find_resource(
            {"id": "test-resource", "resource_version": "2.0.0"}
        )
        self.assertEqual(ret_value, test_resource)

    def test_findResource_not_found(self):
        ret_value = self.mongo_client.find_resource({"id": "test-resource"})
        self.assertEqual(ret_value, {"exists": False})

    def test_deleteResource(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        self.collection.insert_one(test_resource.copy())
        ret_value = self.mongo_client.delete_resource(
            {"id": "test-resource", "resource_version": "1.0.0"}
        )
        self.assertEqual(ret_value, {"status": "Deleted"})

        self.assertEqual(
            json.loads(json_util.dumps(self.collection.find({"id": "test-resource"}))),
            [],
        )

    def test_updateResource(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        original_resource = test_resource.copy()
        self.collection.insert_one(test_resource.copy())
        test_resource["author"].append("test-author2")
        test_resource["description"] = "test-description2"
        ret_value = self.mongo_client.update_resource({"original_resource": original_resource, "resource": test_resource})
        self.assertEqual(ret_value, {"status": "Updated"})
        self.assertEqual(
            self.collection.find({"id": "test-resource"}, {"_id": 0})[0], test_resource
        )

    def test_checkResourceExists(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        self.collection.insert_one(test_resource.copy())
        ret_value = self.mongo_client.check_resource_exists(
            {"id": "test-resource", "resource_version": "1.0.0"}
        )
        self.assertEqual(ret_value, {"exists": True})

    def test_checkResourceExists_not_found(self):
        ret_value = self.mongo_client.check_resource_exists(
            {"id": "test-resource", "resource_version": "1.0.0"}
        )
        self.assertEqual(ret_value, {"exists": False})

    def test_getVersion(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": ["test-author"],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": ["test-tag", "test-tag2"],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0",
        }
        self.collection.insert_one(test_resource.copy())
        test_resource["resource_version"] = "2.0.0"
        test_resource["description"] = "test-description2"
        self.collection.insert_one(test_resource.copy())
        ret_value = self.mongo_client.get_versions({"id": "test-resource"})
        self.assertEqual(
            ret_value, [{"resource_version": "2.0.0"}, {"resource_version": "1.0.0"}]
        )


# if __name__ == '__main__':
#     unittest.main()
