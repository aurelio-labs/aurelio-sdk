import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import IO, Annotated, List, Literal, Optional, Union

import aiofiles
import aiofiles.os
import aiohttp

from aurelio_sdk.const import (
    POLLING_INTERVAL,
    UPLOAD_CHUNK_SIZE,
    WAIT_TIME_BEFORE_POLLING,
)
from aurelio_sdk.exceptions import APIError, APITimeoutError
from aurelio_sdk.logger import logger
from aurelio_sdk.schema import (
    ChunkingOptions,
    ChunkRequestPayload,
    ChunkResponse,
    EmbeddingResponse,
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
        base_url (str): The base URL for the Aurelio API.
        Defaults to "https://api.aurelio.ai".
        debug (bool): Whether to enable debug logging. Defaults to False.

    Raises:
        ValueError: If no API key is provided or found in the environment variables.

    Example:
        >>> client = AsyncAurelioClient(api_key="your-api-key")
        >>> response = await client.chunk("Your document content here")
        >>> print(response.status)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.aurelio.ai",
        debug: bool = False,
    ):
        if not base_url:
            self.base_url = "https://api.aurelio.ai"
        else:
            self.base_url = base_url

        self.api_key = api_key or os.environ.get("AURELIO_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "set as AURELIO_API_KEY environment variable."
            )

        if debug:
            logger.setLevel(logging.DEBUG)

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
        try:
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(
                    client_url, json=payload.model_dump(), headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ChunkResponse(**data)
                    else:
                        try:
                            error_content = await response.json()
                        except Exception:
                            error_content = await response.text()
                        raise APIError(
                            message=error_content,
                            status_code=response.status,
                        )
        except asyncio.TimeoutError:
            raise APITimeoutError(
                timeout=timeout,
                base_url=self.base_url,
            ) from None
        except Exception as e:
            raise APIError(message=str(e), base_url=self.base_url) from e

    async def extract_file(
        self,
        quality: Literal["low", "high"],
        chunk: bool,
        file: Optional[Union[IO[bytes], bytes]] = None,
        file_path: Optional[str] = None,
        wait: int = 30,
        polling_interval: int = POLLING_INTERVAL,
    ) -> ExtractResponse:
        """Process a document from a file asynchronously.

        Args:
            file (Optional[Union[IO[bytes], bytes, AsyncGenerator[bytes, None]]]):
                The file to extract text from (PDF, MP4).
            file_path (Optional[str]): The path to the file to extract
                text from.
            quality (Literal["low", "high"]): Processing quality of the document.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            polling_interval (int): Time between polling requests in seconds.
                Default is 5s, if polling_interval is 0, polling is disabled.

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
        """
        if not (file_path or file):
            raise ValueError("Either file_path or file must be provided")

        client_url = f"{self.base_url}/v1/extract/file"

        # Handle file from path, convert to AsyncGenerator
        if file_path:
            logger.debug(f"Uploading file from path, {file_path}")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            file_stream = _file_stream_generator(file_path)
            filename = Path(file_path).name
        else:
            filename = None

        # Add file field
        data = aiohttp.FormData()
        if file_stream:
            logger.debug("Uploading using stream")
            # Wrap the AsyncGenerator with an AsyncIterablePayload
            file_payload = aiohttp.payload.AsyncIterablePayload(value=file_stream)
            data.add_field(
                name="file",
                value=file_payload,
                filename=filename,
                content_type="application/octet-stream",
            )
        else:
            logger.debug("Uploading file bytes")
            data.add_field("file", file, filename=filename)

        # Add other fields
        data.add_field("quality", quality)
        data.add_field("chunk", str(chunk))
        initial_wait = WAIT_TIME_BEFORE_POLLING if polling_interval > 0 else wait
        data.add_field("wait", str(initial_wait))

        if wait <= 0:
            session_timeout = None
        else:
            # Add 1 second to the timeout to ensure we get the Document ID
            session_timeout = aiohttp.ClientTimeout(total=wait + 1)

        document_id = None
        status_code = None

        try:
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(
                    client_url, data=data, headers=self.headers
                ) as response:
                    status_code = response.status
                    if response.status == 200:
                        extract_response = ExtractResponse(**await response.json())
                        document_id = extract_response.document.id
                    else:
                        try:
                            error_content = await response.json()
                        except Exception:
                            error_content = await response.text()
                        raise ValueError(error_content)

            if wait == 0:
                return extract_response

            # If the document is already processed or polling is disabled,
            # return the response
            if (
                extract_response.status in ["completed", "failed"]
                or polling_interval <= 0
            ):
                return extract_response

            # Wait for the document to complete processing
            return await self.wait_for(
                document_id=document_id, wait=wait, polling_interval=polling_interval
            )
        except asyncio.TimeoutError:
            raise APITimeoutError(
                base_url=self.base_url,
                timeout=session_timeout.total if session_timeout else None,
            ) from None
        except Exception as e:
            raise APIError(
                message=str(e), base_url=self.base_url, status_code=status_code
            ) from e

    async def extract_url(
        self,
        url: str,
        quality: Literal["low", "high"],
        chunk: bool,
        wait: int = 30,
        polling_interval: int = POLLING_INTERVAL,
    ) -> ExtractResponse:
        """Process a document from a URL asynchronously.

        Args:
            url (str): The URL of the document file to be processed.
            quality (Literal["low", "high"]): Processing quality of the document.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            polling_interval (int): Time between polling requests in seconds.
                Default is 15s, if polling_interval is 0, polling is disabled.

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
        """
        client_url = f"{self.base_url}/v1/extract/url"
        data = aiohttp.FormData()
        data.add_field("url", url)
        data.add_field("quality", quality)
        data.add_field("chunk", str(chunk))

        # If polling is enabled, use a short wait time (WAIT_TIME_BEFORE_POLLING)
        # If polling is disabled, use the full wait time
        initial_request_timeout = (
            WAIT_TIME_BEFORE_POLLING if polling_interval < 0 else wait
        )
        data.add_field("wait", str(initial_request_timeout))

        if wait <= 0:
            session_timeout = None
        else:
            # Add 1 second to the timeout to ensure we get the Document ID
            session_timeout = aiohttp.ClientTimeout(total=wait + 1)

        document_id = None
        try:
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(
                    client_url, data=data, headers=self.headers
                ) as response:
                    if response.status == 200:
                        extract_response = ExtractResponse(**await response.json())
                        document_id = extract_response.document.id
                    else:
                        try:
                            error_content = await response.json()
                        except Exception:
                            error_content = await response.text()
                        raise APIError(
                            message=error_content,
                            status_code=response.status,
                        )

            if wait == 0:
                return extract_response

            # If the document is already processed or polling is disabled,
            # return the response
            if (
                extract_response.status in ["completed", "failed"]
                or polling_interval == 0
            ):
                return extract_response

            # Wait for the document to complete processing
            return await self.wait_for(
                document_id=document_id, wait=wait, polling_interval=polling_interval
            )
        except asyncio.TimeoutError:
            raise APITimeoutError(
                base_url=self.base_url,
                timeout=session_timeout.total if session_timeout else None,
            ) from None
        except Exception as e:
            raise APIError(
                message=str(e),
                base_url=self.base_url,
            ) from e

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
            try:
                async with session.get(client_url, headers=self.headers) as response:
                    if response.status == 200:
                        return ExtractResponse(**await response.json())
                    else:
                        try:
                            error_content = await response.json()
                        except Exception:
                            error_content = await response.text()
                        raise APIError(
                            message=error_content,
                            status_code=response.status,
                        )
            except aiohttp.ConnectionTimeoutError as e:
                raise APITimeoutError(
                    base_url=self.base_url,
                    timeout=session_timeout.total if session_timeout else None,
                ) from e

    async def wait_for(
        self,
        document_id: str,
        wait: int = 300,
        polling_interval: int = POLLING_INTERVAL,
    ) -> ExtractResponse:
        """
        Waits for the document to reach 'completed' or 'failed' status or until timeout.

        Args:
            client: The client instance to interact with the API.
            document_id: The ID of the document to monitor.
            wait: Maximum time to wait in seconds (default is 300 seconds).
                After the timeout, raise a timeout error.

        Returns:
            The final document response.
        """
        logger.debug(f"Starting polling for document completion: {document_id}")
        start_time = time.time()
        document_response = await self.get_document(document_id=document_id)

        FINAL_STATES = ["completed", "failed"]
        timeout_reached = False
        end_time = start_time + wait if wait >= 0 else float("inf")

        while document_response.status not in FINAL_STATES and not timeout_reached:
            await asyncio.sleep(polling_interval)

            # Check for timeout
            if time.time() > end_time:
                timeout_reached = True
                logger.debug(
                    f"Timeout reached while waiting for document {document_id}"
                )
                break

            document_response = await self.get_document(document_id=document_id)
            logger.debug(
                f"Polling document {document_id}: status={document_response.status}"
            )
        return document_response

    async def embedding(
        self,
        input: Union[str, List[str]],
        model: Annotated[str, Literal["bm25"]],
        timeout: int = 30,
    ) -> EmbeddingResponse:
        """Generate embeddings for the given input using the specified model.

        Args:
            input (Union[str, List[str]]): The text or list of texts to embed.
            model (str, optional): The model to use for embedding.
                Currently, only "bm25" is available.
            timeout (int, optional): The maximum time in seconds to keep the connection open.
                Defaults to 30 seconds. If exceeded, a timeout error is raised.

        Returns:
            EmbeddingResponse: An object containing the embedding response from the API.

        Raises:
            APIError: If the API request fails.
            APITimeoutError: If the request exceeds the specified timeout.
        """
        client_url = f"{self.base_url}/v1/embeddings"
        data = {"input": input, "model": model}

        session_timeout = aiohttp.ClientTimeout(total=timeout)
        try:
            async with aiohttp.ClientSession(timeout=session_timeout) as session:
                async with session.post(
                    client_url, json=data, headers=self.headers
                ) as response:
                    if response.status == 200:
                        return EmbeddingResponse(**await response.json())
                    else:
                        try:
                            error_content = await response.json()
                        except Exception:
                            error_content = await response.text()
                        raise APIError(
                            message=error_content,
                            status_code=response.status,
                        )
        except asyncio.TimeoutError:
            raise APITimeoutError(
                base_url=self.base_url,
                timeout=session_timeout.total if session_timeout else None,
            ) from None
        except Exception as e:
            raise APIError(message=str(e), base_url=self.base_url) from e


async def _file_stream_generator(
    file_path, chunk_size=UPLOAD_CHUNK_SIZE
) -> AsyncGenerator[bytes, None]:
    total_bytes = 0
    chunk_count = 0
    file_size = os.path.getsize(file_path)

    async with aiofiles.open(file_path, "rb") as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk
            total_bytes += len(chunk)
            chunk_count += 1
            logger.debug(
                f"Reading chunk {chunk_count}, chunk_size: {chunk_size}, total bytes: {total_bytes}"
            )
    logger.debug(
        f"Stream finished, total chunks: {chunk_count}, file size: {file_size / 1024 / 1024:.2f} MB"
    )
    assert (
        total_bytes == file_size
    ), f"Expected {file_size} bytes, but read {total_bytes} bytes"
