from fastapi import status
from fastapi.testclient import TestClient
from data_models import DatabaseConnection
from data_models.models import Account

class TestCreateUser:
    """Test the create user endpoint."""

    def test_create_user(self, client: TestClient) -> None:
        """Test that a user can be created."""
        
        response = client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert isinstance(response_json["data"], int)
        assert response_json["msg"] == 'User "testing" created successfully.'

        with DatabaseConnection() as db:
            user = db.query(Account).filter(Account.username == "testing").one()
            assert user.user_id == int(response_json["data"])
    
    def test_create_user_duplicate_username_raises(self, client: TestClient) -> None:
        """Test that a user cannot be created with a duplicate username."""
        
        username = "testing"

        client.post(
            "/api/user/",
            json = {
                "username": username,
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/user/",
            json = {
                "username": username,
                "email": "bcd@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        response_json = response.json()
        assert response_json["error"] == "DuplicateError"
        assert response_json["error_msg"] == f'Username "{username}" already exists.'
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_create_user_duplicate_email_raises(self, client: TestClient) -> None:
        """Test that a user cannot be created with a duplicate email."""
        
        email = "abc@hello.com"
        
        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": email,
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/user/",
            json = {
                "username": "test",
                "email": email,
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        response_json = response.json()
        assert response_json["error"] == "DuplicateError"
        assert response_json["error_msg"] == f'Email "{email}" already exists.'
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_create_user_invalid_email_raises(self, client: TestClient) -> None:
        """Test that a user cannot be created with an invalid email."""

        email = "abc@hello"
        response = client.post(
            "/api/user/",
            json = {
                "username": "test",
                "email": email,
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert f'Email "{email}" is invalid' in response_json["error_msg"] 
        assert response_json["msg"] is None
        assert response_json["data"] is None
    
    def test_create_user_empty_username_raises(self, client: TestClient) -> None:
        """Test that a user cannot be created with an empty username."""

        username = ""
        response = client.post(
            "/api/user/",
            json = {
                "username": username,
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert f'Username cannot be empty' in response_json["error_msg"]
        assert response_json["msg"] is None
        assert response_json["data"] is None

    def test_create_user_short_password_raises(self, client: TestClient, short_random_string: str) -> None:
        """Test that a user cannot be created with a password shorter than 8 characters."""

        response = client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": short_random_string,
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert 'Password too short' in response_json["error_msg"]
        assert response_json["msg"] is None
        assert response_json["data"] is None
