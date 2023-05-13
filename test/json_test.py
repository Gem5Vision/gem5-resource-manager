import flask
import contextlib
import unittest
from server import app
import json
from bson import json_util
import copy
import io
from mock import patch
from pathlib import Path


def get_json():
    with open("./database/test.json", "rb") as f:
        jsonFile = f.read()
        return json.loads(jsonFile)


@patch('server.isMongo', False)
class TestJson(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls):
    #     cls._collection_name = app.config["DATABASE"].collection_name
    #     app.config["DATABASE"].change_collection("test_test")

    # @classmethod
    # def tearDownClass(cls):
    #     app.config["DATABASE"].delete_collection()
    #     app.config["DATABASE"].change_collection(cls._collection_name)
    def setUp(self):
        """This method sets up the test environment."""
        self.ctx = app.app_context()
        self.ctx.push()
        self.app = app
        self.test_client = app.test_client()
        # delete database/test.json
        file_to_delete = Path("database/test.json")
        if file_to_delete.is_file():
            file_to_delete.unlink()
        with open("./test/refs/test_json.json", "rb") as f:
            jsonFile = f.read()
            data = dict(
                file=(io.BytesIO(jsonFile), "test.json"),)
            self.test_client.post(
                "/validateJSON", content_type='multipart/form-data', data=data)
            self.orignal_json = get_json()

    def tearDown(self):
        """This method tears down the test environment."""
        file_to_delete = Path("database/test.json")
        if file_to_delete.is_file():
            file_to_delete.unlink()
        self.ctx.pop()

    def test_insert(self):
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
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        json_data = get_json()
        self.assertNotEqual(json_data, self.orignal_json)
        self.assertIn(test_resource, json_data)

    def test_find_no_version(self):
        response = self.test_client.post("/find",json={"id":"test-kernel", "resource_version": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data)[0], self.orignal_json[0])
