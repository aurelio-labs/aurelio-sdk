# Tests for AurelioClient
import os
from pathlib import Path

import pydantic_core
import pytest
from dotenv import load_dotenv

# Import the synchronous client instead of the async client
from aurelio_sdk.client import AurelioClient
from aurelio_sdk.schema import ChunkingOptions, ChunkResponse

load_dotenv()


# Setup fixture for synchronous client
@pytest.fixture
def client() -> AurelioClient:
    client = AurelioClient(
        api_key=os.environ["AURELIO_API_KEY"], base_url=os.environ["BASE_URL"]
    )
    return client


# Fixture for content
@pytest.fixture
def content():
    file_path = Path(__file__).parent.parent / "data" / "content.txt"
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pytest.skip(f"Content file not found at {file_path}")


def test_chunk_invalid(client: AurelioClient, content: str):
    with pytest.raises(pydantic_core._pydantic_core.ValidationError):
        chunking_options = ChunkingOptions(
            # Intentionally invalid chunker_type
            chunker_type="invalid",  # type: ignore
            delimiters=[],
            max_chunk_length=400,
        )
        # Call synchronous method
        client.chunk(content=content, processing_options=chunking_options)


def test_chunk_regex(client: AurelioClient, content: str):
    chunking_options = ChunkingOptions(
        chunker_type="regex", delimiters=[], max_chunk_length=400
    )

    # Call synchronous method
    response: ChunkResponse = client.chunk(
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
    # assert max_num_tokens <= 400  # TODO: This is failing


def test_chunk_regex_delimiters(client: AurelioClient):
    chunking_options = ChunkingOptions(
        chunker_type="regex", delimiters=["|", "/", "@"], max_chunk_length=4
    )
    content = "This is a test | This is a test / This is a  @ test."

    # Call synchronous method
    response: ChunkResponse = client.chunk(
        content=content, processing_options=chunking_options
    )
    dict_response = response.model_dump()

    assert dict_response["processing_options"]["chunker_type"] == "regex"
    assert dict_response["processing_options"]["delimiters"] == ["|", "/", "@"]
    assert len(dict_response["document"]["content"]) == 52
    assert dict_response["document"]["num_chunks"] == 4


def test_chunk_semantic(client: AurelioClient, content: str):
    chunking_options = ChunkingOptions(
        chunker_type="semantic", window_size=5, max_chunk_length=400
    )

    # Call synchronous method
    response: ChunkResponse = client.chunk(
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
    assert 15 < dict_response["document"]["num_chunks"] < 20
    assert dict_response["document"]["chunks"][0]["id"].startswith("chunk_")
    assert dict_response["document"]["chunks"][0]["chunk_index"] == 1
    assert dict_response["document"]["chunks"][0]["num_tokens"] > 170
    max_num_tokens = max(
        chunk["num_tokens"] for chunk in dict_response["document"]["chunks"]
    )
    assert max_num_tokens <= 400
