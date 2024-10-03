from typing import Any, Optional


class APIError(Exception):
    """
    Exception for API errors.
    """

    def __init__(
        self, status_code: Optional[int], error: Any, document_id: Optional[str] = None
    ):
        self.status_code = status_code
        self.error = error
        message = f"API request failed with status {self.status_code}: {self.error}."
        if document_id:
            message += f" Document ID: {document_id}"
        super().__init__(message)


class APITimeoutError(TimeoutError):
    """
    Exception for timeout errors.
    """

    def __init__(self, document_id: Optional[str] = None):
        message = "Operation timed out."
        if document_id:
            message += f" Document ID: {document_id}"
        super().__init__(message)
