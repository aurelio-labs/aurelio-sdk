import os
from typing import IO, Literal, Optional

import aiohttp
import requests

from aurelio_sdk.exceptions import AurelioAPIError
from aurelio_sdk.schema import (
    ChunkingOptions,
    ChunkRequestPayload,
    ChunkResponse,
    ExtractResponse,
)


class AurelioClient:
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
        """
        Chunk a document synchronously.

        :param content: The content to chunk.
        :param processing_options: Processing options for the chunking.
        :return: ChunkResponse object containing the response from the API.
        """
        url = f"{self.base_url}/v1/chunk"

        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )
        response = requests.post(url, json=payload.model_dump(), headers=self.headers)
        if response.status_code == 200:
            return ChunkResponse(**response.json())
        else:
            raise AurelioAPIError(response)

    def extract_file(
        self,
        file: IO[bytes],
        quality: Literal["low", "high"],
        chunk: bool,
        timeout: int,
    ) -> ExtractResponse:
        """
        Process a document from an uploaded file synchronously.

        :param file: The file to extract text from (PDF, MP4).
        :param quality: Processing quality of the document.
        :param chunk: Whether the document should be chunked.
        :param timeout: The timeout to keep open the connection to the client in
                seconds, defaults to 30 seconds, -1 means no timeout.
        :return: ExtractResponse object containing the response from the API.
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
        timeout: int,
    ) -> ExtractResponse:
        """
        Process a document from a URL synchronously.

        :param url: The URL of the document file.
        :param quality: Processing quality of the document, "low" or "high".
        :param chunk: Whether the document should be chunked.
        :param timeout: The timeout to keep open the connection to the client in
                seconds, defaults to 30 seconds, -1 means no timeout.
        :return: ExtractResponsePayload object containing the response from the API.
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
        Retrieve a processed document synchronously.

        :param document_id: The ID of the document to retrieve.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/document/{document_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return ExtractResponse(**response.json())
        else:
            raise AurelioAPIError(response)


class AsyncAurelioClient:
    def __init__(
        self, api_key: Optional[str] = None, base_url: str = "https://api.aurelio.ai"
    ):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()

        self.api_key = api_key or os.environ.get("AURELIO_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "set as AURELIO_API_KEY environment variable."
            )
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    async def chunk(
        self, content: str, processing_options: Optional[ChunkingOptions] = None
    ) -> ChunkResponse:
        """
        Asynchronously chunk a document.

        :param content: The content of the document to chunk.
        :param processing_options: Optional ChunkingOptions object containing processing options.
        :return: ChunkResponse object containing the response from the API.
        """
        url = f"{self.base_url}/v1/chunk"
        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )
        async with self.session.post(url, json=payload.model_dump()) as response:
            if response.status == 200:
                data = await response.json()
                return ChunkResponse(**data)
            else:
                error_content = await response.text()
                raise AurelioAPIError(
                    f"API request failed with status {response.status}: {error_content}"
                )

    # async def extract_file(
    #     self, payload: BodyProcessDocumentFileV1ExtractFilePost
    # ) -> ExtractResponse:
    #     """
    #     Asynchronously process a document from an uploaded file.

    #     :param payload: BodyProcessDocumentFileV1ExtractFilePost object containing the file and processing options.
    #     :return: ExtractResponsePayload object containing the response from the API.
    #     """
    #     url = f"{self.base_url}/v1/extract/file"
    #     data = aiohttp.FormData()
    #     data.add_field("file", payload.file)
    #     data.add_field("quality", payload.quality.value)
    #     data.add_field("chunk", str(payload.chunk))
    #     data.add_field("timeout", str(payload.timeout))
    #     async with self.session.post(url, data=data) as response:
    #         if response.status == 200:
    #             resp_data = await response.json()
    #             return ExtractResponse(**resp_data)
    #         else:
    #             raise AurelioAPIError(response)

    # async def extract_url(
    #     self, url:
    # ) -> ExtractResponse:
    #     """
    #     Asynchronously process a document from a URL.

    #     :param payload: BodyProcessUrlV1ExtractUrlPost object containing the URL and processing options.
    #     :return: ExtractResponsePayload object containing the response from the API.
    #     """
    #     url = f"{self.base_url}/v1/extract/url"
    #     data = {
    #         "url": payload.url,
    #         "quality": payload.quality.value,
    #         "chunk": payload.chunk,
    #         "timeout": payload.timeout,
    #     }
    #     async with self.session.post(url, data=data) as response:
    #         if response.status == 200:
    #             resp_data = await response.json()
    #             return ExtractResponse(**resp_data)
    #         else:
    #             raise AurelioAPIError(response)

    async def get_document(self, document_id: str) -> ExtractResponse:
        """
        Retrieve a processed document asynchronously.

        :param document_id: The ID of the document to retrieve.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/document/{document_id}"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return ExtractResponse(**data)
            else:
                raise AurelioAPIError(response)

    async def ingest(self, url_param: str):
        """
        Asynchronously trigger processing of a document from a URL.

        :param url_param: The URL of the document to process.
        :return: JSON response from the API.
        """
        url = f"{self.base_url}/ingest/{url_param}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise AurelioAPIError(response)
