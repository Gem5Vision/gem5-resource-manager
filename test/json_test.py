import flask
import contextlib
import unittest
from server import app
import json
from bson import json_util
import copy

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
        
        with open( "./test/refs/test_json.json" , "r+" ) as f:
            print(f)
            original_json = json.load(f)
            print(original_json)

    def tearDown(self):
        """This method tears down the test environment."""
        self.ctx.pop()

    def test_insert(self):
        print("Testing insert")
        print("Original json: ")
