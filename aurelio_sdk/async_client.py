import os
from typing import Optional

import aiohttp

from .exceptions import AurelioAPIError
from .schema import (
    BodyProcessDocumentFileV1ExtractFilePost,
    BodyProcessUrlV1ExtractUrlPost,
    ChunkingOptions,
    ChunkRequestPayload,
    ChunkResponse,
    ExtractResponsePayload,
)


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

    async def extract_file(
        self, payload: BodyProcessDocumentFileV1ExtractFilePost
    ) -> ExtractResponsePayload:
        """
        Asynchronously process a document from an uploaded file.

        :param payload: BodyProcessDocumentFileV1ExtractFilePost object containing the file and processing options.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/file"
        data = aiohttp.FormData()
        data.add_field("file", payload.file)
        data.add_field("quality", payload.quality.value)
        data.add_field("chunk", str(payload.chunk))
        data.add_field("timeout", str(payload.timeout))
        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                resp_data = await response.json()
                return ExtractResponsePayload(**resp_data)
            else:
                raise AurelioAPIError(response)

    async def extract_url(
        self, payload: BodyProcessUrlV1ExtractUrlPost
    ) -> ExtractResponsePayload:
        """
        Asynchronously process a document from a URL.

        :param payload: BodyProcessUrlV1ExtractUrlPost object containing the URL and processing options.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/url"
        data = {
            "url": payload.url,
            "quality": payload.quality.value,
            "chunk": payload.chunk,
            "timeout": payload.timeout,
        }
        async with self.session.post(url, data=data) as response:
            if response.status == 200:
                resp_data = await response.json()
                return ExtractResponsePayload(**resp_data)
            else:
                raise AurelioAPIError(response)

    async def get_document(self, document_id: str) -> ExtractResponsePayload:
        """
        Retrieve a processed document asynchronously.

        :param document_id: The ID of the document to retrieve.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/document/{document_id}"
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return ExtractResponsePayload(**data)
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
