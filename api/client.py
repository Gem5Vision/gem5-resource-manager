import abc
from abc import ABC, abstractmethod


class Client(ABC):
    def __init__(self):
        self.__undo_stack = []
        self.__redo_stack = []
        self.__undo_limit = 10

    @abstractmethod
    def findResource(self, query):
        raise NotImplementedError

    @abstractmethod
    def getVersions(self, query):
        raise NotImplementedError

    @abstractmethod
    def updateResource(self, query):
        raise NotImplementedError

    @abstractmethod
    def checkResourceExists(self, query):
        raise NotImplementedError

    @abstractmethod
    def insertResource(self, query):
        raise NotImplementedError

    @abstractmethod
    def deleteResource(self, query):
        raise NotImplementedError

    @abstractmethod
    def deleteResource(self, query):
        raise NotImplementedError

    def undoOperation(self):
        """
        This function undoes the last operation performed on the database.
        """
        if len(self.__undo_stack) == 0:
            return {"status": "Nothing to undo"}
        operation = self.__undo_stack.pop()
        print(operation)
        if operation["operation"] == "insert":
            self.deleteResource(operation["resource"])
        elif operation["operation"] == "delete":
            self.insertResource(operation["resource"])
        elif operation["operation"] == "update":
            self.updateResource(operation["resource"])
            temp = operation["resource"]["resource"]
            operation["resource"]["resource"] = operation["resource"]["original_resource"]
            operation["resource"]["original_resource"] = temp
        else:
            raise Exception("Invalid Operation")
        self.__redo_stack.append(operation)
        return {"status": "Undone"}

    def redoOperation(self):
        """
        This function redoes the last operation performed on the database.
        """
        if len(self.__redo_stack) == 0:
            return {"status": "No operations to redo"}
        operation = self.__redo_stack.pop()
        print(operation)
        if operation["operation"] == "insert":
            self.insertResource(operation["resource"])
        elif operation["operation"] == "delete":
            self.deleteResource(operation["resource"])
        elif operation["operation"] == "update":
            self.updateResource(operation["resource"])
            temp = operation["resource"]["resource"]
            operation["resource"]["resource"] = operation["resource"]["original_resource"]
            operation["resource"]["original_resource"] = temp
        else:
            raise Exception("Invalid Operation")
        self.__undo_stack.append(operation)
        return {"status": "Redone"}

    def _addToStack(self, operation):
        if len(self.__undo_stack) == self.__undo_limit:
            self.__undo_stack.pop(0)
        self.__undo_stack.append(operation)
        self.__redo_stack.clear()
        return {"status": "Added to stack"}
