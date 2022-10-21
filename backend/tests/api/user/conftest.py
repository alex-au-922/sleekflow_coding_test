from typing import List
import pytest
from pytest import FixtureRequest
from util.helper.string import random_string

short_random_strings: List[str] = [
    random_string(5) for _ in range(5)
]

long_random_strings: List[str] = [
    random_string(10) for _ in range(5)
]

@pytest.fixture(params = short_random_strings)
def short_random_string(request: FixtureRequest) -> str:
    """Return a short random string"""
    
    return request.param

@pytest.fixture(params = long_random_strings)
def long_random_string(request: FixtureRequest) -> str:
    """Return a long random string"""
    
    return request.param
