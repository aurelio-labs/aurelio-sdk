import os
from typing import Optional

import requests

from aurelio_sdk.exceptions import AurelioAPIError
from aurelio_sdk.schema import (
    BodyProcessDocumentFileV1ExtractFilePost,
    BodyProcessUrlV1ExtractUrlPost,
    ChunkingOptions,
    ChunkRequestPayload,
    ChunkResponse,
    ExtractResponsePayload,
)


class AurelioClient:
    def __init__(
        self, api_key: Optional[str] = None, base_url: str = "https://api.aurelio.ai"
    ):
        self.base_url = base_url
        self.session = requests.Session()

        self.api_key = api_key or os.environ.get("AURELIO_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "set as AURELIO_API_KEY environment variable."
            )
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def chunk(
        self, content: str, processing_options: Optional[ChunkingOptions] = None
    ) -> ChunkResponse:
        """
        Chunk a document synchronously.

        :param payload: ChunkRequestPayload object containing the content and processing options.
        :return: ChunkResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/chunk"

        payload = ChunkRequestPayload(
            content=content, processing_options=processing_options
        )

        response = self.session.post(url, json=payload.model_dump())
        if response.status_code == 200:
            return ChunkResponse(**response.json())
        else:
            raise AurelioAPIError(response)

    def extract_file(
        self, payload: BodyProcessDocumentFileV1ExtractFilePost
    ) -> ExtractResponsePayload:
        """
        Process a document from an uploaded file synchronously.

        :param payload: BodyProcessDocumentFileV1ExtractFilePost object containing the file and processing options.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/file"
        files = {"file": payload.file}
        data = {
            "quality": payload.quality.value,
            "chunk": payload.chunk,
            "timeout": payload.timeout,
        }
        response = self.session.post(url, files=files, data=data)
        if response.status_code == 200:
            return ExtractResponsePayload(**response.json())
        else:
            raise AurelioAPIError(response)

    def extract_url(
        self, payload: BodyProcessUrlV1ExtractUrlPost
    ) -> ExtractResponsePayload:
        """
        Process a document from a URL synchronously.

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
        response = self.session.post(url, data=data)
        if response.status_code == 200:
            return ExtractResponsePayload(**response.json())
        else:
            raise AurelioAPIError(response)

    def get_document(self, document_id: str) -> ExtractResponsePayload:
        """
        Retrieve a processed document synchronously.

        :param document_id: The ID of the document to retrieve.
        :return: ExtractResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/extract/document/{document_id}"
        response = self.session.get(url)
        if response.status_code == 200:
            return ExtractResponsePayload(**response.json())
        else:
            raise AurelioAPIError(response)

    def ingest(self, url_param: str):
        """
        Trigger processing of a document from a URL.

        :param url_param: The URL of the document to process.
        :return: JSON response from the API.
        """
        url = f"{self.base_url}/ingest/{url_param}"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise AurelioAPIError(response)
