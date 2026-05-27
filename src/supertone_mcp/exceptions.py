"""Domain exception hierarchy for the Supertone TTS MCP server."""


class SupertoneError(Exception):
    """Base exception for all Supertone API errors."""

    pass


class SupertoneAuthError(SupertoneError):
    """HTTP 401/403 from API."""

    pass


class SupertoneRateLimitError(SupertoneError):
    """HTTP 429 from API."""

    pass


class SupertoneServerError(SupertoneError):
    """HTTP 5xx from API."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Server error: {status_code}")


class SupertoneAPIError(SupertoneError):
    """Other HTTP 4xx errors from API."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class SupertoneConnectionError(SupertoneError):
    """Network unreachable, DNS failure, timeout."""

    pass
