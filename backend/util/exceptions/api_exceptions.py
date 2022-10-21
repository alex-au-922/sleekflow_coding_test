class InternalServerError(Exception):
    """Raised when an internal server error occurs."""
class TokenExpiredError(Exception):
    """Raised when a token has expired."""
class UnauthorizedError(Exception):
    """Raised when a user is unauthorized to perform an action."""