from typing import List
from abc import ABC, abstractmethod
from vectorapi.models.collection import Collection


class Client(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_collection(self, collection: Collection) -> Collection:
        raise NotImplementedError()

    @abstractmethod
    def get_collection(self, name: str) -> Collection:
        raise NotImplementedError()

    @abstractmethod
    def get_or_create_collection(self, name: str) -> Collection:
        raise NotImplementedError()

    @abstractmethod
    def delete_collection(self, name: str):
        raise NotImplementedError()

    @abstractmethod
    def list_collections(self, collection: Collection) -> List[Collection]:
        raise NotImplementedError()

    # @abstractmethod
    # def update_collection(self, name: str, dimension: int):
    #     pass
