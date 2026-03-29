
class RateLimitedError(Exception):
    """
    Raised when API requests are rate limited or throttled by the server.
    """

    def __init__(self, message: str | None = None) -> None:
        """
        Initialize RateLimitedError with optional context.

        Args:
            message: The error message from the API, typically containing the 'info' field.
        """
        self.message: str = message or "Rate limited. Please try again later."
        super().__init__(self.message)

    def __str__(self) -> str:
        """
        Return a human-readable error message.

        Returns:
            A string describing the rate limiting issue.
        """
        return self.message
