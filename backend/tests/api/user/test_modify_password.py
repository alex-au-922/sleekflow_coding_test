from fastapi import status
from fastapi.testclient import TestClient
from util.helper.string import StringHash
from data_models import DatabaseConnection
from data_models.models import Account
class TestModifyPassword:
    """Test the modify user password endpoint"""

    def test_modify_password(self, client: TestClient, hasher: StringHash) -> None:
        """Test that a user can modify their password."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.put(
            "/api/user/password/",
            json = {
                "username": "testing",
                "old_password": "qwqjdkjwlqrqo",
                "new_password": "qwqjdkjwl",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == "Password updated successfully."

        with DatabaseConnection() as db:
            user: Account = db.query(Account).filter(Account.username == "testing").one()
            password_salt = user.password_salt
            password_hash = user.password_hash

            assert hasher.verify(
                string="qwqjdkjwl",
                salt=password_salt,
                hash=password_hash
            )
    
    def test_modify_password_different_password_salt(self, client: TestClient) -> None:
        """Test that after modifying the user password, the password salt is different."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        with DatabaseConnection() as db:
            user: Account = db.query(Account).filter(Account.username == "testing").one()
            old_password_salt = user.password_salt

        response = client.put(
            "/api/user/password/",
            json = {
                "username": "testing",
                "old_password": "qwqjdkjwlqrqo",
                "new_password": "qwqjdkjwl",
            }
        )

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == "Password updated successfully."

        with DatabaseConnection() as db:
            user = db.query(Account).filter(Account.username == "testing").one()
            new_password_salt = user.password_salt
        
        assert old_password_salt != new_password_salt
    
    def test_new_password_too_short_raises(self, client: TestClient, short_random_string: str) -> None:
        """Test that if the new password is too short, it raises an error."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.put(
            "/api/user/password/",
            json = {
                "username": "testing",
                "old_password": "qwqjdkjwlqrqo",
                "new_password": short_random_string,
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_json = response.json()
        assert response_json["error"] == "ValidationError"
        assert 'Password too short' in response_json["error_msg"]
        assert response_json["data"] is None
        assert response_json["msg"] is None
    
    def test_no_user_raises(self, client: TestClient) -> None:
        """Test that when there is no valid user, it raises an error."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.put(
            "/api/user/password/",
            json = {
                "username": "testin",
                "old_password": "qwqjdkjwlqrq",
                "new_password": "qwqjdkjwl",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["error"] == "InvalidCredentialsError"
        assert response_json["error_msg"] == "Invalid credentials."
        assert response_json["data"] is None
        assert response_json["msg"] is None

    def test_old_password_incorrect_raises(self, client: TestClient) -> None:
        """Test that if the old password is incorrect, it raises an error."""

        client.post(
            "/api/user/",
            json = {
                "username": "testing",
                "email": "abc@hello.com",
                "password": "qwqjdkjwlqrqo",
            }
        )

        response = client.put(
            "/api/user/password/",
            json = {
                "username": "testing",
                "old_password": "qwqjdkjwlqrq",
                "new_password": "qwqjdkjwl",
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_json = response.json()
        assert response_json["error"] == "InvalidCredentialsError"
        assert response_json["error_msg"] == "Invalid credentials."
        assert response_json["data"] is None
        assert response_json["msg"] is None

