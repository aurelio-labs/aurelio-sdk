# Tests for AsyncAurelioClient
import asyncio
import os
from pathlib import Path

import pytest
from aioresponses import aioresponses
from dotenv import load_dotenv

from aurelio_sdk.client_async import AsyncAurelioClient
from aurelio_sdk.exceptions import ApiError, ApiRateLimitError
from aurelio_sdk.schema import ChunkingOptions

load_dotenv()


# setup async client
@pytest.fixture
def client() -> AsyncAurelioClient:
    client = AsyncAurelioClient(
        api_key=os.environ["AURELIO_API_KEY"], base_url=os.environ["BASE_URL"]
    )
    return client


@pytest.fixture
def no_api_key_env():
    """Temporarily remove API key from environment"""
    original_key = os.environ.get("AURELIO_API_KEY")
    os.environ["AURELIO_API_KEY"] = ""
    yield
    if original_key is not None:
        os.environ["AURELIO_API_KEY"] = original_key
    else:
        del os.environ["AURELIO_API_KEY"]


@pytest.mark.asyncio
async def test_async_client_initialization():
    client = AsyncAurelioClient(api_key="test_api_key")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"


def test_async_client_no_api_key(no_api_key_env):
    with pytest.raises(ValueError):
        AsyncAurelioClient(api_key="", base_url="https://api.aurelio.ai")


@pytest.mark.asyncio
async def test_async_client_unauthorized():
    client = AsyncAurelioClient(api_key="test_api_key")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"
    with pytest.raises(ApiError):
        await client.chunk(content="test", processing_options=ChunkingOptions())


@pytest.mark.asyncio
async def test_async_client_empty_base_url():
    client = AsyncAurelioClient(api_key="test_api_key", base_url="")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"


# SJ - as a placeholder for now
# @pytest.mark.asyncio
# async def test_async_client_rate_limit_error(client: AsyncAurelioClient):
#     with pytest.raises(ApiRateLimitError):
#         if client.base_url not in [
#             "https://api.aurelio.ai",
#             "https://staging.api.aurelio.ai",
#         ]:
#             # Rate limits are available only in the cloud environments
#             # This is for local testing
#             client = AsyncAurelioClient(
#                 api_key=os.environ["AURELIO_API_KEY_PRODUCTION"],
#                 base_url=os.environ["BASE_URL_PRODUCTION"],
#             )

#         file_path = Path(__file__).parent.parent / "data" / "test_pdf.pdf"
#         tasks: set[asyncio.Task] = set()
#         for _ in range(30):
#             tasks.add(
#                 asyncio.create_task(
#                     client.extract_file(
#                         file_path=file_path,
#                         quality="low",
#                         chunk=False,
#                         wait=-1,
#                         polling_interval=2,
#                     )
#                 )
#             )
#         try:
#             done, pending = await asyncio.wait(
#                 tasks, return_when=asyncio.FIRST_EXCEPTION
#             )
#             for task in done:
#                 exception = task.exception()
#                 if isinstance(exception, ApiRateLimitError):
#                     tasks.remove(task)
#                     raise exception  # Re-raise to be caught by pytest.raises
#                 elif exception:
#                     tasks.remove(task)
#                     raise exception
#                 else:
#                     tasks.remove(task)
#         finally:
#             for task in pending:
#                 task.cancel()
#             # Await canceled tasks to suppress CancelledError
#             await asyncio.gather(*pending, return_exceptions=True)


# @pytest.mark.asyncio
# async def test_async_client_retry_on_server_error(client):
#     """Test that the client retries on 5xx server errors"""
#     with aioresponses() as mocked:
#         # Mock 3 consecutive 500 errors
#         for _ in range(3):
#             mocked.post(
#                 f"{client.base_url}/v1/extract/url",
#                 status=500,
#                 body="Internal Server Error",
#             )

#         with pytest.raises(ApiError) as exc_info:
#             await client.extract_url(
#                 url="https://123.com", quality="low", chunk=True, wait=-1
#             )

#         assert "Internal Server Error" in str(exc_info.value)
