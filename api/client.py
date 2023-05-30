from abc import ABC, abstractmethod
from typing import Dict, List


class Client(ABC):
    def __init__(self):
        self.__undo_stack = []
        self.__redo_stack = []
        self.__undo_limit = 10

    @abstractmethod
    def find_resource(self, query: Dict)-> Dict:
        raise NotImplementedError

    @abstractmethod
    def get_versions(self, query: Dict) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def update_resource(self, query: Dict)-> Dict:
        raise NotImplementedError

    @abstractmethod
    def check_resource_exists(self, query: Dict)-> Dict:
        raise NotImplementedError

    @abstractmethod
    def insert_resource(self, query: Dict)-> Dict:
        raise NotImplementedError

    @abstractmethod
    def delete_resource(self, query: Dict)-> Dict:
        raise NotImplementedError

    @abstractmethod
    def save_session(self)-> Dict:
        raise NotImplementedError
    
    def undo_operation(self)-> Dict:
        """
        This function undoes the last operation performed on the database.
        """
        if len(self.__undo_stack) == 0:
            return {"status": "Nothing to undo"}
        operation = self.__undo_stack.pop()
        print(operation)
        if operation["operation"] == "insert":
            self.delete_resource(operation["resource"])
        elif operation["operation"] == "delete":
            self.insert_resource(operation["resource"])
        elif operation["operation"] == "update":
            self.update_resource(operation["resource"])
            temp = operation["resource"]["resource"]
            operation["resource"]["resource"] = operation["resource"]["original_resource"]
            operation["resource"]["original_resource"] = temp
        else:
            raise Exception("Invalid Operation")
        self.__redo_stack.append(operation)
        return {"status": "Undone"}

    def redo_operation(self)-> Dict:
        """
        This function redoes the last operation performed on the database.
        """
        if len(self.__redo_stack) == 0:
            return {"status": "No operations to redo"}
        operation = self.__redo_stack.pop()
        print(operation)
        if operation["operation"] == "insert":
            self.insert_resource(operation["resource"])
        elif operation["operation"] == "delete":
            self.delete_resource(operation["resource"])
        elif operation["operation"] == "update":
            self.update_resource(operation["resource"])
            temp = operation["resource"]["resource"]
            operation["resource"]["resource"] = operation["resource"]["original_resource"]
            operation["resource"]["original_resource"] = temp
        else:
            raise Exception("Invalid Operation")
        self.__undo_stack.append(operation)
        return {"status": "Redone"}

    def _add_to_stack(self, operation: Dict) -> Dict:
        if len(self.__undo_stack) == self.__undo_limit:
            self.__undo_stack.pop(0)
        self.__undo_stack.append(operation)
        self.__redo_stack.clear()
        return {"status": "Added to stack"}
    
    def get_revision_status(self) -> Dict:
        return {
            "undo": 1 if len(self.__undo_stack) == 0 else 0,
            "redo": 1 if len(self.__redo_stack) == 0 else 0    
        }
    