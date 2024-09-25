# from unittest.mock import AsyncMock, patch

# import aiohttp
# import pytest

# from aurelio_sdk.async_client import AsyncAurelioClient
# from aurelio_sdk.exceptions import AurelioAPIError
# from aurelio_sdk.schema import (
#     BodyProcessDocumentFileV1ExtractFilePost,
#     BodyProcessUrlV1ExtractUrlPost,
#     ChunkRequestPayload,
#     ChunkResponse,
#     ExtractResponse,
# )


# @pytest.fixture
# async def async_client():
#     client = AsyncAurelioClient()
#     yield client
#     await client.session.close()


# @pytest.mark.asyncio
# async def test_chunk_document_success(async_client):
#     payload = ChunkRequestPayload(content="Test content")
#     mock_response = {
#         "status": "completed",
#         "usage": {"tokens": 100, "pages": 1, "seconds": 2},
#         "message": None,
#         "processing_options": {
#             "max_chunk_length": 400,
#             "chunker_type": "regex",
#             "window_size": 1,
#             "delimiters": [],
#         },
#         "document": {
#             "id": "doc123",
#             "content": "Test content",
#             "source": "source",
#             "source_type": "text/plain",
#             "num_chunks": 1,
#             "metadata": {},
#         },
#     }

#     with patch.object(
#         aiohttp.ClientSession, "post", new_callable=AsyncMock
#     ) as mock_post:
#         mock_post.return_value.__aenter__.return_value.status = 200
#         mock_post.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value=mock_response
#         )

#         response = await async_client.chunk_document(payload)
#         assert isinstance(response, ChunkResponse)
#         assert response.status == "completed"


# @pytest.mark.asyncio
# async def test_chunk_document_failure(async_client):
#     payload = ChunkRequestPayload(content="Test content")

#     with patch.object(
#         aiohttp.ClientSession, "post", new_callable=AsyncMock
#     ) as mock_post:
#         mock_post.return_value.__aenter__.return_value.status = 422
#         mock_post.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value={"detail": "Validation error"}
#         )

#         with pytest.raises(AurelioAPIError):
#             await async_client.chunk_document(payload)


# @pytest.mark.asyncio
# async def test_extract_file_success(async_client):
#     payload = BodyProcessDocumentFileV1ExtractFilePost(
#         file=b"dummy_data", quality="high", chunk=True, timeout=30
#     )
#     mock_response = {
#         "status": "completed",
#         "usage": {"tokens": 200, "pages": 2, "seconds": 4},
#         "message": None,
#         "processing_options": {"chunk": True, "quality": "high"},
#         "document": {
#             "id": "doc456",
#             "content": "Extracted content",
#             "source": "uploaded_file",
#             "source_type": "application/pdf",
#             "num_chunks": 2,
#             "metadata": {},
#         },
#     }

#     with patch.object(
#         aiohttp.ClientSession, "post", new_callable=AsyncMock
#     ) as mock_post:
#         mock_post.return_value.__aenter__.return_value.status = 200
#         mock_post.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value=mock_response
#         )

#         response = await async_client.extract_file(payload)
#         assert isinstance(response, ExtractResponse)
#         assert response.status == "completed"


# @pytest.mark.asyncio
# async def test_extract_file_failure(async_client):
#     payload = BodyProcessDocumentFileV1ExtractFilePost(
#         file=b"dummy_data", quality="high", chunk=True, timeout=30
#     )

#     with patch.object(
#         aiohttp.ClientSession, "post", new_callable=AsyncMock
#     ) as mock_post:
#         mock_post.return_value.__aenter__.return_value.status = 422
#         mock_post.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value={"detail": "Validation error"}
#         )

#         with pytest.raises(AurelioAPIError):
#             await async_client.extract_file(payload)


# @pytest.mark.asyncio
# async def test_extract_url_success(async_client):
#     payload = BodyProcessUrlV1ExtractUrlPost(
#         url="https://example.com/document.pdf", quality="low", chunk=False, timeout=30
#     )
#     mock_response = {
#         "status": "completed",
#         "usage": {"tokens": 150, "pages": 1, "seconds": 3},
#         "message": None,
#         "processing_options": {"chunk": False, "quality": "low"},
#         "document": {
#             "id": "doc789",
#             "content": "Extracted content from URL",
#             "source": "https://example.com/document.pdf",
#             "source_type": "application/pdf",
#             "num_chunks": 1,
#             "metadata": {},
#         },
#     }

#     with patch.object(
#         aiohttp.ClientSession, "post", new_callable=AsyncMock
#     ) as mock_post:
#         mock_post.return_value.__aenter__.return_value.status = 200
#         mock_post.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value=mock_response
#         )

#         response = await async_client.extract_url(payload)
#         assert isinstance(response, ExtractResponse)
#         assert response.status == "completed"


# @pytest.mark.asyncio
# async def test_extract_url_failure(async_client):
#     payload = BodyProcessUrlV1ExtractUrlPost(
#         url="https://example.com/document.pdf", quality="low", chunk=False, timeout=30
#     )

#     with patch.object(
#         aiohttp.ClientSession, "post", new_callable=AsyncMock
#     ) as mock_post:
#         mock_post.return_value.__aenter__.return_value.status = 422
#         mock_post.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value={"detail": "Validation error"}
#         )

#         with pytest.raises(AurelioAPIError):
#             await async_client.extract_url(payload)


# @pytest.mark.asyncio
# async def test_get_document_success(async_client):
#     document_id = "doc123"
#     mock_response = {
#         "status": "completed",
#         "usage": {"tokens": 100, "pages": 1, "seconds": 2},
#         "message": None,
#         "processing_options": {"chunk": True, "quality": "high"},
#         "document": {
#             "id": "doc123",
#             "content": "Test content",
#             "source": "source",
#             "source_type": "text/plain",
#             "num_chunks": 1,
#             "metadata": {},
#         },
#     }

#     with patch.object(aiohttp.ClientSession, "get", new_callable=AsyncMock) as mock_get:
#         mock_get.return_value.__aenter__.return_value.status = 200
#         mock_get.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value=mock_response
#         )

#         response = await async_client.get_document(document_id)
#         assert isinstance(response, ExtractResponse)
#         assert response.status == "completed"


# @pytest.mark.asyncio
# async def test_get_document_failure(async_client):
#     document_id = "invalid_doc_id"

#     with patch.object(aiohttp.ClientSession, "get", new_callable=AsyncMock) as mock_get:
#         mock_get.return_value.__aenter__.return_value.status = 422
#         mock_get.return_value.__aenter__.return_value.json = AsyncMock(
#             return_value={"detail": "Document not found"}
#         )

#         with pytest.raises(AurelioAPIError):
#             await async_client.get_document(document_id)
