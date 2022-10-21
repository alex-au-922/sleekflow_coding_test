from fastapi import status
from fastapi.testclient import TestClient

class TestHealthCheck:
    """Test the healthcheck endpoint."""

    def test_healthcheck(self, client: TestClient) -> None:
        """Test the healthcheck endpoint."""
        
        response = client.get("/api/healthcheck/")

        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["error"] is None
        assert response_json["error_msg"] is None
        assert response_json["data"] is None
        assert response_json["msg"] == "OK"