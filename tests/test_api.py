"""Tests for AmeriGas API client."""
import pytest

from custom_components.amerigas.api import (
    AmeriGasAPI,
    AmeriGasAuthError,
    AmeriGasLoginBlockedError,
    KNOWN_INVALID_CREDENTIAL_PHRASES,
)


def test_amerigas_api_init():
    """Test initialization of AmeriGasAPI."""
    username = "test_user@example.com"
    password = "secure_password"

    api = AmeriGasAPI(username, password)

    assert api.username == username
    assert api.password == password
    assert api._session is None


def _classify(message: str) -> type[Exception]:
    """Mirror the classification branch in _async_fetch_dashboard().

    _async_fetch_dashboard() requires a live aiohttp session and network
    response, so rather than mocking the whole request/response cycle, this
    reproduces the exact matching logic under test: whether a given portal
    message is treated as a recognized bad-credentials rejection
    (AmeriGasAuthError) or an unrecognized rejection such as bot-detection
    (AmeriGasLoginBlockedError). Added in v3.2.2 — see issue #38.
    """
    message_lower = message.lower()
    if any(phrase in message_lower for phrase in KNOWN_INVALID_CREDENTIAL_PHRASES):
        return AmeriGasAuthError
    return AmeriGasLoginBlockedError


@pytest.mark.parametrize(
    "message",
    [
        "The User ID or password is incorrect. Please try again.",
        "The user id or password is incorrect",
        "Invalid credentials",
    ],
)
def test_known_bad_credential_messages_raise_auth_error(message):
    """Messages AmeriGas is known to use for genuinely wrong credentials
    must still classify as AmeriGasAuthError (-> InvalidAuth in config_flow),
    not the new AmeriGasLoginBlockedError."""
    assert _classify(message) is AmeriGasAuthError


@pytest.mark.parametrize(
    "message",
    [
        "Sorry, we are unable to process your request at this time. Please check back later.",
        "Unknown error",
        "",
    ],
)
def test_unrecognized_messages_raise_login_blocked(message):
    """Any success:false message that isn't a known bad-credentials phrase —
    including AmeriGas's bot-detection message — must classify as
    AmeriGasLoginBlockedError rather than being assumed to be a bad password."""
    assert _classify(message) is AmeriGasLoginBlockedError
