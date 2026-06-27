"""Tests for AmeriGas API client."""
from custom_components.amerigas.api import AmeriGasAPI

def test_amerigas_api_init():
    """Test initialization of AmeriGasAPI."""
    username = "test_user@example.com"
    password = "secure_password"

    api = AmeriGasAPI(username, password)

    assert api.username == username
    assert api.password == password
    assert api._session is None
