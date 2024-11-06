# Tests for AsyncAurelioClient
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from aurelio_sdk.client_async import AsyncAurelioClient
from aurelio_sdk.schema import ChunkingOptions, ChunkResponse

load_dotenv()


# setup async client
@pytest.fixture
def client() -> AsyncAurelioClient:
    client = AsyncAurelioClient(
        api_key=os.environ["AURELIO_API_KEY"], base_url=os.environ["BASE_URL"]
    )
    return client


@pytest.fixture
def content():
    file_path = Path(__file__).parent.parent / "data" / "content.txt"
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pytest.skip(f"Content file not found at {file_path}")


# Test successful initialization
@pytest.mark.asyncio
async def test_async_client_initialization():
    client = AsyncAurelioClient(api_key="test_api_key")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"


# Test initialization without API key
def test_async_client_no_api_key():
    with pytest.raises(ValueError):
        AsyncAurelioClient(api_key="", base_url="https://api.aurelio.ai")


# Test chunk method success
@pytest.mark.asyncio
async def test_chunk_method_success(client: AsyncAurelioClient, content: str):
    chunking_options = ChunkingOptions(
        chunker_type="regex", delimiters=[], max_chunk_length=400
    )

    response_regex: ChunkResponse = await client.chunk(
        content=content, processing_options=chunking_options
    )

    assert response_regex.status == "completed"


# # Test chunk method API error
# @pytest.mark.asyncio
# async def test_chunk_method_api_error():
#     async def mock_json():
#         return {"error": "Invalid request"}

#     mock_response = MagicMock()
#     mock_response.status = 400
#     mock_response.json = mock_json

#     with patch(
#         "aiohttp.ClientSession.post",
#         return_value=asyncio.coroutine(lambda: mock_response),
#     ) as mock_post:
#         client = AsyncAurelioClient(api_key="test_api_key")
#         with pytest.raises(APIError):
#             await client.chunk(content="Test content")


# # Test chunk method timeout
# @pytest.mark.asyncio
# async def test_chunk_method_timeout():
#     with patch("aiohttp.ClientSession.post", side_effect=asyncio.TimeoutError):
#         client = AsyncAurelioClient(api_key="test_api_key")
#         with pytest.raises(APITimeoutError):
#             await client.chunk(content="Test content", timeout=1)


# # Test chunk method with processing options
# @pytest.mark.asyncio
# async def test_chunk_method_with_options():
#     mock_response_data = {
#         "status": "completed",
#         "usage": {"tokens": 150},
#         "processing_options": {
#             "chunker_type": "semantic",
#             "max_chunk_length": 500,
#             "window_size": 5,
#             "delimiters": [],
#         },
#         "document": {
#             "id": "doc_id",
#             "content": "Test content with options",
#             "source": "test_source",
#             "source_type": "text_plain",
#             "num_chunks": 2,
#             "metadata": {},
#             "chunks": [
#                 {
#                     "id": "chunk_id_1",
#                     "content": "Test chunk 1",
#                     "chunk_index": 0,
#                     "num_tokens": 75,
#                     "metadata": {},
#                 },
#                 {
#                     "id": "chunk_id_2",
#                     "content": "Test chunk 2",
#                     "chunk_index": 1,
#                     "num_tokens": 75,
#                     "metadata": {},
#                 },
#             ],
#         },
#     }

#     async def mock_json():
#         return mock_response_data

#     mock_response = MagicMock()
#     mock_response.status = 200
#     mock_response.json = mock_json

#     with patch(
#         "aiohttp.ClientSession.post",
#         return_value=asyncio.coroutine(lambda: mock_response),
#     ) as mock_post:
#         client = AsyncAurelioClient(api_key="test_api_key")
#         options = ChunkingOptions(
#             chunker_type="semantic", max_chunk_length=500, window_size=5
#         )
#         response = await client.chunk(
#             content="Test content with options", processing_options=options
#         )
#         assert response.processing_options.chunker_type == "semantic"
#         assert response.document.num_chunks == 2


# # Test chunk method handles invalid response
# @pytest.mark.asyncio
# async def test_chunk_method_invalid_response():
#     async def mock_json():
#         return {"invalid": "data"}

#     mock_response = MagicMock()
#     mock_response.status = 200
#     mock_response.json = mock_json

#     with patch(
#         "aiohttp.ClientSession.post",
#         return_value=asyncio.coroutine(lambda: mock_response),
#     ) as mock_post:
#         client = AsyncAurelioClient(api_key="test_api_key")
#         with pytest.raises(KeyError):
#             await client.chunk(content="Test content")


# # Test chunk method handles network error
# @pytest.mark.asyncio
# async def test_chunk_method_network_error():
#     with patch("aiohttp.ClientSession.post", side_effect=aiohttp.ClientError):
#         client = AsyncAurelioClient(api_key="test_api_key")
#         with pytest.raises(APIError):
#             await client.chunk(content="Test content")


# # Test chunk method with large content
# @pytest.mark.asyncio
# async def test_chunk_method_large_content():
#     large_content = "A" * 10000  # Large content string
#     mock_response_data = {
#         "status": "completed",
#         "usage": {"tokens": 5000},
#         "processing_options": {
#             "chunker_type": "regex",
#             "max_chunk_length": 400,
#             "window_size": 1,
#             "delimiters": [],
#         },
#         "document": {
#             "id": "doc_id",
#             "content": large_content,
#             "source": "test_source",
#             "source_type": "text_plain",
#             "num_chunks": 25,
#             "metadata": {},
#             "chunks": [],
#         },
#     }

#     async def mock_json():
#         return mock_response_data

#     mock_response = MagicMock()
#     mock_response.status = 200
#     mock_response.json = mock_json

#     with patch(
#         "aiohttp.ClientSession.post",
#         return_value=asyncio.coroutine(lambda: mock_response),
#     ) as mock_post:
#         client = AsyncAurelioClient(api_key="test_api_key")
#         response = await client.chunk(content=large_content)
#         assert response.document.num_chunks == 25


# # Test chunk method with invalid processing options
# @pytest.mark.asyncio
# async def test_chunk_method_invalid_options():
#     client = AsyncAurelioClient(api_key="test_api_key")
#     options = ChunkingOptions(chunker_type="invalid_type")
#     with pytest.raises(APIError):
#         await client.chunk(content="Test content", processing_options=options)


# # Test chunk method without content
# @pytest.mark.asyncio
# async def test_chunk_method_no_content():
#     client = AsyncAurelioClient(api_key="test_api_key")
#     with pytest.raises(TypeError):
#         await client.chunk()  # Missing required positional argument 'content'


# # Test chunk method with null content
# @pytest.mark.asyncio
# async def test_chunk_method_null_content():
#     client = AsyncAurelioClient(api_key="test_api_key")
#     with pytest.raises(TypeError):
#         await client.chunk(content=None)


# # Test chunk method with invalid timeout
# @pytest.mark.asyncio
# async def test_chunk_method_invalid_timeout():
#     client = AsyncAurelioClient(api_key="test_api_key")
#     with pytest.raises(ValueError):
#         await client.chunk(content="Test content", timeout=-1)


# # Test chunk method with extra headers
# @pytest.mark.asyncio
# async def test_chunk_method_extra_headers():
#     mock_response_data = {
#         "status": "completed",
#         "usage": {},
#         "processing_options": {},
#         "document": {
#             "id": "doc_id",
#             "content": "Test content",
#             "source": "test_source",
#             "source_type": "text_plain",
#             "num_chunks": 1,
#             "metadata": {},
#             "chunks": [],
#         },
#     }

#     async def mock_json():
#         return mock_response_data

#     def side_effect(*args, **kwargs):
#         headers = kwargs.get("headers")
#         assert "Authorization" in headers
#         assert headers["Authorization"] == "Bearer test_api_key"
#         mock_response = MagicMock()
#         mock_response.status = 200
#         mock_response.json = mock_json
#         return asyncio.coroutine(lambda: mock_response)

#     with patch("aiohttp.ClientSession.post", side_effect=side_effect) as mock_post:
#         client = AsyncAurelioClient(api_key="test_api_key")
#         response = await client.chunk(content="Test content")
#         assert response.status == "completed"


# # Test chunk method with custom base URL
# @pytest.mark.asyncio
# async def test_chunk_method_custom_base_url():
#     custom_url = "https://custom.api.aurelio.ai"
#     client = AsyncAurelioClient(api_key="test_api_key", base_url=custom_url)
#     assert client.base_url == custom_url


# # Test chunk method with empty response
# @pytest.mark.asyncio
# async def test_chunk_method_empty_response():
#     async def mock_json():
#         return {}

#     mock_response = MagicMock()
#     mock_response.status = 200
#     mock_response.json = mock_json

#     with patch(
#         "aiohttp.ClientSession.post",
#         return_value=asyncio.coroutine(lambda: mock_response),
#     ) as mock_post:
#         client = AsyncAurelioClient(api_key="test_api_key")
#         with pytest.raises(KeyError):
#             await client.chunk(content="Test content")


# # Test chunk method with unauthorized access
# @pytest.mark.asyncio
# async def test_chunk_method_unauthorized():
#     async def mock_json():
#         return {"error": "Unauthorized"}

#     mock_response = MagicMock()
#     mock_response.status = 401
#     mock_response.json = mock_json

#     with patch(
#         "aiohttp.ClientSession.post",
#         return_value=asyncio.coroutine(lambda: mock_response),
#     ) as mock_post:
#         client = AsyncAurelioClient(api_key="invalid_api_key")
#         with pytest.raises(APIError):
#             await client.chunk(content="Test content")
