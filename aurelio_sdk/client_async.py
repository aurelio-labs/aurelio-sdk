import asyncio
import os
from typing import IO, Literal, Optional

import aiohttp

from aurelio_sdk.exceptions import AurelioAPIError
from aurelio_sdk.schema import (
    ChunkingOptions,
    ChunkRequestPayload,
    ChunkResponse,
    ExtractResponse,
)


# -----------------------------
# Async Client
# -----------------------------
class AsyncAurelioClient:
    """
    An asynchronous client for interacting with the Aurelio API.

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
        >>> client = AsyncAurelioClient(api_key="your-api-key")
        >>> response = await client.chunk("Your document content here")
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

    async def chunk(
        self,
        content: str,
        processing_options: Optional[ChunkingOptions] = None,
        timeout: int = 30,
    ) -> ChunkResponse:
        """Chunk a document synchronously.

        Args:
            content: The content to chunk.
            processing_options: Processing options for the chunking.
            timeout: The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds, None means no timeout.
                After the timeout, raise a timeout error.

        Returns:
            ChunkResponse: Object containing the response from the API.

        Raises:
            AurelioAPIError: If the API request fails.
        """
        client_url = f"{self.base_url}/v1/chunk"
        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )
        session_timeout = aiohttp.ClientTimeout(total=timeout)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            async with session.post(
                client_url, json=payload.model_dump(), headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return ChunkResponse(**data)
                else:
                    error_content = await response.text()
                    raise AurelioAPIError(
                        f"API request failed with status {response.status}: {error_content}"
                    )

    async def extract_file(
        self,
        file: IO[bytes],
        quality: Literal["low", "high"],
        chunk: bool,
        timeout: int = 30,
    ) -> ExtractResponse:
        """Processes a document from an uploaded file asynchronously.

        Args:
            file (IO[bytes]): The file to extract text from (PDF, MP4).
            quality (str): Processing quality of the document, either "low" or "high".
            chunk (bool): Whether the document should be chunked.
            timeout (int): Default 30 seconds. The timeout to keep open the connection
                to the client in seconds. -1 means no timeout.
                After the timeout, the returns document ID and status "pending"

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/file"

        filename = getattr(file, "name", "document.pdf")

        data = aiohttp.FormData()
        data.add_field("file", file, filename=filename)
        data.add_field("quality", quality)
        data.add_field("chunk", str(chunk))
        data.add_field("timeout", str(timeout))

        if timeout <= 0:
            session_timeout = None
        else:
            # Add 1 second to the timeout to avoid timeout error before the request
            session_timeout = aiohttp.ClientTimeout(total=timeout + 1)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            async with session.post(
                client_url, data=data, headers=self.headers
            ) as response:
                if response.status == 200:
                    return ExtractResponse(**await response.json())
                else:
                    raise AurelioAPIError(response)

    async def extract_url(
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
            timeout: Default 30 seconds. The timeout to keep open the connection
                to the client in seconds. -1 means no timeout.
                After the timeout, the returns document ID and status "pending"

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/url"

        data = aiohttp.FormData()
        data.add_field("url", url)
        data.add_field("quality", quality)
        data.add_field("chunk", str(chunk))
        data.add_field("timeout", str(timeout))

        if timeout <= 0:
            session_timeout = None
        else:
            # Add 1 second to the timeout to avoid timeout error before the request
            session_timeout = aiohttp.ClientTimeout(total=timeout + 1)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            async with session.post(
                client_url, data=data, headers=self.headers
            ) as response:
                if response.status == 200:
                    return ExtractResponse(**await response.json())
                else:
                    raise AurelioAPIError(response)

    async def get_document(
        self, document_id: str, timeout: int = 30
    ) -> ExtractResponse:
        """
        Retrieves a processed document asynchronously.

        Args:
            document_id (str): The ID of the document to retrieve.
            timeout (int): The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds, None means no timeout.
                After the timeout, raise a timeout error.
        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/document/{document_id}"

        session_timeout = aiohttp.ClientTimeout(total=timeout)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            async with session.get(client_url, headers=self.headers) as response:
                if response.status == 200:
                    return ExtractResponse(**await response.json())
                else:
                    raise AurelioAPIError(response)

    async def wait_for_document_completion(
        self, document_id: str, timeout: int = 300
    ) -> ExtractResponse:
        """
        Waits for the document to reach 'completed' status or until timeout.

        Args:
            client: The client instance to interact with the API.
            document_id: The ID of the document to monitor.
            timeout: Maximum time to wait in seconds (default is 300 seconds).
                After the timeout, raise a timeout error.

        Returns:
            The final document response.
        """
        import time

        start_time = time.time()
        document_response = await self.get_document(document_id=document_id)

        # Poll until document status is 'completed' or timeout is reached
        while (
            document_response.status != "completed"
            and time.time() - start_time < timeout
        ):
            await asyncio.sleep(1)
            document_response = await self.get_document(document_id=document_id)
        return document_response
