from typing import Generator
import pytest
from fastapi.testclient import TestClient
from ...main import app
from util.database import Base

@pytest.fixture
def db_teardown_and_setup() -> Generator[None, None, None]:
    Base.metadata.drop_all()
    Base.metadata.create_all()
    yield
    Base.metadata.drop_all()

@pytest.fixture
def client(db_teardown_and_setup) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client