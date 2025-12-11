class LAIAException(Exception):
    """Base exception for LAIA-specific errors."""


class ImproperlyConfigured(LAIAException):
    """Raised when configuration metadata is invalid or missing."""
