import flask
import contextlib
import unittest
from server import app
import server
import json
from bson import json_util
import copy
from unittest.mock import patch
import mongomock
from api.mongo_client import MongoDBClient

@contextlib.contextmanager
def captured_templates(app):
    """This is a context manager that allows you to capture the templates that are rendered during a test."""
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    flask.template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        flask.template_rendered.disconnect(record, app)

class TestAPI(unittest.TestCase):
    @patch.object(
        MongoDBClient,
        "_MongoDBClient__get_database",
        return_value=mongomock.MongoClient().db.collection,
    )
    def setUp(self, mock_get_database):
        """This method sets up the test environment."""
        self.ctx = app.app_context()
        self.ctx.push()
        self.app = app
        self.test_client = app.test_client()
        self.alias = "test"
        objects = []
        with open("./test/refs/resources.json", "rb") as f:
            objects = json.loads(f.read(), object_hook=json_util.object_hook)
        self.collection = mock_get_database()
        for obj in objects:
            self.collection.insert_one(obj)
        # self.mongo_client = MongoDBClient("mongodb://localhost:27017", "test", "test")

        self.test_client.post("/validateMongoDB", json={
            "uri": "mongodb://localhost:27017",
            "database": "test",
            "collection": "test",
            "alias": self.alias
        })
        # server.databases["test"] = self.mongo_client
        # print(mongo_client.insertResource({"id": "test"}))
        # print(mongo_client.findResource({"id": "test-kernel"}))

    def tearDown(self):
        """This method tears down the test environment."""
        self.collection.drop()
        self.ctx.pop()


    
    def test_get_helppage(self):
        """This method tests the call to the help page.
        It checks if the call is GET, status code is 200 and if the template rendered is help.html.
        """
        with captured_templates(self.app) as templates:
            response = self.test_client.get("/help")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(templates[0][0].name == "help.html")

    def test_get_mongodb_loginpage(self):
        """This method tests the call to the MongoDB login page.
        It checks if the call is GET, status code is 200 and if the template rendered is mongoDBLogin.html.
        """
        with captured_templates(self.app) as templates:
            response = self.test_client.get("/login/mongodb")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(templates[0][0].name == "login/login_mongodb.html")

    def test_get_json_loginpage(self):
        """This method tests the call to the JSON login page.
        It checks if the call is GET, status code is 200 and if the template rendered is jsonLogin.html.
        """
        with captured_templates(self.app) as templates:
            response = self.test_client.get("/login/json")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(templates[0][0].name == "login/login_json.html")

    def test_get_editorpage_withoutparameters(self):
        """This method tests the call to the editor page without required query parameters.
        It checks if the call is GET, status code is 404 and if the template rendered is 404.html.
        """
        with captured_templates(self.app) as templates:
            response = self.test_client.get("/editor")
            self.assertEqual(response.status_code, 404)
            self.assertTrue(templates[0][0].name == "404.html")

    def test_default_call_is_not_post(self):
        """This method tests that the default call is not a POST."""

        response = self.test_client.post("/")
        self.assertEqual(response.status_code, 405)

    def test_get_categories(self):
        """The methods tests if the category call returns the same categories as the schema."""

        response = self.test_client.get("/categories")
        post_response = self.test_client.post("/categories")
        categories = [
            "workload",
            "disk-image",
            "binary",
            "kernel",
            "checkpoint",
            "git",
            "bootloader",
            "file",
            "directory",
            "simpoint",
            "simpoint-directory",
            "resource",
            "looppoint-pinpoint-csv",
            "looppoint-json",
        ]
        self.assertEqual(post_response.status_code, 405)
        self.assertEqual(response.status_code, 200)
        returnedData = json.loads(response.data)
        self.assertTrue(returnedData == categories)

    def test_get_schema(self):
        """The methods tests if the schema call returns the same schema as the schema file."""

        response = self.test_client.get("/schema")
        post_response = self.test_client.post("/schema")
        self.assertEqual(post_response.status_code, 405)
        self.assertEqual(response.status_code, 200)
        returnedData = json.loads(response.data)
        schema = {}
        with open("./test/refs/schema.json", "r") as f:
            schema = json.load(f)
        self.assertTrue(returnedData == schema)

    def test_insert(self):
        """This method tests the insert method of the API."""
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
        response = self.test_client.post("/insert", json={"resource": test_resource, "alias": self.alias})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        resource = self.collection.find({"id": "test-resource"}, {"_id": 0})

        json_resource = json.loads(json_util.dumps(resource[0]))
        self.assertTrue(json_resource == test_resource)

    def test_find_no_version(self):
        """This method tests the find method of the API."""
        test_id = "test-resource"
        test_resource_version = "1.0.0"
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
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": "", "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json == test_resource)

    def test_find_not_exist(self):
        """This method tests the find method of the API."""
        test_id = "test-resource"
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": "", "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json == {"exists": False})

    def test_find_with_version(self):
        """This method tests the find method of the API."""
        test_id = "test-resource"
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
        test_resource["resource_version"] = "1.0.1"
        test_resource["description"] = "test-description2"
        self.collection.insert_one(test_resource.copy())
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": "1.0.1", "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        return_json = response.json
        self.assertTrue(return_json["description"] == "test-description2")
        self.assertTrue(return_json["resource_version"] == "1.0.1")
        self.assertTrue(return_json==test_resource)

    def test_delete(self):
        """This method tests the delete method of the API."""
        test_id = "test-resource"
        test_version = "1.0.0"
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
        response = self.test_client.post(
            "/delete", json={"resource": test_resource, "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Deleted"})
        resource = self.collection.find({"id": "test-resource"}, {"_id": 0})
        json_resource = json.loads(json_util.dumps(resource))
        self.assertTrue(json_resource == [])

    def test_if_resource_exists_true(self):
        """This method tests the checkExists method of the API."""
        test_id = "test-resource"
        test_version = "1.0.0"
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
        response = self.test_client.post(
            "/checkExists", json={"id": test_id, "resource_version": test_version, "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"exists": True})

    def test_if_resource_exists_false(self):
        """This method tests the checkExists method of the API."""
        test_id = "test-resource"
        test_version = "1.0.0"
        response = self.test_client.post(
            "/checkExists", json={"id": test_id, "resource_version": test_version, "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"exists": False})

    def test_get_resource_versions(self):
        """This method tests the getResourceVersions method of the API."""
        test_id = "test-resource"
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
        test_resource["resource_version"] = "1.0.1"
        test_resource["description"] = "test-description2"
        self.collection.insert_one(test_resource.copy())
        response = self.test_client.post("/versions", json={"id": test_id, "alias": self.alias})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            return_json, [{"resource_version": "1.0.1"},
                        {"resource_version": "1.0.0"}]
        )

    def test_update_resource(self):
        """This method tests the updateResource method of the API."""
        test_id = "test-resource"
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
        test_resource["description"] = "test-description2"
        test_resource["example_usage"] = "test-usage2"
        response = self.test_client.post(
            "/update", json={"original_resource": original_resource, "resource": test_resource, "alias": self.alias}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Updated"})
        resource = self.collection.find({"id": test_id}, {"_id": 0})
        json_resource = json.loads(json_util.dumps(resource))
        self.assertTrue(json_resource == [test_resource])
        self.collection.delete_one(
            {"id": test_id, "resource_version": "1.0.0"}
        )

    def test_keys_1(self):
        """This method tests the keys method of the API."""
        response = self.test_client.post(
            "/keys", json={"category": "simpoint", "id": "test-resource"}
        )
        test_response = {
            "category": "simpoint",
            "id": "test-resource",
            "author": [],
            "description": "",
            "license": "",
            "source_url": "",
            "tags": [],
            "example_usage": "",
            "gem5_versions": [],
            "resource_version": "1.0.0",
            "simpoint_interval": 0,
            "warmup_interval": 0,
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), test_response)

    def test_keys_2(self):
        """This method tests the keys method of the API."""
        response = self.test_client.post(
            "/keys", json={"category": "disk-image", "id": "test-resource"}
        )
        test_response = {
            "category": "disk-image",
            "id": "test-resource",
            "author": [],
            "description": "",
            "license": "",
            "source_url": "",
            "tags": [],
            "example_usage": "",
            "gem5_versions": [],
            "resource_version": "1.0.0",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), test_response)
