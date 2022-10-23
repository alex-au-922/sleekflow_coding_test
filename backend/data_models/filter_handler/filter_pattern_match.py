import re 
from typing import Optional

class FilterPatternMatch:
    __PATTERN = r"^\[(eq|gt|lt|ge|le|ne)\](.*)$"

    def __init__(self, string: str) -> None:
        self.__string = string
    
    def __call__(self) -> None:
        match = re.search(self.__PATTERN, self.__string)

        if match is None:
            raise ValueError("Invalid filter pattern")
        
        self.__operator = match.group(1)
        self.__value = match.group(2)
    
    def get_operator(self) -> Optional[str]:
        return self.__operator
    
    def get_value(self) -> str:
        return self.__value