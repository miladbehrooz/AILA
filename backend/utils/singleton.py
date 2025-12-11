from threading import Lock
from typing import ClassVar


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    Attributes:
        _instances (ClassVar): Dictionary to hold single instances of classes.
        _lock (Lock): A lock object to ensure thread-safe instantiation.
    """

    _instances: ClassVar = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs) -> object:
        """Return the shared instance, creating it when necessary.
        Returns:
            object: The singleton instance of the class.
        """

        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance

        return cls._instances[cls]
