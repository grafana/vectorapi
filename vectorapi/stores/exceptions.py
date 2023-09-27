__all__ = [
    "CollectionNotFound",
    "CollectionPointNotFound",
]


class CollectionNotFound(Exception):
    """
    Exception raised when attempting to get a collection that does not exist
    """

    ...


class CollectionPointNotFound(Exception):
    """
    Exception raised when attempting to get a collection point that does not exist
    """

    ...
