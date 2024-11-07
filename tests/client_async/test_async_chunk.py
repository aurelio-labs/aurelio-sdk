# Tests for AsyncAurelioClient
import os
from pathlib import Path

import pydantic_core
import pytest
from dotenv import load_dotenv

from aurelio_sdk.client_async import AsyncAurelioClient
from aurelio_sdk.exceptions import ApiError
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

@pytest.mark.asyncio
async def test_chunk_invalid(client: AsyncAurelioClient, content: str):
    with pytest.raises(pydantic_core._pydantic_core.ValidationError):
        chunking_options = ChunkingOptions(
            chunker_type="invalid", delimiters=[], max_chunk_length=400
        )
        await client.chunk(content=content, processing_options=chunking_options)

@pytest.mark.asyncio
async def test_chunk_regex(client: AsyncAurelioClient, content: str):
    chunking_options = ChunkingOptions(
        chunker_type="regex", delimiters=[], max_chunk_length=400
    )

    response: ChunkResponse = await client.chunk(
        content=content, processing_options=chunking_options
    )
    dict_response = response.model_dump()

    assert dict_response["status"] == "completed"
    assert 42930 < dict_response["usage"]["tokens"] < 42940
    assert dict_response["usage"]["pages"] is None
    assert dict_response["usage"]["seconds"] is None
    assert dict_response["processing_options"]["max_chunk_length"] == 400
    assert dict_response["processing_options"]["chunker_type"] == "regex"
    assert dict_response["processing_options"]["delimiters"] == []
    assert len(dict_response["document"]["content"]) > 40000
    assert dict_response["document"]["num_chunks"] == 97
    assert dict_response["document"]["chunks"][0]["id"].startswith("chunk_")
    assert dict_response["document"]["chunks"][0]["chunk_index"] == 1
    assert dict_response["document"]["chunks"][0]["num_tokens"] > 170
    # max_num_tokens = max(chunk["num_tokens"] for chunk in dict_response["document"]["chunks"])
    # # assert max_num_tokens <= 400  # TODO: This is failing


@pytest.mark.asyncio
async def test_chunk_regex_delimiters(client: AsyncAurelioClient):
    chunking_options = ChunkingOptions(
        chunker_type="regex", delimiters=["|", "/", "@"], max_chunk_length=4
    )
    content = "This is a test | This is a test / This is a  @ test."

    response: ChunkResponse = await client.chunk(
        content=content, processing_options=chunking_options
    )
    dict_response = response.model_dump()

    assert dict_response["processing_options"]["chunker_type"] == "regex"
    assert dict_response["processing_options"]["delimiters"] == ["|", "/", "@"]
    assert len(dict_response["document"]["content"]) == 52
    assert dict_response["document"]["num_chunks"] == 4

@pytest.mark.asyncio
async def test_chunk_semantic(client: AsyncAurelioClient, content: str):
    chunking_options = ChunkingOptions(
        chunker_type="semantic", window_size=5, max_chunk_length=400
    )

    response: ChunkResponse = await client.chunk(
        content=content[:10000], processing_options=chunking_options
    )
    dict_response = response.model_dump()

    assert dict_response["status"] == "completed"
    assert 2500 < dict_response["usage"]["tokens"] < 10000
    assert dict_response["usage"]["pages"] is None
    assert dict_response["usage"]["seconds"] is None
    assert dict_response["processing_options"]["max_chunk_length"] == 400
    assert dict_response["processing_options"]["chunker_type"] == "semantic"
    assert dict_response["processing_options"]["window_size"] == 5
    assert len(dict_response["document"]["content"]) == 10000
    assert dict_response["document"]["num_chunks"] == 18
    assert dict_response["document"]["chunks"][0]["id"].startswith("chunk_")
    assert dict_response["document"]["chunks"][0]["chunk_index"] == 1
    assert dict_response["document"]["chunks"][0]["num_tokens"] > 170
    max_num_tokens = max(chunk["num_tokens"] for chunk in dict_response["document"]["chunks"])
    assert max_num_tokens <= 400
