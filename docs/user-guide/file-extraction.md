This guide provides technical details about processing different types of files with the Aurelio SDK, including PDFs, videos, and web content. It covers all available parameters, recommended configurations, and waiting strategies for large files.

## Processing Flow

```mermaid
flowchart TB
    A[Input Source] --> B{Source Type}
    B -->|PDF File| C[PDF Processor]
    B -->|Video File| D[Video Processor]
    B -->|URL| E[Web Content Extractor]
    
    C --> F[Text Extraction]
    D --> G[Transcription]
    E --> H[Content Fetching]
    
    F --> I[Document Processing]
    G --> I
    H --> I
    
    I --> J{Chunking Enabled?}
    J -->|Yes| K[Chunk Document]
    J -->|No| L[Raw Document]
    
    K --> M[Final Result]
    L --> M
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style B fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style C fill:#ffe6e6,stroke:#cc0000,stroke-width:2px
    style D fill:#e6ffe6,stroke:#00cc00,stroke-width:2px
    style E fill:#fff2e6,stroke:#ff8000,stroke-width:2px
    style M fill:#f5f5f5,stroke:#666,stroke-width:2px
```

## Common Parameters

All file extraction methods accept these core parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quality` | `"low"` \| `"high"` | `"low"` | Processing quality. Higher quality is more accurate but slower and consumes more resources. |
| `chunk` | `bool` | `True` | Whether to chunk the document using default chunking config. |
| `wait` | `int` | `30` | Time in seconds to wait for processing completion. Set to `-1` to wait indefinitely. Set to `0` to return immediately with a document ID. |
| `polling_interval` | `int` | `5` | Time in seconds between status check requests. Set to `0` to disable polling. |
| `retries` | `int` | `3` | Number of retry attempts in case of API errors (5xx). |

## Processing from PDF Files

The SDK enables extracting text from PDF documents stored as local files.

### Method Signature

```python
def extract_file(
    self,
    file: Optional[Union[IO[bytes], bytes]] = None,
    file_path: Optional[Union[str, pathlib.Path]] = None,
    quality: Literal["low", "high"] = "low",
    chunk: bool = True,
    wait: int = 30,
    polling_interval: int = 5,
    retries: int = 3,
) -> ExtractResponse:
    """Process a document from a file synchronously."""
```

### Usage Examples

#### From a file path:

```python
from aurelio_sdk import AurelioClient

client = AurelioClient()
response = client.extract_file(
    file_path="path/to/document.pdf",
    quality="low",
    chunk=True,
    wait=30
)
```

#### From file bytes:

```python
with open("path/to/document.pdf", "rb") as f:
    file_bytes = f.read()

file_bytes_io = io.BytesIO(file_bytes)
file_bytes_io.name = "document.pdf"  # Name is important for content type detection

response = client.extract_file(
    file=file_bytes_io,
    quality="high",
    chunk=True,
    wait=-1  # Wait until completion
)
```

### PDF Processing Recommendations

- Use `quality="low"` for faster processing of simple documents
- Use `quality="high"` for complex documents with tables, diagrams, or mixed layouts
- For large PDFs (>100 pages) or image-heavy PDFs, consider increasing `wait` time or using `-1`
- The SDK automatically handles pagination and merges content across pages

## Processing from Video Files

The SDK can extract transcriptions from video files (MP4 format).

### Usage Examples

```python
response = client.extract_file(
    file_path="path/to/video.mp4",
    quality="high",  # Recommended for accurate transcription
    chunk=True,
    wait=-1,         # Video processing can take longer
    polling_interval=15
)
```

### Video Processing Recommendations

- Always use `quality="high"` for better transcription accuracy
- Set `wait=-1` for videos longer than 5 minutes
- Use a longer `polling_interval` (15-30 seconds) for videos to reduce API calls
- Video processing is more resource-intensive and may take several minutes for longer files

## Processing from URLs

Extract content from web-based URLs, including PDF documents and webpages.

### Method Signature

```python
def extract_url(
    self,
    url: str,
    quality: Literal["low", "high"],
    chunk: bool,
    wait: int = 30,
    polling_interval: int = 5,
    retries: int = 3,
) -> ExtractResponse:
    """Process a document from a URL synchronously."""
```

### Usage Examples

```python
# PDF URL
pdf_response = client.extract_url(
    url="https://example.com/document.pdf",
    quality="low",
    chunk=True,
    wait=30
)

# Web page URL
webpage_response = client.extract_url(
    url="https://example.com/blog/article",
    quality="high",
    chunk=True,
    wait=30
)
```

### URL Processing Recommendations

- For PDF URLs, follow the same recommendations as for PDF files
- For web pages, use `quality="high"` to better preserve page structure
- When extracting from dynamic websites, be aware that client-side rendered content may not be fully captured

## Waiting Strategies for Large Files

Processing large files (extensive PDFs or long videos) requires appropriate waiting strategies to handle longer processing times.

```mermaid
sequenceDiagram
    participant Client
    participant API
    
    Note over Client,API: Immediate Return Strategy (wait=0)
    Client->>API: extract_file(wait=0)
    API-->>Client: {status: "pending", document_id: "doc_123"}
    Client->>API: get_document("doc_123")
    API-->>Client: {status: "pending"}
    Client->>API: get_document("doc_123")
    API-->>Client: {status: "completed", ...}
    
    Note over Client,API: Wait Until Completion Strategy (wait=-1)
    Client->>API: extract_file(wait=-1)
    API-->>Client: Processing...
    API-->>Client: Checking status...
    API-->>Client: {status: "completed", ...}
    
    Note over Client,API: Fixed Wait Strategy (wait=30)
    Client->>API: extract_file(wait=30)
    API-->>Client: Processing (up to 30s)...
    API-->>Client: {status: "pending/completed", ...}
```

### Recommended Strategies

1. **Immediate Return (`wait=0`):**
   - Best for very large files where you want to process asynchronously
   - You must handle polling separately
   - Good for user-facing applications to avoid blocking

2. **Wait Until Completion (`wait=-1`):**
   - Simplest approach for backend processing
   - Blocks until processing completes
   - Use `polling_interval` to control how frequently to check status
   - Best for batch processing jobs or automation

3. **Fixed Wait Time (`wait=30`):**
   - Wait for a predefined time (default 30 seconds)
   - Returns with whatever status is available after that time
   - Good for medium-sized files where you expect processing to be quick

### Example: Progressive Polling with Timeout

For large files with uncertain processing times, implement a progressive polling strategy:

```python
from aurelio_sdk import AurelioClient, TaskStatus

client = AurelioClient()

# First request returns immediately with document ID
response = client.extract_file(
    file_path="large_document.pdf",
    quality="high",
    chunk=True,
    wait=0
)

document_id = response.document.id
status = response.status
total_wait_time = 0
max_wait_time = 300  # 5 minutes
polling_interval = 10  # Start polling every 10 seconds

while status == TaskStatus.pending and total_wait_time < max_wait_time:
    # Wait before polling again
    time.sleep(polling_interval)
    total_wait_time += polling_interval
    
    # Get document status
    response = client.get_document(document_id)
    status = response.status
    
    # Increase polling interval for longer waits
    if total_wait_time > 60:
        polling_interval = 30
    
    print(f"Waited {total_wait_time}s, status: {status}")

if status == TaskStatus.completed:
    print("Processing completed successfully")
    document = response.document
else:
    print(f"Processing incomplete after {total_wait_time}s")
```

## Response Structure

The `ExtractResponse` object contains detailed information about the processed document:

```python
class ExtractResponse(BaseModel):
    status: TaskStatus  # "pending", "completed", or "failed"
    usage: Usage        # Resource usage information
    message: Optional[str]  # Additional information (e.g., errors)
    processing_options: ExtractProcessingOptions  # Applied options
    document: ResponseDocument  # The processed document
```

The `ResponseDocument` contains:

```python
class ResponseDocument(BaseModel):
    id: str           # Document ID
    content: str      # Full document content
    source: str       # Source filename or URL
    source_type: SourceType  # MIME type (application/pdf, video/mp4, etc.)
    num_chunks: int   # Number of chunks if chunking was enabled
    metadata: Dict[str, Any]  # User-definable metadata
    chunks: List[ResponseChunk]  # List of document chunks
```

## Error Handling

The SDK can raise several exceptions during file processing:

- `APITimeoutError`: Raised when the request exceeds the wait time
- `APIError`: General API error with details in the message
- `ApiRateLimitError`: Raised when API rate limits are exceeded

Example error handling:

```python
from aurelio_sdk import AurelioClient, APIError, APITimeoutError, ApiRateLimitError

client = AurelioClient()

try:
    response = client.extract_file(
        file_path="document.pdf",
        quality="high",
        chunk=True,
        wait=30
    )
except APITimeoutError:
    print("Processing is taking longer than expected")
except ApiRateLimitError:
    print("Rate limit exceeded, try again later")
except APIError as e:
    print(f"API error: {e.message}")
``` 