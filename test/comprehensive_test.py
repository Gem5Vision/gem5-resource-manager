import flask
import contextlib
import unittest
from server import app
import json
from bson import json_util
import copy


class TestComprehensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._collection_name = app.config["DATABASE"].collection_name
        app.config["DATABASE"].change_collection("test_test")

    @classmethod
    def tearDownClass(cls):
        app.config["DATABASE"].delete_collection()
        app.config["DATABASE"].change_collection(cls._collection_name)

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
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": test_resource_version}
        )
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        # update resource
        test_resource["description"] = "test-description-2"
        test_resource["author"].append("test-author-2")
        response = self.test_client.post(
            "/update", json={"id": test_id, "resource": test_resource}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Updated"})
        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": test_resource_version}
        )
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

    def test_find_new_insert(self):
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
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": test_resource_version}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"exists": False})
        # insert resource
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        # delete resource
        app.config["DATABASE"].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"}
        )

    def test_insert_find_new_version_find_older(self):
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
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        response = self.test_client.post("/insert", json=test_resource)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Inserted"})
        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": test_resource_version}
        )
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
        self.assertEqual(
            return_json, [{"resource_version": "1.0.1"}, {"resource_version": "1.0.0"}]
        )

        resource_version = return_json[1]["resource_version"]
        # find older version
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": resource_version}
        )
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)
        # delete resource
        app.config["DATABASE"].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"}
        )
        app.config["DATABASE"].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.1"}
        )

    def test_find_add_new_version_delete_older(self):
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
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        app.config["DATABASE"].get_collection().insert_one(test_resource.copy())
        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": test_resource_version}
        )
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
        self.assertEqual(
            return_json, [{"resource_version": "1.0.1"}, {"resource_version": "1.0.0"}]
        )

        resource_version = return_json[1]["resource_version"]
        # delet older version
        response = self.test_client.post(
            "/delete", json={"id": test_id, "resource_version": resource_version}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Deleted"})

        # get resource versions
        response = self.test_client.post("/versions", json={"id": test_id})
        return_json = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(return_json, [{"resource_version": "1.0.1"}])
        # delete resource
        app.config["DATABASE"].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.1"}
        )

    def test_find_add_new_version_update_older(self):
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
        test_id = test_resource["id"]
        test_resource_version = test_resource["resource_version"]
        # insert resource
        app.config["DATABASE"].get_collection().insert_one(test_resource.copy())
        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": test_resource_version}
        )
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
        self.assertEqual(
            return_json, [{"resource_version": "1.0.1"}, {"resource_version": "1.0.0"}]
        )

        resource_version = return_json[1]["resource_version"]

        # update older version
        test_resource["description"] = "test-description-3"
        test_resource["author"].append("test-author-3")

        response = self.test_client.post(
            "/update", json={"id": test_id, "resource": test_resource}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "Updated"})

        # find resource
        response = self.test_client.post(
            "/find", json={"id": test_id, "resource_version": resource_version}
        )
        self.assertEqual(response.status_code, 200)
        return_json = json.loads(response.data)[0]
        self.assertTrue(return_json == test_resource)

        # delete resource
        app.config["DATABASE"].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.1"}
        )
        app.config["DATABASE"].get_collection().delete_one(
            {"id": test_id, "resource_version": "1.0.0"}
        )
# def test_get_helppage(self):
    #     """This method tests the call to the help page.
    #     It checks if the call is GET, status code is 200 and if the template rendered is help.html.
    #     """
    #     with captured_templates(self.app) as templates:
    #         response = self.test_client.get("/help")
    #         self.assertEqual(response.status_code, 200)
    #         self.assertTrue(templates[0][0].name == "help.html")

    # def test_get_mongodb_loginpage(self):
    #     """This method tests the call to the MongoDB login page.
    #     It checks if the call is GET, status code is 200 and if the template rendered is mongoDBLogin.html.
    #     """
    #     with captured_templates(self.app) as templates:
    #         response = self.test_client.get("/login/mongodb")
    #         self.assertEqual(response.status_code, 200)
    #         self.assertTrue(templates[0][0].name == "mongoDBLogin.html")

    # def test_get_json_loginpage(self):
    #     """This method tests the call to the JSON login page.
    #     It checks if the call is GET, status code is 200 and if the template rendered is jsonLogin.html.
    #     """
    #     with captured_templates(self.app) as templates:
    #         response = self.test_client.get("/login/json")
    #         self.assertEqual(response.status_code, 200)
    #         self.assertTrue(templates[0][0].name == "jsonLogin.html")

    # def test_get_editorpage_withoutparameters(self):
    #     """This method tests the call to the editor page without required query parameters.
    #     It checks if the call is GET, status code is 404 and if the template rendered is 404.html.
    #     """
    #     with captured_templates(self.app) as templates:
    #         response = self.test_client.get("/editor")
    #         self.assertEqual(response.status_code, 404)
    #         self.assertTrue(templates[0][0].name == "404.html")

    # def test_default_call_is_not_post(self):
    #     """This method tests that the default call is not a POST."""

    #     response = self.test_client.post("/")
    #     self.assertEqual(response.status_code, 405)

    # def test_get_categories(self):
    #     """The methods tests if the category call returns the same categories as the schema."""

    #     response = self.test_client.get("/categories")
    #     post_response = self.test_client.post("/categories")
    #     categories = [
    #         "workload",
    #         "diskimage",
    #         "binary",
    #         "kernel",
    #         "benchmark",
    #         "checkpoint",
    #         "git",
    #         "bootloader",
    #         "file",
    #         "directory",
    #         "simpoint",
    #         "simpoint-directory",
    #         "resource",
    #         "looppoint-pinpoint-csv",
    #         "looppoint-json",
    #     ]
    #     self.assertEqual(post_response.status_code, 405)
    #     self.assertEqual(response.status_code, 200)
    #     returnedData = json.loads(response.data)
    #     self.assertTrue(returnedData == categories)

    # def test_get_schema(self):
    #     """The methods tests if the schema call returns the same schema as the schema file."""

    #     response = self.test_client.get("/schema")
    #     post_response = self.test_client.post("/schema")
    #     self.assertEqual(post_response.status_code, 405)
    #     self.assertEqual(response.status_code, 200)
    #     returnedData = json.loads(response.data)
    #     schema = {}
    #     with open("schema/schema.json", "r") as f:
    #         schema = json.load(f)
    #     self.assertTrue(returnedData == schema)

    # def test_insert(self):
    #     """This method tests the insert method of the API."""
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     response = self.test_client.post("/insert", json=test_resource)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"status": "Inserted"})
    #     resource = (
    #         app.config["DATABASE"]
    #         .get_collection()
    #         .find({"id": "test-resource"}, {"_id": 0})
    #     )
    #     json_resource = json.loads(json_util.dumps(resource[0]))
    #     self.assertTrue(json_resource == test_resource)
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": "test-resource", "resource_version": "1.0.0"}
    #     )

    # def test_find_no_version(self):
    #     """This method tests the find method of the API."""
    #     test_id = "test-resource"
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     response = self.test_client.post(
    #         "/find", json={"id": test_id, "resource_version": ""}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     return_json = json.loads(response.data)[0]
    #     self.assertTrue(return_json == test_resource)
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.0"}
    #     )

    # def test_find_not_exist(self):
    #     """This method tests the find method of the API."""
    #     test_id = "test-resource"
    #     response = self.test_client.post(
    #         "/find", json={"id": test_id, "resource_version": ""}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue(response.json == {"exists": False})

    # def test_find_with_version(self):
    #     """This method tests the find method of the API."""
    #     test_id = "test-resource"
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     test_resource["resource_version"] = "1.0.1"
    #     test_resource["description"] = "test-description2"
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     response = self.test_client.post(
    #         "/find", json={"id": test_id, "resource_version": "1.0.1"}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     return_json = json.loads(response.data)[0]
    #     self.assertTrue(return_json["description"] == "test-description2")
    #     self.assertTrue(return_json["resource_version"] == "1.0.1")
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.0"}
    #     )
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.1"}
    #     )

    # def test_delete(self):
    #     """This method tests the delete method of the API."""
    #     test_id = "test-resource"
    #     test_version = "1.0.0"
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     response = self.test_client.post(
    #         "/delete", json={"id": test_id, "resource_version": test_version}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"status": "Deleted"})
    #     resource = (
    #         app.config["DATABASE"]
    #         .get_collection()
    #         .find({"id": "test-resource"}, {"_id": 0})
    #     )
    #     json_resource = json.loads(json_util.dumps(resource))
    #     self.assertTrue(json_resource == [])

    # def test_if_resource_exists_true(self):
    #     """This method tests the checkExists method of the API."""
    #     test_id = "test-resource"
    #     test_version = "1.0.0"
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     response = self.test_client.post(
    #         "/checkExists", json={"id": test_id, "resource_version": test_version}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"exists": True})
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.0"}
    #     )

    # def test_if_resource_exists_false(self):
    #     """This method tests the checkExists method of the API."""
    #     test_id = "test-resource"
    #     test_version = "1.0.0"
    #     response = self.test_client.post(
    #         "/checkExists", json={"id": test_id, "resource_version": test_version}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"exists": False})

    # def test_get_resource_versions(self):
    #     """This method tests the getResourceVersions method of the API."""
    #     test_id = "test-resource"
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     test_resource["resource_version"] = "1.0.1"
    #     test_resource["description"] = "test-description2"
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     response = self.test_client.post("/versions", json={"id": test_id})
    #     return_json = json.loads(response.data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(
    #         return_json, [{"resource_version": "1.0.1"},
    #                       {"resource_version": "1.0.0"}]
    #     )
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.0"}
    #     )
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.1"}
    #     )

    # def test_update_resource(self):
    #     """This method tests the updateResource method of the API."""
    #     test_id = "test-resource"
    #     test_resource = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": ["test-author"],
    #         "description": "test-description",
    #         "license": "test-license",
    #         "source_url": "https://github.com/gem5/gem5-resources/tree/develop/src/x86-ubuntu",
    #         "tags": ["test-tag", "test-tag2"],
    #         "example_usage": " test-usage",
    #         "gem5_versions": [
    #             "22.1",
    #         ],
    #         "resource_version": "1.0.0",
    #     }
    #     app.config["DATABASE"].get_collection(
    #     ).insert_one(test_resource.copy())
    #     test_resource["description"] = "test-description2"
    #     test_resource["example_usage"] = "test-usage2"
    #     response = self.test_client.post(
    #         "/update", json={"id": test_id, "resource": test_resource}
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.json, {"status": "Updated"})
    #     resource = (
    #         app.config["DATABASE"]
    #         .get_collection()
    #         .find({"id": "test-resource"}, {"_id": 0})
    #     )
    #     json_resource = json.loads(json_util.dumps(resource))
    #     self.assertTrue(json_resource == [test_resource])
    #     app.config["DATABASE"].get_collection().delete_one(
    #         {"id": test_id, "resource_version": "1.0.0"}
    #     )

    # def test_keys_1(self):
    #     """This method tests the keys method of the API."""
    #     response = self.test_client.post(
    #         "/keys", json={"category": "simpoint", "id": "test-resource"}
    #     )
    #     test_response = {
    #         "category": "simpoint",
    #         "id": "test-resource",
    #         "author": [],
    #         "description": "",
    #         "license": "",
    #         "source_url": "",
    #         "tags": [],
    #         "example_usage": "",
    #         "gem5_versions": [],
    #         "resource_version": "",
    #         "simpoint_interval": 0,
    #         "simpoint_list": [],
    #         "weight_list": [],
    #         "warmup_interval": 0,
    #     }
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(json.loads(response.data), test_response)

    # def test_keys_2(self):
    #     """This method tests the keys method of the API."""
    #     response = self.test_client.post(
    #         "/keys", json={"category": "diskimage", "id": "test-resource"}
    #     )
    #     test_response = {
    #         "category": "diskimage",
    #         "id": "test-resource",
    #         "author": [],
    #         "description": "",
    #         "license": "",
    #         "source_url": "",
    #         "tags": [],
    #         "example_usage": "",
    #         "gem5_versions": [],
    #         "resource_version": "",
    #     }
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(json.loads(response.data), test_response)
