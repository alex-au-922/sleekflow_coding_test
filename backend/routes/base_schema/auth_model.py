from pydantic import BaseModel
from abc import ABC, abstractmethod

class AuthModel(BaseModel, ABC):
    """Auth model class for api"""

    @abstractmethod
    def get_auth_user(self) -> str:
        """Get auth user"""