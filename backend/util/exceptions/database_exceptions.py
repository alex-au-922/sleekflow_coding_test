class DatabaseError(Exception):
    """Base class for database exceptions."""

class InvalidCredentialsError(DatabaseError):
    """Raised when the credentials are invalid."""

class DuplicateError(DatabaseError):
    """Raised when a duplicate entry is found."""