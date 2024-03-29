from bson import json_util
from pathlib import Path
import json
import requests
from api.client import Client
from werkzeug.utils import secure_filename
from typing import Dict, List


class JSONClient(Client):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = Path("database/") / file_path
        self.resources = self.__get_resources(self.file_path)

    def __get_resources(self, path: Path) -> List[Dict]:
        """
        Retrieves the resources from the JSON file.
        :param path: The path to the JSON file.
        :return: The resources as a JSON string.
        """
        with open(path) as f:
            return json.load(f)

    def find_resource(self, query: Dict) -> Dict:
        """
        Finds a resource within a list of resources based on the provided query.
        :param query: The query object containing the search criteria.
        :return: The resource that matches the query.        
        """
        found_resources = []
        for resource in self.resources:
            if (
                "resource_version" not in query
                or query["resource_version"] == ""
                or query["resource_version"] == "Latest"
            ):
                if resource["id"] == query["id"]:
                    found_resources.append(resource)
            else:
                if (
                    resource["id"] == query["id"]
                    and resource["resource_version"] == query["resource_version"]
                ):
                    return resource
        if not found_resources:
            return {"exists": False}
        return max(
            found_resources,
            key=lambda resource: tuple(
                map(int, resource["resource_version"].split("."))
            ),
        )

    def get_versions(self, query: Dict) -> List[Dict]:
        """
        Retrieves all versions of a resource with the given ID from the list of resources.
        :param query: The query object containing the search criteria.
        :return: A list of all versions of the resource.
        """
        versions = []
        for resource in self.resources:
            if resource["id"] == query["id"]:
                versions.append(
                    {"resource_version": resource["resource_version"]})
        versions.sort(
            key=lambda resource: tuple(
                map(int, resource["resource_version"].split("."))
            ),
            reverse=True,
        )
        return versions

    def update_resource(self, query: Dict) -> Dict:
        """
        Updates a resource within a list of resources based on the provided query.

        The function iterates over the resources and checks if the "id" and "resource_version" of a resource match the values in the query.
        If there is a match, it removes the existing resource from the list and appends the updated resource.

        After updating the resources, the function saves the updated list to the specified file path.

        :param query: The query object containing the resource identification criteria.
        :return: A dictionary indicating that the resource was updated.
        """
        original_resource = query["original_resource"]
        modified_resource = query["resource"]
        if original_resource["id"] != modified_resource["id"] and original_resource["resource_version"] != modified_resource["resource_version"]:
            return {"status": "Cannot change resource id"}
        for resource in self.resources:
            if (
                resource["id"] == original_resource["id"]
                and resource["resource_version"] == original_resource["resource_version"]
            ):
                self.resources.remove(resource)
                self.resources.append(modified_resource)

        self.write_to_file()
        return {"status": "Updated"}

    def check_resource_exists(self, query: Dict) -> Dict:
        """
        Checks if a resource exists within a list of resources based on the provided query.

        The function iterates over the resources and checks if the "id" and "resource_version" of a resource match the values in the query.
        If a matching resource is found, it returns a dictionary indicating that the resource exists.
        If no matching resource is found, it returns a dictionary indicating that the resource does not exist.

        :param query: The query object containing the resource identification criteria.
        :return: A dictionary indicating whether the resource exists.
        """
        for resource in self.resources:
            if (
                resource["id"] == query["id"]
                and resource["resource_version"] == query["resource_version"]
            ):
                return {"exists": True}
        return {"exists": False}

    def insert_resource(self, query: Dict) -> Dict:
        """
        Inserts a new resource into a list of resources.

        The function appends the query (new resource) to the resources list, indicating the insertion.
        It then writes the updated resources to the specified file path.

        :param query: The query object containing the resource identification criteria.
        :return: A dictionary indicating that the resource was inserted.
        """
        if self.check_resource_exists(query)["exists"]:
            return {"status": "Resource already exists"}
        self.resources.append(query)
        self.write_to_file()
        return {"status": "Inserted"}

    def delete_resource(self, query: Dict) -> Dict:
        """
        This function deletes a resource from the list of resources based on the provided query.

        :param query: The query object containing the resource identification criteria.
        :return: A dictionary indicating that the resource was deleted.
        """
        for resource in self.resources:
            if (
                resource["id"] == query["id"]
                and resource["resource_version"] == query["resource_version"]
            ):
                self.resources.remove(resource)
        self.write_to_file()
        return {"status": "Deleted"}

    def write_to_file(self) -> None:
        """
        This function writes the list of resources to a file at the specified file path.

        :return: None
        """
        with Path(self.file_path).open("w") as outfile:
            json.dump(self.resources, outfile, indent=4)

    def save_session(self) -> Dict:
        """
        This function saves the client session to a dictionary.
        :return: A dictionary containing the client session.
        """
        session = {
            'client': 'json',
            'filename': self.file_path.name,
        }
        return session
