import flask
import contextlib
import unittest
from api.json_client import JSONClient
from server import app
import json
from bson import json_util
import copy
import io
from mock import patch
from pathlib import Path
from api.json_client import JSONClient


def get_json():
    with open("test/refs/test_json.json", "r") as f:
        jsonFile = f.read()
        return json.loads(jsonFile)


def mockinit(self, file_path):
    self.file_path = Path("test/refs/") / file_path
    with open(self.file_path, "r") as f:
        self.resources = json.load(f)


class TestJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("./test/refs/resources.json", "rb") as f:
            jsonFile = f.read()
            with open("./test/refs/test_json.json", "wb") as f:
                f.write(jsonFile)

    @classmethod
    def tearDownClass(cls):
        Path("./test/refs/test_json.json").unlink()

    @patch.object(JSONClient, "__init__", mockinit)
    def setUp(self):
        """This method sets up the test environment."""
        with open("./test/refs/test_json.json", "rb") as f:
            jsonFile = f.read()
            self.orignal_json = json.loads(jsonFile)
        self.json_client = JSONClient("test_json.json")

    def tearDown(self):
        """This method tears down the test environment."""
        with open("./test/refs/test_json.json", "w") as f:
            json.dump(self.orignal_json, f, indent=4)

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
        response = self.json_client.insertResource(test_resource)
        self.assertEqual(response, {"status": "Inserted"})
        json_data = get_json()
        self.assertNotEqual(json_data, self.orignal_json)
        self.assertIn(test_resource, json_data)

    def test_insertResource_duplicate(self):
        test_resource = {
            "category": "diskimage",
            "id": "disk-image-example",
            "description": "disk-image documentation.",
            "architecture": "X86",
            "is_zipped": True,
            "md5sum": "90e363abf0ddf22eefa2c7c5c9391c49",
            "url": "http://dist.gem5.org/dist/develop/images/x86/ubuntu-18-04/x86-ubuntu.img.gz",
            "source": "src/x86-ubuntu",
            "root_partition": "1",
            "resource_version": "1.0.0",
            "gem5_versions": ["23.0"],
        }
        response = self.json_client.insertResource(test_resource)
        self.assertEqual(response, {"status": "Resource already exists"})

    def test_find_no_version(self):
        expected_response = {
            "category": "diskimage",
            "id": "disk-image-example",
            "description": "disk-image documentation.",
            "architecture": "X86",
            "is_zipped": True,
            "md5sum": "90e363abf0ddf22eefa2c7c5c9391c49",
            "url": "http://dist.gem5.org/dist/develop/images/x86/ubuntu-18-04/x86-ubuntu.img.gz",
            "source": "src/x86-ubuntu",
            "root_partition": "1",
            "resource_version": "1.0.0",
            "gem5_versions": ["23.0"],
        }
        response = self.json_client.findResource({"id": expected_response["id"]})
        self.assertEqual(response, expected_response)

    def test_find_with_version(self):
        expected_response = {
            "category": "kernel",
            "id": "kernel-example",
            "description": "kernel-example documentation.",
            "architecture": "RISCV",
            "is_zipped": False,
            "md5sum": "60a53c7d47d7057436bf4b9df707a841",
            "url": "http://dist.gem5.org/dist/develop/kernels/x86/static/vmlinux-5.4.49",
            "source": "src/linux-kernel",
            "resource_version": "1.0.0",
            "gem5_versions": ["23.0"],
        }
        response = self.json_client.findResource(
            {
                "id": expected_response["id"],
                "resource_version": expected_response["resource_version"],
            }
        )
        self.assertEqual(response, expected_response)

    def test_find_not_found(self):
        response = self.json_client.findResource({"id": "not-found"})
        self.assertEqual(response, {"exists": False})

    def test_deleteResource(self):
        deleted_resource = {
            "category": "diskimage",
            "id": "disk-image-example",
            "description": "disk-image documentation.",
            "architecture": "X86",
            "is_zipped": True,
            "md5sum": "90e363abf0ddf22eefa2c7c5c9391c49",
            "url": "http://dist.gem5.org/dist/develop/images/x86/ubuntu-18-04/x86-ubuntu.img.gz",
            "source": "src/x86-ubuntu",
            "root_partition": "1",
            "resource_version": "1.0.0",
            "gem5_versions": ["23.0"],
        }
        response = self.json_client.deleteResource(
            {
                "id": deleted_resource["id"],
                "resource_version": deleted_resource["resource_version"],
            }
        )
        self.assertEqual(response, {"status": "Deleted"})
        json_data = get_json()
        self.assertNotEqual(json_data, self.orignal_json)
        self.assertNotIn(deleted_resource, json_data)

    def test_updateResource(self):
        updated_resource = {
            "category": "diskimage",
            "id": "disk-image-example",
            "description": "disk-image documentation.",
            "architecture": "X86",
            "is_zipped": True,
            "md5sum": "90e363abf0ddf22eefa2c7c5c9391c49",
            "url": "http://dist.gem5.org/dist/develop/images/x86/ubuntu-18-04/x86-ubuntu.img.gz",
            "source": "src/x86-ubuntu",
            "root_partition": "1",
            "resource_version": "1.0.0",
            "gem5_versions": ["23.0"],
        }
        response = self.json_client.updateResource(updated_resource)
        self.assertEqual(response, {"status": "Updated"})
        json_data = get_json()
        self.assertNotEqual(json_data, self.orignal_json)
        self.assertIn(updated_resource, json_data)

    def test_getVersions(self):
        resource_id = "kernel-example"
        response = self.json_client.getVersions({"id": resource_id})
        self.assertEqual(
            response, [{"resource_version": "2.0.0"}, {"resource_version": "1.0.0"}]
        )

    def test_checkResourceExists_True(self):
        resource_id = "kernel-example"
        resource_version = "1.0.0"
        response = self.json_client.checkResourceExists(
            {"id": resource_id, "resource_version": resource_version}
        )
        self.assertEqual(response, {"exists": True})

    def test_checkResourceExists_False(self):
        resource_id = "kernel-example"
        resource_version = "3.0.0"
        response = self.json_client.checkResourceExists(
            {"id": resource_id, "resource_version": resource_version}
        )
        self.assertEqual(response, {"exists": False})
