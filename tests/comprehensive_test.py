import flask
import contextlib
import unittest
from server import app, app.config['DATABSE']
import json
from bson import json_util
import copy

class TestComprehensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._collection_name = app.config['DATABSE'].collection_name
        app.config['DATABSE'].change_collection("test_test")

    @classmethod
    def tearDownClass(cls):
        app.config['DATABSE'].delete_collection()
        app.config['DATABSE'].change_collection(cls._collection_name)

    def setUp(self):
        """This method sets up the test environment."""

        self.ctx = app.app_context()
        self.ctx.push()
        self.app = app
        self.test_client = app.test_client()

    def tearDown(self):
        """This method tears down the test environment."""
        self.ctx.pop()

    def test_insert_find_update_find(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": [
                "test-author"
            ],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": [
                "test-tag",
                "test-tag2"
            ],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0"
        }
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": test_resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        # update resource
        test_resource["description"] = "test-description-2"
        test_resource["author"].append("test-author-2")
        response = self.test_client.post("/update", json={"id": test_id, "resource": test_resource})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Updated"})
        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": test_resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

    def test_find_new_insert(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": [
                "test-author"
            ],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": [
                "test-tag",
                "test-tag2"
            ],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0"
        }
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": test_resource_version})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"exists": False})
        # insert resource
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        # delete resource
        app.config['DATABSE'].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})

    def test_insert_find_new_version_find_older(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": [
                "test-author"
            ],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": [
                "test-tag",
                "test-tag2"
            ],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0"
        }
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": test_resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        # add new version
        test_resource_new_version = copy.deepcopy(test_resource)
        test_resource_new_version["description"] = "test-description-2"
        test_resource_new_version["author"].append("test-author-2")
        test_resource_new_version["resource_version"] = "1.0.1"

        response = self.test_client.post("/insert", json=test_resource_new_version)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})

        # get resource versions
        response = self.test_client.post("/versions", json={"id": test_id})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_json, [{'resource_version': '1.0.1'}, {
                         'resource_version': '1.0.0'}])
        
        resource_version = return_json[1]["resource_version"]
        # find older version
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)
        #delete resource
        app.config['DATABSE'].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})
        app.config['DATABSE'].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.1"})
        
    def test_find_add_new_version_delete_older(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": [
                "test-author"
            ],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": [
                "test-tag",
                "test-tag2"
            ],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0"
        }
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        app.config['DATABSE'].get_collection().insert_one(test_resource.copy())
        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": test_resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        # add new version
        test_resource_new_version = copy.deepcopy(test_resource)
        test_resource_new_version["description"] = "test-description-2"
        test_resource_new_version["author"].append("test-author-2")
        test_resource_new_version["resource_version"] = "1.0.1"

        response = self.test_client.post("/insert", json=test_resource_new_version)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})

        # get resource versions
        response = self.test_client.post("/versions", json={"id": test_id})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_json, [{'resource_version': '1.0.1'}, {'resource_version': '1.0.0'}])

        resource_version = return_json[1]["resource_version"]
        # delet older version
        response = self.test_client.post("/delete", json={"id": test_id, "resource_version": resource_version})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Deleted"})

        # get resource versions
        response = self.test_client.post("/versions", json={"id": test_id})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_json, [{'resource_version': '1.0.1'}])
        #delete resource
        app.config['DATABSE'].get_collection().delete_one({"id": test_id, "resource_version": "1.0.1"})

    def test_find_add_new_version_update_older(self):
        test_resource = {
            "category": "diskimage",
            "id": "test-resource",
            "author": [
                "test-author"
            ],
            "description": "test-description",
            "license": "test-license",
            "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
            "tags": [
                "test-tag",
                "test-tag2"
            ],
            "example_usage": " test-usage",
            "gem5_versions": [
                "22.1",
            ],
            "resource_version": "1.0.0"
        }
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        app.config['DATABSE'].get_collection().insert_one(test_resource.copy())
        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": test_resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        # add new version
        test_resource_new_version = copy.deepcopy(test_resource)
        test_resource_new_version["description"] = "test-description-2"
        test_resource_new_version["author"].append("test-author-2")
        test_resource_new_version["resource_version"] = "1.0.1"

        response = self.test_client.post("/insert", json=test_resource_new_version)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})

        # get resource versions
        response = self.test_client.post("/versions", json={"id": test_id})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_json, [{'resource_version': '1.0.1'}, {'resource_version': '1.0.0'}])

        resource_version = return_json[1]["resource_version"]

        # update older version
        test_resource["description"] = "test-description-3"
        test_resource["author"].append("test-author-3")

        response = self.test_client.post("/update", json={"id": test_id, "resource": test_resource})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Updated"})

        # find resource
        response = self.test_client.post("/find", json={"id": test_id, "resource_version": resource_version})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        #delete resource
        app.config['DATABSE'].get_collection().delete_one({"id": test_id, "resource_version": "1.0.1"})
        app.config['DATABSE'].get_collection().delete_one({"id": test_id, "resource_version": "1.0.0"})
