import asyncio
import io
import logging
import os
import time
from pathlib import Path
from typing import IO, Annotated, AsyncGenerator, List, Literal, Optional, Union

import aiofiles
import aiofiles.os
import aiohttp

from aurelio_sdk.const import (
    POLLING_INTERVAL,
    UPLOAD_CHUNK_SIZE,
    WAIT_TIME_BEFORE_POLLING,
)
from aurelio_sdk.exceptions import ApiError, ApiRateLimitError, ApiTimeoutError
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
        base_url: Optional[str] = None,
        debug: bool = False,
        source: str = "aurelio-sdk",
    ):
        if not base_url:
            self.base_url = "https://api.aurelio.ai"
        else:
            self.base_url = base_url

        self.api_key = api_key or os.environ.get("AURELIO_API_KEY", "")

        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "API key must be provided either as an argument or "
                "set as AURELIO_API_KEY environment variable."
            )

        if debug:
            logger.setLevel(logging.DEBUG)

        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.source = source

    async def chunk(
        self,
        content: str,
        processing_options: Optional[ChunkingOptions] = None,
        timeout: int = 60,
        retries: int = 3,
    ) -> ChunkResponse:
        """Chunk a document synchronously.

        Args:
            content: The content to chunk.
            processing_options: Processing options for the chunking.
            timeout: The timeout to keep open the connection to the client in
                seconds. Defaults to 60 seconds, None means no timeout.
                After the timeout, raise a timeout error.
            retries: Number of times to retry the request in case of failures.

        Returns:
            ChunkResponse: Object containing the response from the API.

        Raises:
            AurelioAPIError: If the API request fails.
            ApiRateLimitError: If the rate limit is exceeded.
            ApiTimeoutError: If the request times out.
        """
        client_url = f"{self.base_url}/v1/chunk"
        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )
        session_timeout = aiohttp.ClientTimeout(total=timeout)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for attempt in range(1, retries + 1):
                try:
                    async with session.post(
                        client_url, json=payload.model_dump(), headers=self.headers
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return ChunkResponse(**data)
                        elif response.status == 429:
                            raise ApiRateLimitError(
                                message="Rate limit exceeded of 100 requests per minute",
                                status_code=response.status,
                                base_url=self.base_url,
                            )
                        elif response.status >= 500:
                            # Server error, retry
                            error_content = await response.text()
                            if attempt == retries:
                                raise ApiError(
                                    message=error_content,
                                    status_code=response.status,
                                )
                            else:
                                logger.debug(
                                    f"Retrying due to server error (attempt {attempt}): "
                                    f"{error_content}"
                                )
                                continue  # Retry
                        else:
                            # Client error, do not retry
                            error_content = await response.text()
                            raise ApiError(
                                message=error_content,
                                status_code=response.status,
                            )
                except ApiRateLimitError as e:
                    raise e
                except asyncio.TimeoutError:
                    if attempt == retries:
                        raise ApiTimeoutError(
                            timeout=timeout, base_url=self.base_url
                        ) from None
                    else:
                        logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                        continue  # Retry
                except Exception as e:
                    raise ApiError(
                        message=str(e), base_url=self.base_url
                    ) from e  # break
        raise ApiError(
            message="Failed to get chunk response",
            base_url=self.base_url,
        )

    async def extract_file(
        self,
        chunk: bool = False,
        quality: Optional[Literal["low", "high"]] = None,
        file: Optional[Union[IO[bytes], bytes]] = None,
        file_path: Optional[Union[str, Path]] = None,
        wait: int = 30,
        polling_interval: int = POLLING_INTERVAL,
        retries: int = 3,
        chunk_size: int = UPLOAD_CHUNK_SIZE,
        model: Optional[
            Literal["aurelio-base", "docling-base", "gemini-2-flash-lite"]
        ] = None,
    ) -> ExtractResponse:
        """Process a document from a file asynchronously.

        Args:
            file (Optional[Union[IO[bytes], bytes, AsyncGenerator[bytes, None]]]):
                The file to extract text from (PDF, MP4).
            file_path (Optional[str]): The path to the file to extract
                text from.
            quality (Literal["low", "high"]): Processing quality of the document. Deprecated, use model instead.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
                polling_interval (int): Time between polling requests in seconds.
                Default is 5s, if polling_interval is 0, polling is disabled.
            retries (int): Number of times to retry the request in case of failures.
                Defaults to 3. Retries on 5xx errors.
            chunk_size (int): The size of the chunks to read from the file.
                Defaults to 40MB.
            model (Optional[Literal["aurelio-base", "docling-base", "gemini-2-flash-lite"]]):
                Processing model to use. If not provided, it will be inferred from quality.

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
            ApiRateLimitError: If the rate limit is exceeded.
        """
        if not (file_path or file):
            raise ValueError("Either file_path or file must be provided")

        client_url = f"{self.base_url}/v1/extract/file"

        # Map quality to model if model is not provided
        if model is None:
            # Check if file is video based on extension
            is_video = False
            if file_path:
                file_extension = Path(file_path).suffix.lower()
                is_video = file_extension in [".mp4"]
            elif file and hasattr(file, "name"):
                file_name = getattr(file, "name", "")
                file_extension = Path(file_name).suffix.lower()
                is_video = file_extension in [".mp4"]

            # For video files, always use aurelio-base regardless of quality
            if is_video:
                model = "aurelio-base"
            elif quality == "high":
                model = "docling-base"
            else:  # quality == "low"
                model = "aurelio-base"

        if wait <= 0:
            session_timeout = None
        else:
            # Add 1 second to the timeout to ensure we get the Document ID
            session_timeout = aiohttp.ClientTimeout(total=wait + 1)

        extract_response = None

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for attempt in range(1, retries + 1):
                # Form data
                data = aiohttp.FormData()
                data.add_field("model", model)
                data.add_field("chunk", str(chunk))
                initial_wait = (
                    WAIT_TIME_BEFORE_POLLING if polling_interval > 0 else wait
                )
                data.add_field("wait", str(initial_wait))

                # Handle file from path, convert to AsyncGenerator
                if file_path:
                    if not await aiofiles.os.path.exists(file_path):
                        raise FileNotFoundError(f"File not found: {file_path}")

                    # Open the file and keep it open during the API call
                    async with aiofiles.open(file_path, "rb") as file_buffer:
                        filename = Path(file_path).name
                        file_size = await aiofiles.os.path.getsize(file_path)

                        # Stream the file in chunks
                        async def _file_stream() -> AsyncGenerator[bytes, None]:
                            total_bytes = 0
                            chunk_count = 0
                            try:
                                while True:
                                    chunk = await file_buffer.read(chunk_size)
                                    if not chunk:
                                        break
                                    yield chunk
                                    total_bytes += len(chunk)
                                    chunk_count += 1
                                    logger.debug(
                                        f"Reading chunk {chunk_count}, chunk_size: "
                                        f"{chunk_size / 1024 / 1024:.2f} MB, "
                                        f"total size: {total_bytes / 1024 / 1024:.2f} MB"
                                    )

                                if total_bytes != file_size:
                                    logger.warning(
                                        f"File size mismatch: expected {file_size} bytes, "
                                        f"but read {total_bytes} bytes"
                                    )
                            except Exception as e:
                                logger.error(f"Error during file streaming: {str(e)}")
                                raise

                        # Wrap the AsyncGenerator with an AsyncIterablePayload
                        file_payload = aiohttp.payload.AsyncIterablePayload(
                            _file_stream()
                        )
                        file_payload.content_type
                        data.add_field(
                            name="file",
                            value=file_payload,
                            filename=filename,
                            content_type=file_payload.content_type,
                        )

                        # Call the API within the same context to keep the file open
                        try:
                            async with session.post(
                                client_url, data=data, headers=self.headers
                            ) as response:
                                logger.debug("Calling API")
                                if response.status == 200:
                                    extract_response = ExtractResponse(
                                        **await response.json()
                                    )
                                    document_id = extract_response.document.id
                                    break  # Success
                                elif response.status == 429:
                                    raise ApiRateLimitError(
                                        status_code=response.status,
                                        base_url=self.base_url,
                                    )
                                elif response.status >= 500:
                                    error_content = await response.text()
                                    if attempt == retries:
                                        raise ApiError(
                                            message=error_content,
                                            status_code=response.status,
                                        )
                                    else:
                                        logger.debug(
                                            f"Retrying due to server error (attempt {attempt}): "
                                            f"{error_content}"
                                        )
                                        continue  # Retry
                                else:
                                    try:
                                        error_content = await response.text()
                                    except Exception:
                                        error_content = await response.text()
                                    raise ApiError(
                                        message=error_content,
                                        status_code=response.status,
                                    )
                        except ApiRateLimitError as e:
                            raise e from None
                        except asyncio.TimeoutError:
                            if attempt == retries:
                                raise ApiTimeoutError(
                                    base_url=self.base_url,
                                    timeout=session_timeout.total
                                    if session_timeout
                                    else None,
                                ) from None
                            else:
                                logger.debug(
                                    f"Timeout error on attempt {attempt}, retrying..."
                                )
                                continue  # Retry
                        except Exception as e:
                            raise ApiError(
                                message=str(e),
                                base_url=self.base_url,
                            ) from e

                # Handles file bytes
                else:
                    try:
                        if isinstance(file, (bytes, bytearray)):
                            data.add_field("file", file)
                        elif isinstance(file, io.IOBase):
                            # Handle file-like objects
                            pos = file.tell()
                            file.seek(0)
                            file_content = file.read()
                            data.add_field("file", file_content)
                            file.seek(pos)
                    except Exception as e:
                        raise ApiError(
                            message=f"Failed to read file contents: {str(e)}",
                            base_url=self.base_url,
                        ) from e

                    # Call the API
                    try:
                        async with session.post(
                            client_url, data=data, headers=self.headers
                        ) as response:
                            logger.debug("Calling API")
                            if response.status == 200:
                                extract_response = ExtractResponse(
                                    **await response.json()
                                )
                                document_id = extract_response.document.id
                                break  # Success
                            elif response.status == 429:
                                raise ApiRateLimitError(
                                    status_code=response.status,
                                    base_url=self.base_url,
                                )
                            elif response.status >= 500:
                                error_content = await response.text()
                                if attempt == retries:
                                    raise ApiError(
                                        message=error_content,
                                        status_code=response.status,
                                    )
                                else:
                                    logger.debug(
                                        f"Retrying due to server error (attempt {attempt}): "
                                        f"{error_content}"
                                    )
                                    continue  # Retry
                            else:
                                try:
                                    error_content = await response.text()
                                except Exception:
                                    error_content = await response.text()
                                raise ApiError(
                                    message=error_content,
                                    status_code=response.status,
                                )
                    except ApiRateLimitError as e:
                        raise e from None
                    except asyncio.TimeoutError:
                        if attempt == retries:
                            raise ApiTimeoutError(
                                base_url=self.base_url,
                                timeout=session_timeout.total
                                if session_timeout
                                else None,
                            ) from None
                        else:
                            logger.debug(
                                f"Timeout error on attempt {attempt}, retrying..."
                            )
                            continue  # Retry
                    except Exception as e:
                        raise ApiError(
                            message=str(e),
                            base_url=self.base_url,
                        ) from e

        if extract_response is None:
            raise ApiError(
                message="Failed to get document response",
                base_url=self.base_url,
            )
        if wait == 0:
            return extract_response

        # If the document is already processed or polling is disabled,
        # return the response
        if extract_response.status in ["completed", "failed"] or polling_interval <= 0:
            return extract_response

        # Wait for the document to complete processing
        return await self.wait_for(
            document_id=document_id,
            wait=wait,
            polling_interval=polling_interval,
        )

    async def extract_url(
        self,
        url: str,
        quality: Optional[Literal["low", "high"]] = None,
        chunk: bool = False,
        wait: int = 30,
        polling_interval: int = POLLING_INTERVAL,
        retries: int = 3,
        model: Optional[
            Literal["aurelio-base", "docling-base", "gemini-2-flash-lite"]
        ] = None,
    ) -> ExtractResponse:
        """Process a document from a URL asynchronously.

        Args:
            url (str): The URL of the document file to be processed.
            quality (Literal["low", "high"]): Processing quality of the document. Deprecated, use model instead.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            polling_interval (int): Time between polling requests in seconds.
                Default is 15s, if polling_interval is 0, polling is disabled.
            retries (int): Number of times to retry the request in case of failures.
            model (Optional[Literal["aurelio-base", "docling-base", "gemini-2-flash-lite"]]):
                Processing model to use. If not provided, it will be inferred from quality.

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
        """
        client_url = f"{self.base_url}/v1/extract/url"

        # Map quality to model if model is not provided
        if model is None:
            # Check if URL points to a video based on extension
            lower_url = url.lower()
            is_video_url = (
                any(lower_url.endswith(ext) for ext in [".mp4"]) or "video" in lower_url
            )

            # For video URLs, always use aurelio-base regardless of quality
            if is_video_url:
                model = "aurelio-base"
            elif quality == "high":
                model = "docling-base"
            else:  # quality == "low"
                model = "aurelio-base"

        if wait <= 0:
            session_timeout = None
        else:
            # Add 1 second to the timeout to ensure we get the Document ID
            session_timeout = aiohttp.ClientTimeout(total=wait + 1)

        extract_response = None

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for attempt in range(1, retries + 1):
                data = aiohttp.FormData()
                data.add_field("url", url)
                data.add_field("model", model)
                data.add_field("chunk", str(chunk))

                # If polling is enabled (polling_interval > 0), use a short wait time
                # (WAIT_TIME_BEFORE_POLLING)
                # If polling is disabled (polling_interval <= 0), use the full wait time
                initial_request_timeout = (
                    WAIT_TIME_BEFORE_POLLING if polling_interval < 0 else wait
                )
                data.add_field("wait", str(initial_request_timeout))

                try:
                    async with session.post(
                        client_url, data=data, headers=self.headers
                    ) as response:
                        if response.status == 200:
                            extract_response = ExtractResponse(**await response.json())
                            break  # Success
                        elif response.status == 429:
                            raise ApiRateLimitError(
                                status_code=response.status,
                                base_url=self.base_url,
                            )
                        elif response.status >= 500:
                            error_content = await response.text()
                            if attempt == retries:
                                raise ApiError(
                                    message=error_content,
                                    status_code=response.status,
                                )
                            else:
                                logger.debug(
                                    f"Server error (attempt {attempt}): {error_content}"
                                )
                                continue  # Retry
                        else:
                            # client error, do not retry
                            try:
                                error_content = await response.json()
                            except Exception:
                                error_content = await response.text()
                            raise ApiError(
                                message=error_content,
                                status_code=response.status,
                            )
                except ApiRateLimitError as e:
                    raise e from None
                except asyncio.TimeoutError:
                    if attempt == retries:
                        raise ApiTimeoutError(
                            base_url=self.base_url,
                            timeout=session_timeout.total if session_timeout else None,
                        ) from None
                    logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                    continue  # Retry
                except Exception as e:
                    raise ApiError(
                        message=f"Failed to get response after {retries} retries: {str(e)}",
                        base_url=self.base_url,
                    ) from e

        if extract_response is None:
            raise ApiError(
                message=f"Failed to get document response from url {url}",
                base_url=self.base_url,
            )

        if wait == 0:
            return extract_response

        # If the document is already processed or polling is disabled,
        # return the response
        if extract_response.status in ["completed", "failed"] or polling_interval == 0:
            return extract_response

        # Wait for the document to complete processing
        return await self.wait_for(
            document_id=extract_response.document.id,
            wait=wait,
            polling_interval=polling_interval,
        )

    async def get_document(
        self, document_id: str, timeout: int = 30, retries: int = 3
    ) -> ExtractResponse:
        """
        Retrieves a processed document asynchronously.

        Args:
            document_id (str): The ID of the document to retrieve.
            timeout (int): The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds, None means no timeout.
                After the timeout, raise a timeout error.
            retries (int): Number of times to retry the request in case of failures.
                Defaults to 3.
        Returns:
            ExtractResponse: An object containing the response from the API.

        Raises:
            ApiRateLimitError: If the rate limit is exceeded.
            ApiTimeoutError: If the request times out.
            ApiError: If there's an error in the API response.
        """
        client_url = f"{self.base_url}/v1/extract/document/{document_id}"

        session_timeout = aiohttp.ClientTimeout(total=timeout)

        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for attempt in range(1, retries + 1):
                try:
                    async with session.get(
                        client_url, headers=self.headers
                    ) as response:
                        if response.status == 200:
                            return ExtractResponse(**await response.json())
                        elif response.status == 429:
                            raise ApiRateLimitError(
                                message="Rate limit exceeded",
                                status_code=response.status,
                                base_url=self.base_url,
                            )
                        elif response.status >= 500:
                            # Server error, retry
                            error_content = await response.text()
                            if attempt == retries:
                                raise ApiError(
                                    message=error_content,
                                    status_code=response.status,
                                )
                            else:
                                logger.debug(
                                    f"Retrying due to server error (attempt {attempt}): "
                                    f"{error_content}"
                                )
                                continue  # Retry
                        else:
                            # Client error, do not retry
                            try:
                                error_content = await response.json()
                            except Exception:
                                error_content = await response.text()
                            raise ApiError(
                                message=error_content,
                                status_code=response.status,
                            )
                except ApiRateLimitError as e:
                    raise e
                except aiohttp.ConnectionTimeoutError as e:
                    logger.error(
                        f"Connection timeout: {e}, timeout: "
                        f"{session_timeout.total if session_timeout else None}"
                    )
                    raise ApiTimeoutError(
                        base_url=self.base_url,
                        timeout=session_timeout.total if session_timeout else None,
                    ) from e
                except Exception as e:
                    raise ApiError(
                        message=str(e),
                        base_url=self.base_url,
                    ) from e

        raise ApiError(
            message=f"Failed to get document {document_id} response",
            base_url=self.base_url,
        )

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
        input_type: Annotated[str, Literal["queries", "documents"]],
        model: Annotated[str, Literal["bm25"]],
        timeout: int = 30,
        retries: int = 3,
    ) -> EmbeddingResponse:
        """Generate embeddings for the given input using the specified model.

        Args:
            input (Union[str, List[str]]): The text or list of texts to embed.
            model (str, optional): The model to use for embedding.
                Currently, only "bm25" is available.
            timeout (int, optional): The maximum time in seconds to keep the connection open.
                Defaults to 30 seconds. If exceeded, a timeout error is raised.
            retries (int, optional): Number of times to retry the request in case of failures.

        Returns:
            EmbeddingResponse: An object containing the embedding response from the API.

        Raises:
            APIError: If the API request fails.
            APITimeoutError: If the request exceeds the specified timeout.
            ApiRateLimitError: If the rate limit is exceeded.
        """
        client_url = f"{self.base_url}/v1/embeddings"

        session_timeout = aiohttp.ClientTimeout(total=timeout)

        # Added retry logic similar to extract_url
        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for attempt in range(1, retries + 1):
                data = {"input": input, "input_type": input_type, "model": model}
                try:
                    async with session.post(
                        client_url, json=data, headers=self.headers
                    ) as response:
                        if response.status == 200:
                            return EmbeddingResponse(**await response.json())
                        elif response.status == 429:
                            raise ApiRateLimitError(
                                status_code=response.status,
                                base_url=self.base_url,
                            )
                        elif response.status >= 500:
                            error_content = await response.text()
                            if attempt == retries:
                                raise ApiError(
                                    message=error_content,
                                    status_code=response.status,
                                )
                            else:
                                logger.debug(
                                    f"Server error (attempt {attempt}): {error_content}"
                                )
                                continue  # Retry
                        else:
                            try:
                                error_content = await response.json()
                            except Exception:
                                error_content = await response.text()
                            raise ApiError(
                                message=error_content,
                                status_code=response.status,
                            )
                except ApiRateLimitError as e:
                    raise e
                except asyncio.TimeoutError:
                    if attempt == retries:
                        raise ApiTimeoutError(
                            base_url=self.base_url,
                            timeout=session_timeout.total if session_timeout else None,
                        ) from None
                    else:
                        logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                        continue  # Retry
                except Exception as e:
                    raise ApiError(message=str(e), base_url=self.base_url) from e
        raise ApiError(
            message="Failed to get embedding response",
            base_url=self.base_url,
        )
