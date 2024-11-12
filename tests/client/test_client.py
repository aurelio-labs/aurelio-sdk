import os

import pytest
from dotenv import load_dotenv

from aurelio_sdk.client import AurelioClient
from aurelio_sdk.exceptions import ApiError
from aurelio_sdk.schema import ChunkingOptions

load_dotenv()


# setup sync client
@pytest.fixture
def client() -> AurelioClient:
    client = AurelioClient(
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


def test_sync_client_initialization():
    client = AurelioClient(api_key="test_api_key")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"


def test_sync_client_no_api_key(no_api_key_env):
    with pytest.raises(ValueError):
        AurelioClient(api_key="", base_url="https://api.aurelio.ai")


def test_sync_client_unauthorized():
    client = AurelioClient(api_key="test_api_key")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"
    with pytest.raises(ApiError):
        client.chunk(content="test", processing_options=ChunkingOptions())


def test_sync_client_empty_base_url():
    client = AurelioClient(api_key="test_api_key", base_url="")
    assert client.api_key == "test_api_key"
    assert client.base_url == "https://api.aurelio.ai"


# SJ - as a placeholder for now
# def test_sync_client_rate_limit_error(client: AurelioClient):
#     with pytest.raises(ApiRateLimitError):
#         if client.base_url not in [
#             "https://api.aurelio.ai",
#             "https://staging.api.aurelio.ai",
#         ]:
#             # Rate limits are available only in the cloud environments
#             # This is for local testing
#             client = AurelioClient(
#                 api_key=os.environ["AURELIO_API_KEY_PRODUCTION"],
#                 base_url=os.environ["BASE_URL_PRODUCTION"],
#             )

#         file_path = Path(__file__).parent.parent / "data" / "test_pdf.pdf"
#         # Trigger rate limit by making multiple requests
#         for _ in range(30):
#             try:
#                 client.extract_file(
#                     file_path=file_path,
#                     quality="low",
#                     chunk=False,
#                     wait=-1,
#                     polling_interval=2,
#                 )
#             except ApiRateLimitError as e:
#                 raise e
#             except Exception:
#                 continue
