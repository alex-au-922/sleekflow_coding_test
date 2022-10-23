from fastapi import status
from fastapi.testclient import TestClient
class TestLogin:
    """Test the login endpoint"""

    def test_login_username(self, client: TestClient) -> None:
        """Test that a user can login with their username."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/login/",
            json = {
                "input_field": "testing",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert isinstance(response_json["data"], dict)
        assert response_json["msg"] == "Login successful."
        assert "access_token" in response_json["data"]
        assert "refresh_token" in response_json["data"]
        assert "expires_in" in response_json["data"]
        assert response_json["data"]["type"] == "Bearer"

    def test_login_email(self, client: TestClient) -> None:
        """Test that a user can login with their email."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/login/",
            json = {
                "input_field": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert isinstance(response_json["data"], dict)
        assert response_json["msg"] == "Login successful."
        assert "access_token" in response_json["data"]
        assert "refresh_token" in response_json["data"]
        assert "expires_in" in response_json["data"]
        assert response_json["data"]["type"] == "Bearer"

    def test_login_wrong_username_raises(self, client: TestClient) -> None:  
        """Test that a user cannot login with an invalid username."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/login/",
            json = {
                "input_field": "testin",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["error"] == "InvalidCredentialsError"
        assert response_json["error_msg"] == "Invalid credentials."
    
    def test_login_wrong_email_raises(self, client: TestClient) -> None:  
        """Test that a user cannot login with an invalid username."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/login/",
            json = {
                "input_field": "bcd@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["error"] == "InvalidCredentialsError"
        assert response_json["error_msg"] == "Invalid credentials."
    
    def test_login_username_wrong_password_raises(self, client: TestClient) -> None:  
        """Test that a user cannot login with an invalid username."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/login/",
            json = {
                "input_field": "testing",
                "password": "qwqjdkjwl",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["error"] == "InvalidCredentialsError"
        assert response_json["error_msg"] == "Invalid credentials."


    def test_login_email_wrong_password_raises(self, client: TestClient) -> None:  
        """Test that a user cannot login with an invalid username."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.post(
            "/api/login/",
            json = {
                "input_field": "abc@hello.com",
                "password": "qwqjdkjwl",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["error"] == "InvalidCredentialsError"
        assert response_json["error_msg"] == "Invalid credentials."
