import logging
import os
import time
from typing import IO, Annotated, List, Literal, Optional, Union

import requests

from aurelio_sdk.const import POLLING_INTERVAL, WAIT_TIME_BEFORE_POLLING
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
        self.base_url = base_url

        self.api_key = api_key or os.environ.get("AURELIO_API_KEY")
        if debug:
            logger.setLevel(logging.DEBUG)

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
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise APIError(response.status_code, error_content)

    def extract_file(
        self,
        file: Union[IO[bytes], bytes],
        quality: Literal["low", "high"],
        chunk: bool,
        wait: int = 30,
        enable_polling: bool = True,
    ) -> ExtractResponse:
        """Process a document from a file asynchronously.

        Args:
            file (Union[IO[bytes], bytes]): The file to extract text from (PDF, MP4).
            quality (Literal["low", "high"]): Processing quality of the document.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            enable_polling (bool): If False, disables polling for document completion.
                Instead, maintains a continuous connection to the API until the
                document is completed. Default is True (polling is enabled).

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
        """
        client_url = f"{self.base_url}/v1/extract/file"

        filename = getattr(file, "name", "document.pdf")

        files = {"file": (filename, file)}
        data = {
            "quality": quality,
            "chunk": chunk,
            "wait": wait,
        }

        # If polling is enabled, use a short wait time (WAIT_TIME_BEFORE_POLLING)
        if enable_polling:
            data["wait"] = WAIT_TIME_BEFORE_POLLING

        document_id = None
        try:
            session_timeout = wait + 1 if wait > 0 else None
            response = requests.post(
                client_url,
                files=files,
                data=data,
                headers=self.headers,
                timeout=session_timeout,
            )

            if response.status_code == 200:
                extract_response = ExtractResponse(**response.json())
                document_id = extract_response.document.id
            else:
                try:
                    error_content = response.json()
                except Exception:
                    error_content = response.text
                raise APIError(response.status_code, error_content)

            if wait == 0:
                return extract_response

            # If the document is already processed or polling is disabled,
            # return the response
            if extract_response.status in ["completed", "failed"] or not enable_polling:
                return extract_response

            # Wait for the document to complete processing
            return self.wait_for(document_id=document_id, wait=wait)
        except requests.exceptions.Timeout:
            raise APITimeoutError(document_id=document_id) from None
        except Exception as e:
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise APIError(response.status_code, error_content) from e

    def extract_url(
        self,
        url: str,
        quality: Literal["low", "high"],
        chunk: bool,
        wait: int = 30,
        enable_polling: bool = True,
    ) -> ExtractResponse:
        """Process a document from a URL synchronously.

        Args:
            url (str): The URL of the document file to be processed.
            quality (Literal["low", "high"]): Processing quality of the document.
            chunk (bool): Whether the document should be chunked.
            wait (int): Time to wait for document completion in seconds. Default is 30.
                If set to -1, waits until completion. If the wait time is exceeded,
                returns the document ID with a "pending" status.
            enable_polling (bool): If False, disables polling for document completion.
                Instead, maintains a continuous connection to the API until the
                document is completed. Default is True (polling is enabled).

        Returns:
            ExtractResponse: An object containing the response from the API, including
            the processed document information and status.

        Raises:
            APITimeoutError: If the request times out.
            APIError: If there's an error in the API response.
        """
        client_url = f"{self.base_url}/v1/extract/url"
        data = {
            "url": url,
            "quality": quality,
            "chunk": chunk,
            "wait": wait,
        }

        # If polling is enabled, use a short wait time (WAIT_TIME_BEFORE_POLLING)
        if enable_polling:
            data["wait"] = WAIT_TIME_BEFORE_POLLING

        document_id = None
        try:
            session_timeout = wait + 1 if wait > 0 else None
            response = requests.post(
                client_url, data=data, headers=self.headers, timeout=session_timeout
            )

            if response.status_code == 200:
                extract_response = ExtractResponse(**response.json())
                document_id = extract_response.document.id
            else:
                try:
                    error_content = response.json()
                except Exception:
                    error_content = response.text
                raise APIError(response.status_code, error_content)

            if wait == 0:
                return extract_response

            # If the document is already processed or polling is disabled,
            # return the response
            if extract_response.status in ["completed", "failed"] or not enable_polling:
                return extract_response

            # Wait for the document to complete processing
            return self.wait_for(document_id=document_id, wait=wait)
        except requests.exceptions.Timeout:
            raise APITimeoutError(document_id=document_id) from None
        except Exception as e:
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise APIError(response.status_code, error_content) from e

    def get_document(self, document_id: str, timeout: int = 30) -> ExtractResponse:
        """
        Retrieves a processed document synchronously.

        Args:
            document_id (str): The ID of the document to retrieve.

        Returns:
            ExtractResponse: An object containing the response from the API.
        """
        client_url = f"{self.base_url}/v1/extract/document/{document_id}"
        try:
            response = requests.get(client_url, headers=self.headers, timeout=timeout)
            if response.status_code == 200:
                return ExtractResponse(**response.json())
            else:
                try:
                    error_content = response.json()
                except Exception:
                    error_content = response.text
                raise APIError(response.status_code, error_content)
        except requests.exceptions.Timeout:
            raise APITimeoutError(document_id=document_id) from None
        except Exception as e:
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise APIError(response.status_code, error_content) from e

    def wait_for(self, document_id: str, wait: int = 300) -> ExtractResponse:
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
            time.sleep(POLLING_INTERVAL)

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
        try:
            response = requests.post(
                client_url, json=data, headers=self.headers, timeout=timeout
            )
            if response.status_code == 200:
                return EmbeddingResponse(**response.json())
            else:
                try:
                    error_content = response.json()
                except Exception:
                    error_content = response.text
                raise APIError(response.status_code, error_content)
        except requests.exceptions.Timeout:
            raise APITimeoutError() from None
        except Exception as e:
            try:
                error_content = response.json()
            except Exception:
                error_content = response.text
            raise APIError(response.status_code, error_content) from e
