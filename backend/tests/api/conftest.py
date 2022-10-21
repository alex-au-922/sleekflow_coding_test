from typing import Generator
import pytest
from fastapi.testclient import TestClient
from ...main import app
from data_models import Base, Engine

@pytest.fixture
def db_teardown_and_setup() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind = Engine)
    Base.metadata.create_all(bind = Engine)
    yield
    Base.metadata.drop_all(bind = Engine)

@pytest.fixture
def client(db_teardown_and_setup) -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client