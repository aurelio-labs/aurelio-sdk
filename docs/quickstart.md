This guide will get you up and running with the Aurelio SDK for document processing, chunking, and embedding generation.

## Installation

Install the Aurelio SDK using pip:

```bash
pip install -qU aurelio-sdk
```

Or with Poetry:

```bash
poetry add aurelio-sdk
```

## Authentication

The SDK requires an [API key](https://platform.aurelio.ai/) for authentication:

```python
from aurelio_sdk import AurelioClient
import os

# Set your API key as an environment variable
# export AURELIO_API_KEY=your_api_key_here

# Initialize the client
client = AurelioClient(api_key=os.environ["AURELIO_API_KEY"])

# Or use the async client for better performance
from aurelio_sdk import AsyncAurelioClient
async_client = AsyncAurelioClient(api_key=os.environ["AURELIO_API_KEY"])
```

## Document Extraction

Extract text from a PDF file:

```python
from aurelio_sdk import ExtractResponse

# Local PDF file
response = client.extract_file(
    file_path="document.pdf", 
    quality="high",  # Higher quality, more accurate but slower
    chunk=True,      # Automatically chunk the document
    wait=30          # Wait up to 30 seconds for processing
)

# Access the document ID for status checking
document_id = response.document.id

# If the document is still processing, wait for completion
if response.status != "complete":
    final_response = client.wait_for(document_id=document_id, wait=300)
    
# Access the chunks once processing is complete
for chunk in final_response.chunks:
    print(f"Chunk: {chunk.text[:100]}...")
```

For PDF URLs:

```python
url_response = client.extract_url(
    url="https://arxiv.org/pdf/2305.10403.pdf",
    quality="high",
    chunk=True,
    wait=30
)
```

## Intelligent Chunking

Chunk existing text with customized settings:

```python
from aurelio_sdk import ChunkingOptions, ChunkResponse

# Define chunking parameters
chunking_options = ChunkingOptions(
    chunker_type="semantic",  # Uses semantic chunking
    max_chunk_length=400,     # Maximum token limit for one chunk
    window_size=5             # Rolling window context size
)

long_text = """Your long document text here..."""

# Perform chunking
chunk_response = client.chunk(
    content=long_text, 
    processing_options=chunking_options
)

# Process the chunks
for i, chunk in enumerate(chunk_response.chunks):
    print(f"Chunk {i+1}: {chunk.text[:50]}...")
```

## Embedding Generation

Generate embeddings for text or chunks:

```python
from aurelio_sdk import EmbeddingResponse

# Generate embeddings for a single text
single_embedding = client.embedding(
    input="This is a sample text to embed",
    model="bm25"  # Choose your embedding model
)

# Generate embeddings for multiple texts (batch processing)
texts = [
    "First document to embed",
    "Second document to embed",
    "Third document to embed"
]

batch_embeddings = client.embedding(
    input=texts
)

# Access the embedding vectors
vectors = batch_embeddings.data
```

## Complete Pipeline Example

Extract, chunk, and embed a PDF in one workflow:

```python
# 1. Extract and chunk a PDF
extract_response = client.extract_file(
    file_path="research_paper.pdf", 
    quality="high",
    chunk=True,
    wait=60
)

# Wait for completion if needed
if extract_response.status != "complete":
    extract_response = client.wait_for(document_id=extract_response.document.id, wait=300)

# 2. Get all chunk texts
chunk_texts = [chunk.text for chunk in extract_response.chunks]

# 3. Generate embeddings for all chunks
embedding_response = client.embedding(input=chunk_texts)

# 4. Now you have vectorized your PDF document
# Each vector corresponds to a chunk from the original document
vectors = embedding_response.data
```