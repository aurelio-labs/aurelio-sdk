from typing import Optional, Union


class APIError(Exception):
    """
    Exception for API errors.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        document_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        message = f"[AurelioSDK] API request failed: {message}."
        if document_id:
            message += f" Document ID: {document_id}"
        if status_code:
            message += f" Status code: {status_code}"
        if base_url:
            message += f" Base URL: {base_url}"
        super().__init__(message)


class APITimeoutError(TimeoutError):
    """
    Exception for timeout errors.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[Union[int, float]] = None,
    ):
        message = "[AurelioSDK] Operation timed out."
        if timeout:
            message += f" Timeout value: {timeout}s."
        if base_url:
            message += f" Base URL: {base_url}"
        super().__init__(message)
