This guide helps you migrate your code from previous versions of the Aurelio SDK to v0.0.19, which introduces significant changes to the `extract` endpoint.

## Key Changes

### Deprecated: `quality` parameter

The `quality` parameter previously used with values `"low"` and `"high"` for both PDF and MP4 file extraction has been deprecated.

### New: `model` parameter 

The new `model` parameter replaces `quality` and provides more granular control over the extraction process with different model options.

### New: Enhanced processing options for video files

For MP4 files, chunking preferences previously set through the `quality` parameter are now explicitly configured in the `processing_options` parameter.

## Migration Table

| File Type | Old Approach | New Approach | Notes |
|-----------|--------------|--------------|-------|
| PDF | `quality="low"` | `model="aurelio-base"` | Fastest, cheapest option for clean PDFs |
| PDF | `quality="high"` | `model="docling-base"` | Code-based OCR method for high precision |
| PDF | - | `model="gemini-2-flash-lite"` | **New!** State-of-the-art VLM-based extraction |
| MP4 | `quality="low"`, `chunk=True` | `model="aurelio-base"`, `processing_options={"chunking": {"chunker_type": "regex"}}` | Basic chunking for videos |
| MP4 | `quality="high"`, `chunk=True` | `model="aurelio-base"`, `processing_options={"chunking": {"chunker_type": "semantic"}}` | Semantic chunking for videos |

## Code Examples

### PDF Extraction

#### Before (pre-v0.0.19):

```python
# Fast extraction for simple PDFs
response = client.extract_file(
    file_path="document.pdf",
    quality="low",
    chunk=True,
    wait=30
)

# Higher quality extraction for complex PDFs
response = client.extract_file(
    file_path="complex_document.pdf",
    quality="high",
    chunk=True,
    wait=30
)
```

#### After (v0.0.19+):

```python
# Fast extraction for simple PDFs
response = client.extract_file(
    file_path="document.pdf",
    model="aurelio-base",  # Equivalent to the old quality="low"
    chunk=True,
    wait=30
)

# Higher quality extraction for complex PDFs
response = client.extract_file(
    file_path="complex_document.pdf",
    model="docling-base",  # Equivalent to the old quality="high"
    chunk=True,
    wait=30
)

# NEW: State-of-the-art extraction using VLM
response = client.extract_file(
    file_path="document.pdf",
    model="gemini-2-flash-lite",  # New option not available before
    chunk=True,
    wait=30
)
```

### Video Extraction

#### Before (pre-v0.0.19):

```python
# Basic video extraction with regex chunking
response = client.extract_file(
    file_path="video.mp4",
    quality="low",
    chunk=True,
    wait=-1
)

# Video extraction with semantic chunking
response = client.extract_file(
    file_path="video.mp4",
    quality="high",
    chunk=True,
    wait=-1
)
```

#### After (v0.0.19+):

```python
# Basic video extraction with regex chunking
response = client.extract_file(
    file_path="video.mp4",
    model="aurelio-base",  # Only supported model for videos
    chunk=True,
    wait=-1,
    processing_options={
        "chunking": {
            "chunker_type": "regex"  # Equivalent to old quality="low"
        }
    }
)

# Video extraction with semantic chunking
response = client.extract_file(
    file_path="video.mp4",
    model="aurelio-base",  # Only supported model for videos
    chunk=True,
    wait=-1,
    processing_options={
        "chunking": {
            "chunker_type": "semantic"  # Equivalent to old quality="high"
        }
    }
)
```

## URL Extraction

The changes for `extract_url` are identical to those for `extract_file` - replace the `quality` parameter with the appropriate `model` parameter, and for videos, specify chunking preferences in `processing_options`.

## VLM-based Extraction (New Feature)

The new `gemini-2-flash-lite` model uses a Vision Language Model to process PDF content, offering state-of-the-art accuracy. This can be especially valuable for:

- Scanned documents with complex layouts
- Documents with tables, charts, and diagrams
- Documents where context and visual understanding are important

```python
response = client.extract_file(
    file_path="complex_scanned_document.pdf",
    model="gemini-2-flash-lite",
    chunk=True,
    wait=60  # May require longer processing time
)
```

**Note:** As mentioned in the [OCR in Large Multimodal Models paper](https://arxiv.org/html/2305.07895v5), VLMs like Gemini can occasionally hallucinate content. While hallucinations are rare, the model is designed for high-recall, potentially with lower precision than code-based OCR methods.

## Pricing Considerations

- `aurelio-base` pricing is equivalent to the old `low` quality setting
- Both `docling-base` and `gemini-2-flash-lite` are priced equivalent to the old `high` quality setting

## Transition Period

The `quality` parameter will continue to work during a transition period but will be removed in a future release. We recommend updating your code to use the new `model` parameter as soon as possible. 