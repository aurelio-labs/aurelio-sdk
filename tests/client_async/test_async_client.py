# Tests for AsyncAurelioClient
import os

import pytest
from dotenv import load_dotenv

from aurelio_sdk.client_async import AsyncAurelioClient
from aurelio_sdk.exceptions import ApiError
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
    # Temporarily remove API key from environment
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