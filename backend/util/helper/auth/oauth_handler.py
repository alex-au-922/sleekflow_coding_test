from .jwt import JWTHandler
from ...exceptions import (
    UnauthorizedError,
    InvalidTokenError
)
from typing import Optional

jwt_handler = JWTHandler()

def auth_check(auth_header: Optional[str], auth_field: str, auth_value: str) -> None:
    """Check the authentication"""

    if auth_header is None:
        raise UnauthorizedError("Unauthorized action.")

    token = auth_header.replace("Bearer ", "")
    payload = jwt_handler.get_payload(token)
    
    if auth_field not in payload:
        raise InvalidTokenError("Invalid token.")
    
    if auth_value != payload[auth_field]:
        raise UnauthorizedError("Unauthorized action.")