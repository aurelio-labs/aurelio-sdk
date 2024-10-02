from typing import Optional

import aiohttp


class APIError(Exception):
    """
    Exception for API errors.
    """

    def __init__(self, response, document_id: Optional[str] = None):
        if isinstance(response, aiohttp.ClientResponse):
            self.status_code = response.status
        else:
            self.status_code = response.status_code
        try:
            self.error = response.json()
        except ValueError:
            self.error = response.text
        super().__init__(
            f"API request failed with status {self.status_code}: {self.error}. "
            f"Document ID: {document_id}"
        )


class APITimeoutError(TimeoutError):
    """
    Exception for timeout errors, includes document_id as a reference.
    """

    def __init__(self, document_id: Optional[str] = None):
        self.document_id = document_id
        super().__init__(f"Operation timed out. Document ID: {self.document_id}")
