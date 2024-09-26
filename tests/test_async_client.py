import sys

sys.path.append(".")

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aurelio_sdk.client_async import AsyncAurelioClient
from aurelio_sdk.exceptions import AurelioAPIError
from aurelio_sdk.schema import ChunkResponse, ExtractResponse


@pytest.fixture
def client():
    return AsyncAurelioClient(api_key="test_api_key")


# @pytest.mark.asyncio
# async def test_chunk_success(client):
#     content = "Test content"
#     expected_data = {
#         "status": "completed",
#         "chunks": ["chunk1", "chunk2"],
#         "usage": {"characters_processed": 100},  # Added required field 'usage'
#         "processing_options": {},  # Added required field 'processing_options'
#         "document": {},  # Added required field 'document'
#     }
#     expected_response = ChunkResponse(**expected_data)

#     with patch("aiohttp.ClientSession.post") as mock_post:
#         mock_response = MagicMock()
#         mock_response.status = 200
#         mock_response.json = AsyncMock(
#             return_value=expected_data
#         )  # Use AsyncMock for async method
#         mock_post.return_value.__aenter__.return_value = mock_response

#         response = await client.chunk(content)

#     assert response.status == expected_response.status
#     assert response.chunks == expected_response.chunks


@pytest.mark.asyncio
async def test_chunk_api_error(client):
    content = "Test content"

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(
            return_value="Bad Request"
        )
        mock_post.return_value.__aenter__.return_value = mock_response

        with pytest.raises(AurelioAPIError):
            await client.chunk(content)


@pytest.mark.asyncio
async def test_extract_file_success(client):
    file = MagicMock()
    file.name = "document.pdf"
    quality = "high"
    chunk = True
    expected_data = {
        "status": "completed",
        "usage": {
            "tokens": 1000,
            "pages": 2,
            "seconds": 1,
        },
        "processing_options": {
            "chunk": True,
            "quality": "high",
        },
        "document": {
            "id": "doc_123",
            "content": "Extracted content from the document.",
            "source": "document.pdf",
            "source_type": "application/pdf",
            "num_chunks": 1,
            "metadata": {},
            "chunks": [
                {
                    "id": "chunk_1",
                    "content": "Chunked content.",
                    "chunk_index": 0,
                    "num_tokens": 50,
                    "metadata": {},
                }
            ],
        },
    }
    expected_response = ExtractResponse(**expected_data)

    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=expected_data)
        mock_post.return_value.__aenter__.return_value = mock_response

        response = await client.extract_file(file, quality, chunk)

    assert response.status == expected_response.status
    assert response.document.id == expected_response.document.id


# @pytest.mark.asyncio
# async def test_extract_file_api_error(client):
#     file = MagicMock()
#     file.name = "document.pdf"
#     quality = "high"
#     chunk = True

#     with patch("aiohttp.ClientSession.post") as mock_post:
#         mock_response = MagicMock()
#         mock_response.status = 500
#         mock_response.text = AsyncMock(
#             return_value="Internal Server Error"
#         )  # Use AsyncMock for async method
#         mock_post.return_value.__aenter__.return_value = mock_response

#         with pytest.raises(AurelioAPIError):
#             await client.extract_file(file, quality, chunk)


# @pytest.mark.asyncio
# async def test_extract_url_success(client):
#     url = "https://example.com/document.pdf"
#     quality = "low"
#     chunk = False
#     expected_data = {
#         "status": "completed",
#         "document_id": "doc456",
#         "usage": {},  # Added required field 'usage'
#         "processing_options": {},  # Added required field 'processing_options'
#         "document": {},  # Added required field 'document'
#     }
#     expected_response = ExtractResponse(**expected_data)

#     with patch("aiohttp.ClientSession.post") as mock_post:
#         mock_response = MagicMock()
#         mock_response.status = 200
#         mock_response.json = AsyncMock(
#             return_value=expected_data
#         )  # Use AsyncMock for async method
#         mock_post.return_value.__aenter__.return_value = mock_response

#         response = await client.extract_url(url, quality, chunk)

#     assert response.status == expected_response.status
#     assert response.document_id == expected_response.document_id


# @pytest.mark.asyncio
# async def test_get_document_success(client):
#     document_id = "doc123"
#     expected_data = {
#         "status": "completed",
#         "document_id": document_id,
#         "usage": {},  # Added required field 'usage'
#         "processing_options": {},  # Added required field 'processing_options'
#         "document": {},  # Added required field 'document'
#     }
#     expected_response = ExtractResponse(**expected_data)

#     with patch("aiohttp.ClientSession.get") as mock_get:
#         mock_response = MagicMock()
#         mock_response.status = 200
#         mock_response.json = AsyncMock(
#             return_value=expected_data
#         )  # Use AsyncMock for async method
#         mock_get.return_value.__aenter__.return_value = mock_response

#         response = await client.get_document(document_id)

#     assert response.status == expected_response.status
#     assert response.document_id == expected_response.document_id


# @pytest.mark.asyncio
# async def test_wait_for_document_completion_success(client):
#     document_id = "doc123"
#     responses = [
#         ExtractResponse(
#             status="pending",  # Changed status from 'processing' to 'pending'
#             document_id=document_id,
#             usage={},  # Added required field 'usage'
#             processing_options={},  # Added required field 'processing_options'
#             document={},  # Added required field 'document'
#         ),
#         ExtractResponse(
#             status="completed",
#             document_id=document_id,
#             usage={},  # Added required field 'usage'
#             processing_options={},  # Added required field 'processing_options'
#             document={},  # Added required field 'document'
#         ),
#     ]

#     with patch.object(client, "get_document", side_effect=responses):
#         response = await client.wait_for_document_completion(document_id, timeout=5)

#     assert response.status == "completed"
#     assert response.document_id == document_id


# @pytest.mark.asyncio
# async def test_wait_for_document_completion_timeout(client):
#     document_id = "doc123"
#     response_data = ExtractResponse(
#         status="pending",  # Changed status from 'processing' to 'pending'
#         document_id=document_id,
#         usage={},  # Added required field 'usage'
#         processing_options={},  # Added required field 'processing_options'
#         document={},  # Added required field 'document'
#     )

#     with patch.object(client, "get_document", return_value=response_data):
#         response = await client.wait_for_document_completion(document_id, timeout=1)

#     assert response.status == "pending"
#     assert response.document_id == document_id
