from __future__ import annotations

import logging
import os
import pathlib
import time
from typing import IO, Annotated, List, Literal, Optional, Union

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from aurelio_sdk.const import POLLING_INTERVAL, WAIT_TIME_BEFORE_POLLING
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

    def chunk(
        self,
        content: str,
        processing_options: Optional[ChunkingOptions] = None,
        timeout: int = 30,
        retries: int = 3,
    ) -> ChunkResponse:
        """Chunk a document synchronously.

        Args:
            content: The content to chunk.
            processing_options: Processing options for the chunking.
            timeout: The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds.
                After the timeout, raise a timeout error.
            retries: Number of times to retry the request in case of failures.

        Returns:
            ChunkResponse: Object containing the response from the API.

        Raises:
            AurelioAPIError: If the API request fails.
            ApiRateLimitError: If the rate limit is exceeded.
        """
        client_url = f"{self.base_url}/v1/chunk"

        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )
        response = None
        for attempt in range(1, retries + 1):
            try:
                response = requests.post(
                    client_url,
                    json=payload.model_dump(),
                    headers=self.headers,
                    timeout=timeout,
                )
                if response.status_code == 200:
                    return ChunkResponse(**response.json())
                elif response.status_code == 429:
                    raise ApiRateLimitError(
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
                elif response.status_code >= 500:
                    if attempt == retries:
                        raise ApiError(
                            message=response.text,
                            status_code=response.status_code,
                            base_url=self.base_url,
                        )
                    else:
                        logger.debug(
                            f"Retrying due to server error (attempt {attempt}): "
                            f"{response.text}"
                        )
                        continue  # Retry
                else:
                    try:
                        error_content = response.json()
                    except Exception:
                        error_content = response.text
                    raise ApiError(
                        message=error_content,
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
            except ApiRateLimitError as e:
                raise e
            except Exception as e:
                if attempt == retries:
                    raise ApiError(message=str(e), base_url=self.base_url) from e
                else:
                    logger.debug(f"Retrying due to exception (attempt {attempt}): {e}")
                    continue  # Retry
        raise ApiError(
            message=f"Failed to get response after {retries} retries",
            base_url=self.base_url,
        )

    def extract_file(
        self,
        file: Optional[Union[IO[bytes], bytes]] = None,
        file_path: Optional[Union[str, pathlib.Path]] = None,
        quality: Literal["low", "high"] = "low",
        chunk: bool = True,
        wait: int = 30,
        polling_interval: int = POLLING_INTERVAL,
        retries: int = 3,
    ) -> ExtractResponse:
        """Process a document from a file synchronously.

        Args:
            file (Union[IO[bytes], bytes]): The file to extract text from (PDF, MP4).
            quality (Literal["low", "high"]): Processing quality of the document.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            polling_interval (int): Time between polling requests in seconds.
                Default is 5s, if polling_interval is 0, polling is disabled.
            retries: Number of times to retry the request in case of failures.
                Defaults to 3.

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

        fields = {
            "quality": str(quality),
            "chunk": str(chunk).lower(),
            "wait": str(wait),
        }
        initial_wait = WAIT_TIME_BEFORE_POLLING if polling_interval > 0 else wait
        fields["wait"] = str(initial_wait)

        if file_path:
            filename = pathlib.Path(file_path).name
            multipart_encoder = MultipartEncoder(
                fields={**fields, "file": (filename, open(file_path, "rb"))}
            )
        else:
            filename = getattr(file, "name", "document.pdf")
            multipart_encoder = MultipartEncoder(
                fields={**fields, "file": (filename, file)}
            )

        document_id = None
        response = None
        session_timeout = wait + 1 if wait > 0 else None

        for attempt in range(1, retries + 1):
            try:
                session_timeout = wait + 1 if wait > 0 else None
                response = requests.post(
                    client_url,
                    data=multipart_encoder,
                    headers={
                        **self.headers,
                        "Content-Type": multipart_encoder.content_type,
                    },
                    timeout=session_timeout,
                )

                if response.status_code == 200:
                    extract_response = ExtractResponse(**response.json())
                    document_id = extract_response.document.id
                elif response.status_code == 429:
                    raise ApiRateLimitError(
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
                elif response.status_code >= 500:
                    if attempt == retries:
                        raise ApiError(
                            message=response.text,
                            status_code=response.status_code,
                            base_url=self.base_url,
                        )
                    else:
                        logger.debug(
                            f"Retrying due to server error (attempt {attempt}): "
                            f"{response.text}"
                        )
                        continue  # Retry
                else:
                    try:
                        error_content = response.json()
                    except Exception:
                        error_content = response.text
                    raise ApiError(
                        message=error_content,
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
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
                return self.wait_for(
                    document_id=document_id,
                    wait=wait,
                    polling_interval=polling_interval,
                )
            except ApiRateLimitError as e:
                raise e
            except requests.exceptions.Timeout:
                if attempt == retries:
                    raise ApiTimeoutError(
                        timeout=session_timeout,
                        base_url=self.base_url,
                    ) from None
                else:
                    logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                    continue  # Retry
            except Exception as e:
                if attempt == retries:
                    raise ApiError(message=str(e), base_url=self.base_url) from e
                else:
                    logger.debug(f"Retrying due to exception (attempt {attempt}): {e}")
                    continue  # Retry
        raise ApiError(
            message=f"Failed to get response after {retries} retries",
            base_url=self.base_url,
        )

    def extract_url(
        self,
        url: str,
        quality: Literal["low", "high"],
        chunk: bool,
        wait: int = 30,
        polling_interval: int = POLLING_INTERVAL,
        retries: int = 3,
    ) -> ExtractResponse:
        """Process a document from a URL synchronously.

        Args:
            url (str): The URL of the document file to be processed.
            quality (Literal["low", "high"]): Processing quality of the document.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            polling_interval (int): Time between polling requests in seconds.
                Default is 5s, if polling_interval is 0, polling is disabled.
            retries: Number of times to retry the request in case of failures.

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
            ApiRateLimitError: If the rate limit is exceeded.
        """
        client_url = f"{self.base_url}/v1/extract/url"
        data = {
            "url": url,
            "quality": quality,
            "chunk": chunk,
            "wait": wait,
        }

        # If polling is enabled, use a short wait time (WAIT_TIME_BEFORE_POLLING)
        initial_wait = WAIT_TIME_BEFORE_POLLING if polling_interval > 0 else wait
        data["wait"] = initial_wait

        document_id = None
        response = None
        session_timeout = wait + 1 if wait > 0 else None

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(
                    client_url, data=data, headers=self.headers, timeout=session_timeout
                )

                if response.status_code == 200:
                    extract_response = ExtractResponse(**response.json())
                    document_id = extract_response.document.id
                elif response.status_code == 429:
                    raise ApiRateLimitError(
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
                elif response.status_code >= 500:
                    if attempt == retries:
                        raise ApiError(
                            message=response.text,
                            status_code=response.status_code,
                            base_url=self.base_url,
                        )
                    else:
                        logger.debug(
                            f"Retrying due to server error (attempt {attempt}): "
                            f"{response.text}"
                        )
                        continue  # Retry
                else:
                    try:
                        error_content = response.json()
                    except Exception:
                        error_content = response.text
                    raise ApiError(
                        message=error_content,
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )

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
                return self.wait_for(
                    document_id=document_id,
                    wait=wait,
                    polling_interval=polling_interval,
                )
            except ApiRateLimitError as e:
                raise e
            except requests.exceptions.Timeout:
                if attempt == retries:
                    raise ApiTimeoutError(
                        timeout=session_timeout,
                        base_url=self.base_url,
                    ) from None
                else:
                    logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                    continue  # Retry
            except Exception as e:
                if attempt == retries:
                    raise ApiError(
                        message=str(e),
                        base_url=self.base_url,
                    ) from e
                else:
                    logger.debug(f"Retrying due to exception (attempt {attempt}): {e}")
                    continue  # Retry
        raise ApiError(
            message=f"Failed to get response after {retries} retries",
            base_url=self.base_url,
        )

    def get_document(
        self, document_id: str, timeout: int = 30, retries: int = 3
    ) -> ExtractResponse:
        """
        Retrieves a processed document synchronously.

        Args:
            document_id (str): The ID of the document to retrieve.
            timeout: The timeout to keep open the connection to the client in
                seconds. Defaults to 30 seconds.
                After the timeout, raise a timeout error.
            retries: Number of times to retry the request in case of failures.
                Defaults to 3.

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/document/{document_id}"
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(
                    client_url, headers=self.headers, timeout=timeout
                )
                if response.status_code == 200:
                    return ExtractResponse(**response.json())
                elif response.status_code == 429:
                    raise ApiRateLimitError(
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
                elif response.status_code >= 500:
                    if attempt == retries:
                        raise ApiError(
                            message=response.text,
                            status_code=response.status_code,
                            base_url=self.base_url,
                        )
                    else:
                        logger.debug(
                            f"Retrying due to server error (attempt {attempt}): "
                            f"{response.text}"
                        )
                        continue  # Retry
                else:
                    try:
                        error_content = response.json()
                    except Exception:
                        error_content = response.text
                    raise ApiError(
                        message=error_content,
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
            except ApiRateLimitError as e:
                raise e
            except requests.exceptions.Timeout:
                if attempt == retries:
                    raise ApiTimeoutError(
                        timeout=timeout,
                        base_url=self.base_url,
                    ) from None
                else:
                    logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                    continue  # Retry
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Error on attempt {attempt}: {e}")
                    raise ApiError(message=str(e), base_url=self.base_url) from e
                else:
                    logger.debug(f"Retrying due to exception (attempt {attempt}): {e}")
                    continue  # Retry
        raise ApiError(
            message=f"Failed to get response after {retries} retries",
            base_url=self.base_url,
        )

    def wait_for(
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
        document_response = self.get_document(document_id=document_id)

        FINAL_STATES = ["completed", "failed"]
        timeout_reached = False
        end_time = start_time + wait if wait >= 0 else float("inf")

        while document_response.status not in FINAL_STATES and not timeout_reached:
            time.sleep(polling_interval)

            # Check for timeout
            if time.time() > end_time:
                timeout_reached = True
                logger.debug(
                    f"Timeout reached while waiting for document {document_id}"
                )
                break

            document_response = self.get_document(document_id=document_id)
            logger.debug(
                f"Polling document {document_id}: status={document_response.status}"
            )
        return document_response

    def embedding(
        self,
        input: Union[str, List[str]],
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
            retries: Number of times to retry the request in case of failures.
                Defaults to 3.

        Returns:
            EmbeddingResponse: An object containing the embedding response from the API.

        Raises:
            APIError: If the API request fails.
            APITimeoutError: If the request exceeds the specified timeout.
            ApiRateLimitError: If the rate limit is exceeded.
        """
        client_url = f"{self.base_url}/v1/embeddings"
        data = {"input": input, "model": model}

        for attempt in range(1, retries + 1):
            try:
                response = requests.post(
                    client_url, json=data, headers=self.headers, timeout=timeout
                )
                if response.status_code == 200:
                    return EmbeddingResponse(**response.json())
                elif response.status_code == 429:
                    raise ApiRateLimitError(
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
                elif response.status_code >= 500:
                    if attempt == retries:
                        raise ApiError(
                            message=response.text,
                            status_code=response.status_code,
                            base_url=self.base_url,
                        )
                    else:
                        logger.debug(
                            f"Retrying due to server error (attempt {attempt}): "
                            f"{response.text}"
                        )
                        continue  # Retry
                else:
                    try:
                        error_content = response.json()
                    except Exception:
                        error_content = response.text
                    raise ApiError(
                        message=error_content,
                        status_code=response.status_code,
                        base_url=self.base_url,
                    )
            except ApiRateLimitError as e:
                raise e
            except requests.exceptions.Timeout:
                if attempt == retries:
                    raise ApiTimeoutError(
                        timeout=timeout,
                        base_url=self.base_url,
                    ) from None
                else:
                    logger.debug(f"Timeout error on attempt {attempt}, retrying...")
                    continue  # Retry
            except Exception as e:
                if attempt == retries:
                    logger.error(f"Error on attempt {attempt}: {e}")
                    raise ApiError(
                        message=str(e),
                        base_url=self.base_url,
                    ) from e
                else:
                    logger.debug(f"Retrying due to exception (attempt {attempt}): {e}")
                    continue  # Retry
        raise ApiError(
            message=f"Failed to get response after {retries} retries",
            base_url=self.base_url,
        )
