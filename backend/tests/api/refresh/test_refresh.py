import datetime
from fastapi import status
from fastapi.testclient import TestClient
from ...mock_data import TestUserInfo
from data_models.connection import DatabaseConnection
from data_models.models import Account, Login

class TestRefresh:
    """Test the refresh endpoint for refreshing access and refresh tokens."""

    def test_refresh_refresh_access_tokens(self, client: TestClient, create_user: TestUserInfo) -> None:
        """Test that a user can login with their username."""

        login_response = client.post(
            "/api/login/",
            json = {
                "input_field": create_user.username,
                "password": create_user.password,
            }
        )

        refresh_token = login_response.json()["data"]["refresh_token"]      

        response = client.post(
            "/api/refresh/",
            json = {
                "username": create_user.username,
                "refresh_token": refresh_token,
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert isinstance(response_json["data"], dict)
        assert response_json["msg"] == "Refreshed access and refresh tokens."
        assert "access_token" in response_json["data"]
        assert "refresh_token" in response_json["data"]
        assert "expires_in" in response_json["data"]
        assert response_json["data"]["type"] == "Bearer"

class TestRefreshTokenError:
    """Test the errors when refreshing refresh and access tokens."""

    def test_refresh_token_expired_raises(self, client: TestClient, create_user: TestUserInfo) -> None:
        """Test that a user can login with their email."""

        login_response = client.post(
            "/api/login/",
            json = {
                "input_field": create_user.username,
                "password": create_user.password,
            }
        )

        refresh_token = login_response.json()["data"]["refresh_token"]      

        with DatabaseConnection() as db:
            login: Login = db.query(Login).join(Account, Account.user_id == Login.user_id).filter(Account.username == create_user.username).first()
            login.expiry_date = datetime.datetime.now() - datetime.timedelta(seconds = 1)
            db.commit()

        response = client.post(
            "/api/refresh/",
            json = {
                "username": create_user.username,
                "refresh_token": refresh_token,
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "TokenExpiredError"
        assert response_json["error_msg"] == "Token has expired."
        assert response_json["data"] is None
        assert response_json["msg"] is None

    def test_refresh_token_wrong_raises(self, client: TestClient, create_user: TestUserInfo) -> None:  
        """Test the refresh token is wrong when refresh."""

        login_response = client.post(
            "/api/login/",
            json = {
                "input_field": create_user.username,
                "password": create_user.password,
            }
        )

        refresh_token = login_response.json()["data"]["refresh_token"]      

        response = client.post(
            "/api/refresh/",
            json = {
                "username": create_user.username,
                "refresh_token": f"{refresh_token}1",
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "InvalidTokenError"
        assert response_json["error_msg"] == "Invalid token."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_no_refresh_token_issued_raises(self, client: TestClient, create_user: TestUserInfo, short_random_string: str) -> None:  
        """Test that there is no refresh token issued, that user doesn't login before."""

        response = client.post(
            "/api/refresh/",
            json = {
                "username": create_user.username,
                "refresh_token": short_random_string,
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_json = response.json()
        assert response_json["error"] == "UnauthorizedError"
        assert response_json["error_msg"] == "Unauthorized action."
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_user_not_exists_raises(self, client: TestClient, test_user_info: TestUserInfo, short_random_string: str) -> None:
        """Test that when there is no user in the database, that raises."""

        response = client.post(
            "/api/refresh/",
            json = {
                "username": test_user_info.username,
                "refresh_token": short_random_string,
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_json = response.json()
        assert response_json["error"] == "NotFoundError"
        assert response_json["error_msg"] == f'User "{test_user_info.username}" not found.'
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
   
