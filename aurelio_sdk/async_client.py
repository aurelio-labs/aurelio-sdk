import aiohttp

from .exceptions import AurelioAPIError
from .schema import (
    BodyProcessDocumentFileV1ExtractFilePost,
    BodyProcessUrlV1ExtractUrlPost,
    ChunkRequestPayload,
    ChunkResponsePayload,
    ExtractResponsePayload,
)


class AsyncAurelioClient:
    def __init__(self, base_url: str = "https://api.aurelio.ai"):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()

    async def chunk_document(
        self, payload: ChunkRequestPayload
    ) -> ChunkResponsePayload:
        """
        Asynchronously chunk a document.

        :param payload: ChunkRequestPayload object containing the content and processing options.
        :return: ChunkResponsePayload object containing the response from the API.
        """
        url = f"{self.base_url}/v1/chunk"
        async with self.session.post(url, json=payload.dict()) as response:
            if response.status == 200:
                data = await response.json()
                return ChunkResponsePayload(**data)
            else:
                raise AurelioAPIError(response)

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
