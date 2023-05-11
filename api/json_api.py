from bson import json_util
from pathlib import Path
import json


def findResource(resources, query):
    """
    Finds and returns the matching resources based on the provided query.

    The function iterates over the resources and compares the "id" and "resource_version" fields with the values in the query.
    If the "resource_version" in the query is empty or "Latest", it checks for a matching "id" value.
    If the "resource_version" in the query is not empty and not "Latest", it checks for matching "id" and "resource_version" values.

    If a matching resource is found, it is returned as a JSON string.

    If no matching resources are found, a response indicating that the resource does not exist is returned.

    If multiple matching resources are found, the function returns the one with the highest version number.

    :param resources: The list of resources to search within.
    :param query: The query object containing the search criteria.
    :return: The matching resource(s) as a JSON string, or a response indicating the resource does not exist.
    """
    found_resources = []
    for resource in resources:
        if query["resource_version"] == "" or query["resource_version"] == "Latest":
            if resource["id"] == query["id"]:
                found_resources.append(resource)
        else:
            if (
                resource["id"] == query["id"]
                and resource["resource_version"] == query["resource_version"]
            ):
                return json_util.dumps([resource])
    if not found_resources:
        return {"exists": False}
    return json_util.dumps(
        [
            max(
                found_resources,
                key=lambda resource: tuple(
                    map(int, resource["resource_version"].split("."))
                ),
            )
        ]
    )


def getVersions(resources, query):
    """
    Retrieves the versions of a resource based on the provided query.

    The function iterates over the resources and checks if the "id" field matches the value in the query.
    If there is a match, it appends the "resource_version" of the resource to a list.

    The list of versions is then sorted in descending order based on the version numbers.

    The function returns the list of versions as a JSON string.

    :param resources: The list of resources to search within.
    :param query: The query object containing the search criteria.
    :return: The versions of the resource as a JSON string.
    """
    versions = []
    for resource in resources:
        if resource["id"] == query["id"]:
            versions.append({"resource_version": resource["resource_version"]})
    versions.sort(
        key=lambda resource: tuple(map(int, resource["resource_version"].split("."))),
        reverse=True,
    )
    return json_util.dumps(versions)


def updateResource(resources, query, file_path):
    """
    Updates a resource within a list of resources based on the provided query.

    The function iterates over the resources and checks if the "id" and "resource_version" of a resource match the values in the query.
    If there is a match, it removes the existing resource from the list and appends the updated resource.

    After updating the resources, the function saves the updated list to the specified file path.

    :param resources: The list of resources to update.
    :param query: The query object containing the update criteria.
    :param file_path: The file path to save the updated resources.
    :return: A dictionary indicating the status of the update.
    """
    print("before update:\n", resources)

    for resource in resources:
        if (
            resource["id"] == query["id"]
            and resource["resource_version"] == query["resource"]["resource_version"]
        ):
            resources.remove(resource)
            resources.append(query["resource"])

    print("after update:\n", resources)
    writeToFile(file_path, resources)
    return {"status": "Updated"}


def checkResourceExists(resources, query):
    """
    Checks if a resource exists within a list of resources based on the provided query.

    The function iterates over the resources and checks if the "id" and "resource_version" of a resource match the values in the query.
    If a matching resource is found, it returns a dictionary indicating that the resource exists.
    If no matching resource is found, it returns a dictionary indicating that the resource does not exist.

    :param resources: The list of resources to check.
    :param query: The query object containing the resource identification criteria.
    :return: A dictionary indicating if the resource exists or not.
    """
    for resource in resources:
        if (
            resource["id"] == query["id"]
            and resource["resource_version"] == query["resource_version"]
        ):
            return {"exists": True}
    return {"exists": False}


def insertResource(resources, query, file_path):
    """
    Inserts a new resource into a list of resources.

    The function appends the query (new resource) to the resources list, indicating the insertion.
    It then writes the updated resources to the specified file path.

    :param resources: The list of resources.
    :param query: The resource object to insert.
    :param file_path: The file path to write the updated resources to.
    :return: A dictionary indicating the status of the insertion.
    """
    print("before insert:\n", resources)
    resources.append(query)
    print("after insert:\n", resources)
    writeToFile(file_path, resources)
    return {"status": "Inserted"}


def deleteResource(resources, query, file_path):
    """
    This function deletes a resource from the list of resources based on the provided query.

    :param resources: List of resources
    :param query: JSON object with id and resource_version
    :param file_path: File path where the resources are stored
    :return: JSON object with status message
    """
    for resource in resources:
        if (
            resource["id"] == query["id"]
            and resource["resource_version"] == query["resource_version"]
        ):
            resources.remove(resource)
    writeToFile(file_path, resources)

    return {"status": "Deleted"}


def writeToFile(file_path, resources):
    """
    This function writes the list of resources to a file at the specified file path.

    :param file_path: File path where the resources will be written
    :param resources: List of resources to be written to the file
    """
    with Path(file_path).open("w") as outfile:
        json.dump(resources, outfile, indent=4)
