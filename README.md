<p>
<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/aurelio-sdk?logo=python&logoColor=gold" />
<img alt="GitHub Contributors" src="https://img.shields.io/github/contributors/aurelio-labs/aurelio-sdk" />
<img alt="GitHub Last Commit" src="https://img.shields.io/github/last-commit/aurelio-labs/aurelio-sdk" />
<img alt="GitHub Repo Size" src="https://img.shields.io/github/repo-size/aurelio-labs/aurelio-sdk" />
<img alt="GitHub Issues" src="https://img.shields.io/github/issues/aurelio-labs/aurelio-sdk" />
<img alt="GitHub Pull Requests" src="https://img.shields.io/github/issues-pr/aurelio-labs/aurelio-sdk" />
<img alt="Github License" src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</p>

# Aurelio SDK

The Aurelio Platform SDK. [API references](https://api.aurelio.ai/saturn)

## Installation

To install the Aurelio SDK, use pip or poetry:

```bash
pip install aurelio-sdk
```

## Authentication

The SDK requires an API key for authentication.
Get key from [Aurelio Platform](https://platform.aurelio.ai).
Set your API key as an environment variable:

```bash
export AURELIO_API_KEY=your_api_key_here
```

## Usage

See [examples](./examples) for more details.

### Initializing the Client

```python
from aurelio_sdk import AurelioClient
import os

client = AurelioClient(api_key=os.environ["AURELIO_API_KEY"])
```

or use asynchronous client:

```python
from aurelio_sdk import AsyncAurelioClient

client = AsyncAurelioClient(api_key="your_api_key_here")
```

### Chunk

```python
from aurelio_sdk import ChunkingOptions, ChunkResponse

# All options are optional with default values
chunking_options = ChunkingOptions(
    chunker_type="semantic", max_chunk_length=400, window_size=5
)

response: ChunkResponse = client.chunk(
    content="Your text here to be chunked", processing_options=chunking_options
)
```

### Extracting Text from Files

#### PDF Files

```python
from aurelio_sdk import ExtractResponse

# From a local file
file_path = "path/to/your/file.pdf"

with open(file_path, "rb") as file:
    response_pdf_file: ExtractResponse = client.extract_file(
        file=file, quality="low", chunk=True, wait=-1, enable_polling=True
    )
```

#### Video Files

```python
from aurelio_sdk import ExtractResponse

# From a local file
file_path = "path/to/your/file.mp4"

with open(file_path, "rb") as file:
    response_video_file: ExtractResponse = client.extract_file(
        file=file, quality="low", chunk=True, wait=-1, enable_polling=True
    )
```

### Extracting Text from URLs

#### PDF URLs

```python
from aurelio_sdk import ExtractResponse

# From URL
url = "https://arxiv.org/pdf/2408.15291"
response_pdf_url: ExtractResponse = client.extract_url(
    url=url, quality="low", chunk=True, wait=-1, enable_polling=True
)
```

#### Video URLs

```python
from aurelio_sdk import ExtractResponse

# From URL
url = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4"
response_video_url: ExtractResponse = client.extract_url(
    url=url, quality="low", chunk=True, wait=-1, enable_polling=True
)
```

### Waiting for completion and checking document atatus

```python
# Set timeout for large files with `high` quality
# Timeout is set to 10 seconds
response_pdf_url: ExtractResponse = client.extract_url(
    url="https://arxiv.org/pdf/2408.15291", quality="high", chunk=True, wait=10
)

# Get document status and response
document_response: ExtractResponse = client.get_document(
    document_id=response_pdf_file.document.id
)
print("Status:", document_response.status)

# Use a pre-built function, which helps to avoid long hanging requests (Recommended)
document_response = client.wait_for(
    document_id=response_pdf_file.document.id, wait=300
)
```

### Embeddings

```python
from aurelio_sdk import EmbeddingResponse

response: EmbeddingResponse = client.embedding(
    input="Your text here to be embedded",
    model="bm25")

# Or with a list of texts
response: EmbeddingResponse = client.embedding(
    input=["Your text here to be embedded", "Your text here to be embedded"]
)
```

## Response Structure

The `ExtractResponse` object contains the following key information:

- `status`: The current status of the extraction task
- `usage`: Information about token usage, pages processed, and processing time
- `message`: Any relevant messages about the extraction process
- `document`: The extracted document information, including its ID
- `chunks`: The extracted text, divided into chunks if chunking was enabled

The `EmbeddingResponse` object contains the following key information:

- `message`: Any relevant messages about the embedding process
- `model`: The model name used for embedding
- `usage`: Information about token usage, pages processed, and processing time
- `data`: The embedded documents

## Best Practices

1. Use appropriate wait times based on your use case and file sizes.
2. Use async client for better performance.
3. For large files or when processing might take longer, enable polling for long-hanging requests.
4. Always handle potential exceptions and check the status of the response.
5. Adjust the `quality` parameter based on your needs. "low" is faster but less accurate, while "high" is slower but more accurate.
