import flask
import contextlib
import unittest
from server import app, database
import json
from bson import json_util


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


class TestApi(unittest.TestCase):
    """This is a test class that tests the API."""
    API_URL = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        cls._collection_name = database.collection_name
        database.change_collection("test_test")

    @classmethod
    def tearDownClass(cls):
        database.delete_collection()
        database.change_collection(cls._collection_name)

    def setUp(self):
        """This method sets up the test environment."""

        self.ctx = app.app_context()
        self.ctx.push()
        self.app = app
        self.test_client = app.test_client()

    def tearDown(self):
        """This method tears down the test environment."""
        self.ctx.pop()

    def test_get_homepage(self):
        """This method tests the default call.
    It checks if the default call is GET, status code is 200 and if the template rendered is index.html."""
        with captured_templates(self.app) as templates:
            response = self.test_client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(templates[0][0].name == 'index.html')

    def test_default_call_is_not_post(self):
        """This method tests that the default call is not a POST."""

        response = self.test_client.post('/')
        self.assertEqual(response.status_code, 405)

    def test_get_categories(self):
        """The methods tests if the category call returns the same categories as the schema."""

        response = self.test_client.get('/categories')
        post_response = self.test_client.post('/categories')
        categories = [
            "workload",
            "diskimage",
            "binary",
            "kernel",
            "benchmark",
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

        response = self.test_client.get('/schema')
        post_response = self.test_client.post('/schema')
        self.assertEqual(post_response.status_code, 405)
        self.assertEqual(response.status_code, 200)
        returnedData = json.loads(response.data)
        schema = {}
        with open("schema/test.json", "r") as f:
            schema = json.load(f)
        self.assertTrue(returnedData == schema)

    def test_insert(self):
        """This method tests the insert method of the API."""
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
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        resource = database.get_collection().find(
            {"id": "test-resource"}, {"_id": 0})
        json_resource = json.loads(json_util.dumps(resource[0]))
        self.assertTrue(json_resource == test_resource)
        database.get_collection().delete_one(
            {"id": "test-resource", "resource_version": "1.0.0"})

    def test_find_no_version(self):
        """This method tests the find method of the API."""
        test_id = "test-resource"
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
        database.get_collection().insert_one(test_resource.copy())
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": ""})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})

    def test_find_not_exist(self):
        """This method tests the find method of the API."""
        test_id = "test-resource"
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json == {"exists": False})

    def test_find_with_version(self):
        """This method tests the find method of the API."""
        test_id = "test-resource"
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
        database.get_collection().insert_one(test_resource.copy())
        test_resource["resource_version"] = "1.0.1"
        test_resource["description"] = "test-description2"
        database.get_collection().insert_one(test_resource.copy())
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": "1.0.1"})
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json["description"] == "test-description2")
        self.assertTrue(return_json["resource_version"] == "1.0.1")
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.1"})

    def test_delete(self):
        """This method tests the delete method of the API."""
        test_id = "test-resource"
        test_version = "1.0.0"
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
        database.get_collection().insert_one(test_resource.copy())
        response = self.test_client.post("/delete", json={
            "id": test_id, "resource_version": test_version})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Deleted"})
        resource = database.get_collection().find(
            {"id": "test-resource"}, {"_id": 0})
        json_resource = json.loads(json_util.dumps(resource))
        self.assertTrue(json_resource == [])

    def test_if_resource_exists_true(self):
        """This method tests the checkExists method of the API."""
        test_id = "test-resource"
        test_version = "1.0.0"
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
        database.get_collection().insert_one(test_resource.copy())
        response = self.test_client.post(
            "/checkExists", json={"id": test_id, "resource_version": test_version})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"exists": True})
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})

    def test_if_resource_exists_false(self):
        """This method tests the checkExists method of the API."""
        test_id = "test-resource"
        test_version = "1.0.0"
        response = self.test_client.post(
            "/checkExists", json={"id": test_id, "resource_version": test_version})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"exists": False})

    def test_get_resource_versions(self):
        """This method tests the getResourceVersions method of the API."""
        test_id = "test-resource"
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
        database.get_collection().insert_one(test_resource.copy())
        test_resource["resource_version"] = "1.0.1"
        test_resource["description"] = "test-description2"
        database.get_collection().insert_one(test_resource.copy())
        response = self.test_client.post("/versions", json={"id": test_id})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_json, [{'resource_version': '1.0.1'}, {
                         'resource_version': '1.0.0'}])
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.1"})

    def test_update_resource(self):
        """This method tests the updateResource method of the API."""
        test_id = "test-resource"
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
        database.get_collection().insert_one(test_resource.copy())
        test_resource["description"] = "test-description2"
        test_resource["example_usage"] = "test-usage2"
        response = self.test_client.post(
            "/update", json={"id": test_id, "resource": test_resource})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Updated"})
        resource = database.get_collection().find(
            {"id": "test-resource"}, {"_id": 0})
        json_resource = json.loads(json_util.dumps(resource))
        self.assertTrue(json_resource == [test_resource])
        database.get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"})

    def test_keys_1(self):
        """This method tests the keys method of the API."""
        response = self.test_client.post(
            "/keys", json={"category": "simpoint", "id": "test-resource"})
        test_response = {"category": "simpoint", "id": "test-resource", "author": [], "description": "", "license": "", "source_url": "", "tags": [],
                         "example_usage": "", "gem5_versions": [], "resource_version": "", "simpoint_interval": 0, "simpoint_list": [], "weight_list": [], "warmup_interval": 0}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), test_response)

    def test_keys_2(self):
        """This method tests the keys method of the API."""
        response = self.test_client.post(
            "/keys", json={"category": "diskimage", "id": "test-resource"})
        test_response = {"category": "diskimage",
                         "id": "test-resource",
                         "author": [],
                         "description": "",
                         "license": "",
                         "source_url": "",
                         "tags": [],
                         "example_usage": "",
                         "gem5_versions": [],
                         "resource_version": ""}
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), test_response)


# if __name__ == '__main__':
#     unittest.main()
