import flask
import contextlib
import requests
import unittest
from server import app
import json


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


if __name__ == '__main__':
    unittest.main()
