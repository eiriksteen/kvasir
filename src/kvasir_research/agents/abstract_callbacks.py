from abc import ABC


class AbstractCallbacks(ABC):
    """
    Class to run code during agent run for connecting to an application (streaming, saving to DB, etc)
    """
