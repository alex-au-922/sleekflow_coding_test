class InternalServerError(Exception):
    """Raised when an internal server error occurs."""
class NotFoundError(Exception):
    """Raised when a resource is not found."""
class TokenExpiredError(Exception):
    """Raised when a token has expired."""
class InvalidTokenError(Exception):
    """Raised when a token is invalid."""
class UnauthorizedError(Exception):
    """Raised when a user is unauthorized to perform an action."""