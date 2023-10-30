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


class CollectionPointFilterError(Exception):
    """
    Exception raised when there is an error in the filter passed to the collection point query
    """

    ...


class EmbedderModelNotFound(Exception):
    """
    Exception raised when attempting to get a model that does not exist
    """

    ...
