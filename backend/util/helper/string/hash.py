from hashlib import blake2b
from abc import ABC, abstractmethod

class StringHash(ABC):

    @abstractmethod 
    def hash(self, *, string: str, salt: str) -> str:
        """Hash sensitive string"""

    @abstractmethod
    def verify(self, *, string: str, salt: str, hash: str) -> bool:
        """Verify a hash against a string"""

class StringHashFactory:

    def get_hasher(self, hasher: str) -> StringHash:
        """Get hasher instance"""
        match hasher:
            case "blake2b":
                return Blake2bHash()
            case _:
                raise ValueError(f"Hasher {hasher} is not supported")

class Blake2bHash(StringHash):
    """Blake2b hash class"""

    def hash(self, *, string: str, salt: str) -> str:
        """Hash sensitive string with blake2b algorithm"""

        concated_string = string + salt
        hash_object = blake2b()
        hash_object.update(concated_string.encode())
        return hash_object.hexdigest()
    
    def verify(self, *, string: str, salt: str, hash: str) -> bool:
        """Verify a hash against a string"""
        
        return self.hash(string=string, salt=salt) == hash
    