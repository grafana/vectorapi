__all__ = [
    "CollectionNotFound",
]

class CollectionNotFound(Exception):
    """
    Exception raised when attempting to get a collection that does not exist
    """

    ...