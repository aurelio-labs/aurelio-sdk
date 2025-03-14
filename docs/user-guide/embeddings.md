This guide provides detailed technical information about embedding capabilities in the Aurelio SDK. Embeddings are vector representations of text that capture semantic meaning and are essential for building text retrieval and search systems.

## Embedding Flow

```mermaid
flowchart TB
    A[Input Text] --> B[Preprocessing]
    B --> C[BM25 Embedding Model]
    C --> D[Sparse Vector Generation]
    D --> E[Final Embeddings]
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style C fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style E fill:#f5f5f5,stroke:#666,stroke-width:2px
```

## Embedding Options

The SDK provides a focused embedding API with the following parameters:

```python
def embedding(
    self,
    input: Union[str, List[str]],
    input_type: Annotated[str, Literal["queries", "documents"]],
    model: Annotated[str, Literal["bm25"]],
    timeout: int = 30,
    retries: int = 3,
) -> EmbeddingResponse:
    """Generate embeddings for the given input using the specified model."""
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | `Union[str, List[str]]` | Required | Text or list of texts to embed |
| `input_type` | `str` | Required | Either "queries" or "documents" depending on use case |
| `model` | `str` | `"bm25"` | Embedding model to use (currently only "bm25" is available) |
| `timeout` | `int` | `30` | Maximum seconds to wait for API response |
| `retries` | `int` | `3` | Number of retry attempts for failed requests |

## Sparse Embeddings

The Aurelio SDK uses sparse BM25-style embeddings, which differ from traditional dense embeddings:

```mermaid
flowchart LR
    subgraph "Dense Embedding"
        A1[Input Text] --> B1[Dense Model]
        B1 --> C1[Fixed-Dimension Dense Vector]
    end
    
    subgraph "Sparse BM25 Embedding"
        A2[Input Text] --> B2[BM25 Model]
        B2 --> C2[Sparse Vector with Indices & Values]
    end
    
    style B1 fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style B2 fill:#ffe6e6,stroke:#cc0000,stroke-width:2px
    style C1 fill:#f9f9f9,stroke:#333,stroke-width:2px
    style C2 fill:#f9f9f9,stroke:#333,stroke-width:2px
```

### Aurelio Sparse Implementation

The SDK's BM25 embedding model uses a single set of pretrained weights trained on a web-scale dataset to produce a "world model" set of BM25-like weights. These weights are transformed into sparse vector embeddings with the following characteristics:

- **Structure**: Each embedding contains index-value pairs, where indices represent specific terms/tokens and values represent their importance
- **Sparse Representation**: Only non-zero values are stored, making them memory-efficient
- **Exact Term Matching**: Excellent for capturing exact terminology for specialized domains
- **Domain-Specific Performance**: Well-suited for finance, medical, legal, and technical domains where specific terminology matters

### Input Types

The `input_type` parameter accepts two possible values:

| Input Type | Use Case | Description |
|------------|----------|-------------|
| `"documents"` | Creating a searchable knowledge base | Optimizes embeddings for document representation in a vector database |
| `"queries"` | Querying a knowledge base | Optimizes embeddings for query representation when searching against embedded documents |

### Sparse Embedding Structure

```python
class SparseEmbedding(BaseModel):
    indices: list[int]
    values: list[float]
```

The `indices` correspond to token positions in the vocabulary, while the `values` represent the importance of each token for the given text.

## Usage Examples

### Basic Embedding Generation

```python
from aurelio_sdk import AurelioClient

client = AurelioClient(api_key="your_api_key")

# Embedding a single text
response = client.embedding(
    input="What is the capital of France?", 
    input_type="queries",
    model="bm25"
)

# Accessing the embedding
embedding = response.data[0].embedding
print(f"Indices: {embedding.indices[:5]}...")
print(f"Values: {embedding.values[:5]}...")
```

### Batch Embedding Generation

```python
# Embedding multiple documents at once
documents = [
    "Paris is the capital of France.",
    "Berlin is the capital of Germany.",
    "Rome is the capital of Italy."
]

response = client.embedding(
    input=documents,
    input_type="documents",
    model="bm25"
)

# Process each embedding
for i, item in enumerate(response.data):
    embedding = item.embedding
    print(f"Document {i}: {len(embedding.indices)} non-zero elements")
```

### Async Embedding Generation

```python
from aurelio_sdk import AsyncAurelioClient
import asyncio

async def generate_embeddings():
    client = AsyncAurelioClient(api_key="your_api_key")
    
    response = await client.embedding(
        input="Async embedding generation", 
        input_type="documents",
        model="bm25"
    )
    
    return response

embeddings = asyncio.run(generate_embeddings())
```

## Complete Workflow: Chunk and Embed

A common pattern is to chunk documents and then embed each chunk:

```python
# 1. Extract and chunk a document
extract_response = client.extract_file(
    file_path="document.pdf", 
    quality="high",
    chunk=True
)

# 2. Get chunks from the document
chunks = [chunk.content for chunk in extract_response.document.chunks]

# 3. Generate embeddings for all chunks
embedding_response = client.embedding(
    input=chunks,
    input_type="documents",
    model="bm25"
)

# Now you can store these embeddings in a vector database
for i, chunk in enumerate(extract_response.document.chunks):
    embedding = embedding_response.data[i].embedding
    # Store chunk ID, content, and embedding in your vector store
```

## Response Structure

The embedding response contains detailed information:

```python
class EmbeddingResponse(BaseModel):
    message: Optional[str]
    model: str      # The model used (e.g., "bm25")
    object: str     # Always "list"
    usage: EmbeddingUsage
    data: list[EmbeddingDataObject]
```

The `EmbeddingUsage` provides token consumption metrics:

```python
class EmbeddingUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int
```

Each embedding is contained in an `EmbeddingDataObject`:

```python
class EmbeddingDataObject(BaseModel):
    object: str     # Always "embedding"
    index: int      # Position in the input array
    embedding: SparseEmbedding
```

## Advantages of Sparse Embeddings

### Sparse vs. Dense Embeddings

| Characteristic | Sparse BM25 Embeddings | Dense Embeddings |
|----------------|------------------------|------------------|
| Representation | Index-value pairs for non-zero elements | Fixed-dimension vectors of continuous values |
| Storage Efficiency | High (only stores non-zero values) | Low (stores all dimensions) |
| Term Matching | Excellent for exact term/keyword matching | May miss exact terminology |
| Domain Adaptation | Strong for specialized vocabulary domains | May require fine-tuning for domains |
| Interpretability | Higher (indices correspond to vocabulary terms) | Lower (dimensions not directly interpretable) |

### When to Use Sparse

```mermaid
flowchart TD
    A[Choose Embedding Type] --> B{Need Exact Term Matching?}
    B -->|Yes| C[Use Sparse BM25]
    B -->|No| D[Consider Dense Embeddings]
    
    C --> E{Application Domain}
    E -->|Medical/Legal/Technical| F[Sparse BM25 Recommended]
    E -->|General Text| G[Either May Work]
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style C fill:#e6ffe6,stroke:#00cc00,stroke-width:2px
    style F fill:#e6ffe6,stroke:#00cc00,stroke-width:2px
```

Sparse BM25 embeddings excel in scenarios where:

- You need to capture domain-specific terminology (medical, finance, legal, technical)
- Exact keyword matching is important
- You want higher interpretability of search results
- You're building systems where precision on terminology matters more than general semantic similarity

## Error Handling

```python
from aurelio_sdk import AurelioClient, ApiError, ApiTimeoutError

client = AurelioClient(api_key="your_api_key")

try:
    response = client.embedding(
        input="Sample text", 
        input_type="documents",
        model="bm25"
    )
except ApiTimeoutError:
    print("Request timed out, try increasing the timeout parameter")
except ApiError as e:
    print(f"Error: {e.message}")
```

## Future Plans

The Aurelio SDK plans to enhance embedding capabilities with:

- Additional sparse embedding models
- User-trainable models for specific domains
- Advanced embedding customization options

Stay tuned for updates to the embedding API as these features become available. 