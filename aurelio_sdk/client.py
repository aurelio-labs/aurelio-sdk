import os
from typing import IO, Literal, Optional

import requests

from aurelio_sdk.exceptions import AurelioAPIError
from aurelio_sdk.schema import (
    ChunkingOptions,
    ChunkRequestPayload,
    ChunkResponse,
    ExtractResponse,
)


# -----------------------------
# Sync Client
# -----------------------------
class AurelioClient:
    """
    A client for interacting with the Aurelio API.

    This class provides methods to perform various operations such as chunking documents,
    extracting text from files and URLs, and retrieving processed documents.

    Attributes:
        base_url (str): The base URL for the Aurelio API.
        api_key (str): The API key for authentication.
        headers (dict): HTTP headers including the authorization token.

    Args:
        api_key (Optional[str]): The API key for authentication. If not provided,
            it will attempt to use the AURELIO_API_KEY environment variable.
        base_url (str): The base URL for the Aurelio API. Defaults to "https://api.aurelio.ai".

    Raises:
        ValueError: If no API key is provided or found in the environment variables.

    Example:
        >>> client = AurelioClient(api_key="your-api-key")
        >>> response = client.chunk("Your document content here")
        >>> print(response.status)
    """

    def __init__(
        self, api_key: Optional[str] = None, base_url: str = "https://api.aurelio.ai"
    ):
        self.base_url = base_url

        self.api_key = api_key or os.environ.get("AURELIO_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "set as AURELIO_API_KEY environment variable."
            )
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def chunk(
        self, content: str, processing_options: Optional[ChunkingOptions] = None
    ) -> ChunkResponse:
        """Chunk a document synchronously.

        Args:
            content: The content to chunk.
            processing_options: Processing options for the chunking.

        Returns:
            ChunkResponse: Object containing the response from the API.

        Raises:
            AurelioAPIError: If the API request fails.
        """
        client_url = f"{self.base_url}/v1/chunk"

        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )
        response = requests.post(
            client_url, json=payload.model_dump(), headers=self.headers
        )
        if response.status_code == 200:
            return ChunkResponse(**response.json())
        else:
            raise AurelioAPIError(response)

    def extract_file(
        self,
        file: IO[bytes],
        quality: Literal["low", "high"],
        chunk: bool,
        timeout: int = 30,
    ) -> ExtractResponse:
        """Processes a document from an uploaded file synchronously.

        Args:
            file (IO[bytes]): The file to extract text from (PDF, MP4).
            quality (str): Processing quality of the document, either "low" or "high".
            chunk (bool): Whether the document should be chunked.
            timeout (int): The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds, -1 means no timeout.

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/file"

        filename = getattr(file, "name", "document.pdf")

        files = {"file": (filename, file)}

        data = {
            "quality": quality,
            "chunk": chunk,
            "timeout": timeout,
        }
        response = requests.post(
            client_url, files=files, data=data, headers=self.headers
        )
        if response.status_code == 200:
            return ExtractResponse(**response.json())
        else:
            raise AurelioAPIError(response)

    def extract_url(
        self,
        url: str,
        quality: Literal["low", "high"],
        chunk: bool,
        timeout: int = 30,
    ) -> ExtractResponse:
        """Process a document from a URL synchronously.

        Args:
            url: The URL of the document file.
            quality: Processing quality of the document, "low" or "high".
            chunk: Whether the document should be chunked.
            timeout: The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds, -1 means no timeout.

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/url"
        data = {
            "url": url,
            "quality": quality,
            "chunk": chunk,
            "timeout": timeout,
        }
        response = requests.post(client_url, data=data, headers=self.headers)
        if response.status_code == 200:
            return ExtractResponse(**response.json())
        else:
            raise AurelioAPIError(response)

    def get_document(self, document_id: str) -> ExtractResponse:
        """
        Retrieves a processed document synchronously.

        Args:
            document_id (str): The ID of the document to retrieve.

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/document/{document_id}"
        response = requests.get(client_url, headers=self.headers)
        if response.status_code == 200:
            return ExtractResponse(**response.json())
        else:
            raise AurelioAPIError(response)

    def wait_for_document_completion(
        self, document_id: str, timeout: int = 300
    ) -> ExtractResponse:
        """
        Waits for the document to reach 'completed' status or until timeout.

        Args:
            client: The client instance to interact with the API.
            document_id: The ID of the document to monitor.
            timeout: Maximum time to wait in seconds (default is 300 seconds).

        Returns:
            The final document response.
        """
        import time

        start_time = time.time()
        document_response = self.get_document(document_id=document_id)

        # Poll until document status is 'completed' or timeout is reached
        while (
            document_response.status != "completed"
            and time.time() - start_time < timeout
        ):
            time.sleep(1)
            document_response = self.get_document(document_id=document_id)
        return document_response
