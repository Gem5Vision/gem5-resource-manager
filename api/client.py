import abc
from abc import ABC, abstractmethod

class Client(ABC):

    @abstractmethod
    def findResource(self,query):
        raise NotImplementedError
    
    @abstractmethod
    def getVersions(self, query):
        raise NotImplementedError
    
    @abstractmethod
    def updateResource(self, query):
        raise NotImplementedError
    
    @abstractmethod
    def checkResourceExists(self,  query):
        raise NotImplementedError
    
    @abstractmethod
    def insertResource(self, query):
        raise NotImplementedError
    
    @abstractmethod
    def deleteResource(self, query):
        raise NotImplementedError
    
