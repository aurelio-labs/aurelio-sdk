# Tests for AsyncAurelioClient
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from aurelio_sdk.client_async import AsyncAurelioClient
from aurelio_sdk.schema import ExtractResponse

load_dotenv()


# setup async client
@pytest.fixture
def client() -> AsyncAurelioClient:
    client = AsyncAurelioClient(
        api_key=os.environ["AURELIO_API_KEY"], base_url=os.environ["BASE_URL"]
    )
    return client


# @pytest.mark.asyncio
# async def test_extract_pdf_file_wait_5_seconds(client: AsyncAurelioClient):
#     file_path = Path(__file__).parent.parent / "data" / "test_pdf.pdf"

#     response: ExtractResponse = await client.extract_file(
#         file_path=file_path, quality="low", chunk=True, wait=5, polling_interval=1
#     )

#     dict_response = response.model_dump()

#     # Status
#     assert dict_response["status"] == "pending"

#     # Processing options
#     assert dict_response["processing_options"]["quality"] == "low"
#     assert dict_response["processing_options"]["chunk"] is True

#     # Document
#     assert dict_response["document"]["id"].startswith("doc_")

# @pytest.mark.asyncio
# async def test_extract_pdf_file_from_file_path(client: AsyncAurelioClient):
#     file_path = Path(__file__).parent.parent / "data" / "test_pdf.pdf"

#     response: ExtractResponse = await client.extract_file(
#         file_path=file_path, quality="low", chunk=True, wait=-1, polling_interval=2
#     )

#     dict_response = response.model_dump()

#     # Status
#     assert dict_response["status"] == "completed"

#     # Usage
#     assert 11690 < dict_response["usage"]["tokens"] < 11700
#     assert dict_response["usage"]["pages"] == 7
#     assert dict_response["usage"]["seconds"] is None

#     # Processing options
#     assert dict_response["processing_options"]["quality"] == "low"
#     assert dict_response["processing_options"]["chunk"] is True

#     # Document
#     assert dict_response["document"]["id"].startswith("doc_")
#     assert len(dict_response["document"]["content"]) > 11000
#     assert dict_response["document"]["num_chunks"] == 43
#     assert dict_response["document"]["chunks"][0]["id"].startswith("chunk_")
#     assert dict_response["document"]["chunks"][0]["chunk_index"] == 1
#     assert dict_response["document"]["chunks"][0]["num_tokens"] > 170
#     max_num_tokens = max(chunk["num_tokens"] for chunk in dict_response["document"]["chunks"])
#     assert max_num_tokens <= 500


# @pytest.mark.asyncio
# async def test_extract_pdf_file_no_chunks(client: AsyncAurelioClient):
#     file_path = Path(__file__).parent.parent / "data" / "test_pdf.pdf"

#     response: ExtractResponse = await client.extract_file(
#         file_path=file_path, quality="low", chunk=False, wait=-1, polling_interval=2
#     )

#     dict_response = response.model_dump()

#     # Status
#     assert dict_response["status"] == "completed"

#     # Usage
#     # assert dict_response["usage"]["tokens"] is None #TODO: this should be None, if chunk is False
#     assert dict_response["usage"]["pages"] == 7
#     assert dict_response["usage"]["seconds"] is None

#     # Processing options
#     assert dict_response["processing_options"]["quality"] == "low"
#     assert dict_response["processing_options"]["chunk"] is False

#     # Document
#     assert dict_response["document"]["num_chunks"] == 0
#     assert dict_response["document"]["chunks"] == []


# @pytest.mark.asyncio
# async def test_extract_pdf_file_from_bytes(client: AsyncAurelioClient):
#     file_path = Path(__file__).parent.parent / "data" / "test_pdf.pdf"
#     with open(file_path, "rb") as f:
#         file_bytes = f.read()

#     response: ExtractResponse = await client.extract_file(
#         file=file_bytes, quality="low", chunk=False, wait=-1, polling_interval=2
#     )

#     dict_response = response.model_dump()

#     # Status
#     assert dict_response["status"] == "completed"

#     # Usage
#     assert dict_response["usage"]["pages"] == 7
#     assert dict_response["usage"]["seconds"] is None

#     # Processing options
#     assert dict_response["processing_options"]["quality"] == "low"
#     assert dict_response["processing_options"]["chunk"] is False

#     # Document
#     assert dict_response["document"]["num_chunks"] == 0
#     assert dict_response["document"]["chunks"] == []


@pytest.mark.asyncio
async def test_extract_video_file_from_file_path(client: AsyncAurelioClient):
    file_path = Path(__file__).parent.parent / "data" / "test_video.mp4"

    response: ExtractResponse = await client.extract_file(
        file_path=file_path, quality="low", chunk=True, wait=-1, polling_interval=10
    )

    dict_response = response.model_dump()

    # Status
    assert dict_response["status"] == "completed"

    # Usage
    assert 830 < dict_response["usage"]["tokens"] < 840
    assert dict_response["usage"]["pages"] is None
    assert dict_response["usage"]["seconds"] == 291

    # Processing options
    assert dict_response["processing_options"]["quality"] == "low"
    assert dict_response["processing_options"]["chunk"] is True

    # Document
    assert dict_response["document"]["id"].startswith("doc_")
    assert len(dict_response["document"]["content"]) > 840
    assert dict_response["document"]["num_chunks"] == 3
    assert dict_response["document"]["chunks"][0]["id"].startswith("chunk_")
    assert dict_response["document"]["chunks"][0]["chunk_index"] == 1
    assert dict_response["document"]["chunks"][0]["num_tokens"] > 200
    max_num_tokens = max(
        chunk["num_tokens"] for chunk in dict_response["document"]["chunks"]
    )
    assert max_num_tokens <= 500
    print(dict_response["document"]["metadata"])
    assert dict_response["document"]["metadata"]["start_time"] == 0
    assert dict_response["document"]["metadata"]["end_time"] == 99


@pytest.mark.asyncio
async def test_extract_pdf_file_from_url(client: AsyncAurelioClient):
    url = "https://arxiv.org/pdf/2408.15291"

    response: ExtractResponse = await client.extract_url(
        url=url, quality="low", chunk=True, wait=-1, polling_interval=5
    )

    dict_response = response.model_dump()

    # Status
    assert dict_response["status"] == "completed"

    # Usage
    assert 11870 < dict_response["usage"]["tokens"] < 11890
    assert dict_response["usage"]["pages"] == 8
    assert dict_response["usage"]["seconds"] is None

    # Processing options
    assert dict_response["processing_options"]["quality"] == "low"
    assert dict_response["processing_options"]["chunk"] is True

    # Document
    assert dict_response["document"]["id"].startswith("doc_")
    assert len(dict_response["document"]["content"]) > 11000
    assert dict_response["document"]["num_chunks"] == 43
    assert dict_response["document"]["chunks"][0]["id"].startswith("chunk_")
    assert dict_response["document"]["chunks"][0]["chunk_index"] == 1
    assert dict_response["document"]["chunks"][0]["num_tokens"] > 270
    max_num_tokens = max(
        chunk["num_tokens"] for chunk in dict_response["document"]["chunks"]
    )
    assert max_num_tokens <= 500


@pytest.mark.asyncio
async def test_extract_pdf_file_from_url_chunk_false(client: AsyncAurelioClient):
    url = "https://arxiv.org/pdf/2408.15291"

    response: ExtractResponse = await client.extract_url(
        url=url, quality="low", chunk=False, wait=-1, polling_interval=5
    )

    dict_response = response.model_dump()

    # Status
    assert dict_response["status"] == "completed"

    # Usage
    assert dict_response["usage"]["tokens"] is None
    assert dict_response["usage"]["pages"] == 8
    assert dict_response["usage"]["seconds"] is None

    # Processing options
    assert dict_response["processing_options"]["quality"] == "low"
    assert dict_response["processing_options"]["chunk"] is False

    # Document
    assert dict_response["document"]["id"].startswith("doc_")
    assert len(dict_response["document"]["content"]) > 11000
    assert dict_response["document"]["num_chunks"] == 0
    assert dict_response["document"]["chunks"] == []



@pytest.mark.asyncio
async def test_extract_pdf_file_from_url_wait_5_seconds(client: AsyncAurelioClient):
    url = "https://arxiv.org/pdf/2408.15291"

    response: ExtractResponse = await client.extract_url(
        url=url, quality="low", chunk=True, wait=5, polling_interval=1
    )

    dict_response = response.model_dump()

    # Status
    assert dict_response["status"] == "pending"

    # Processing options
    assert dict_response["processing_options"]["quality"] == "low"
    assert dict_response["processing_options"]["chunk"] is True

    # Document
    assert dict_response["document"]["id"].startswith("doc_")


@pytest.mark.asyncio
async def test_extract_pdf_file_from_bad_url(client: AsyncAurelioClient):
    with pytest.raises(ValueError):
        await client.extract_url(
            url="https://123.com", quality="low", chunk=True, wait=-1
        )
