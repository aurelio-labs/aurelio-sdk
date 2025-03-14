The Aurelio SDK provides a streamlined interface to the Aurelio Platform's document processing capabilities. It enables developers to extract, chunk, and embed textual content from various sources with minimal effort.

## What is Aurelio SDK?

Aurelio SDK is a Python library that abstracts the complexity of document processing pipelines. It offers both synchronous and asynchronous clients to interact with the Aurelio Platform.

## Core Capabilities

### Document Extraction
Extract text from multiple sources including:
- PDF documents (local files or URLs)
- Video files with automatic transcription
- Web-based content

### Intelligent Chunking
Break down documents into meaningful segments using:
- Semantic chunking that respects content boundaries
- Configurable parameters for chunk size and overlap
- Window-based processing for context preservation

### Embeddings Generation
Transform text into vector representations using:
- Multiple embedding models including BM25
- Batch processing for efficiency
- Consistent vector formats for downstream applications

## When to Use Aurelio SDK

Aurelio SDK is particularly useful when:

- Building document processing pipelines that require extraction and structuring of content
- Implementing semantic search capabilities across large document collections
- Preparing text data for large language model applications
- Creating NLP workflows that need consistent text chunking and embedding

## Architecture

The SDK follows a client-based architecture:

```mermaid
%%{init: {'theme':'neutral', 'themeVariables': {'darkMode': true, 'primaryColor': '#4182c3', 'primaryTextColor': '#fff', 'primaryBorderColor': '#7a7a7a', 'lineColor': '#7a7a7a', 'secondaryColor': '#f5f5f5', 'tertiaryColor': '#333'}}}%%
flowchart LR
    A[Your Application] --> B[Aurelio SDK Client]
    B --> C[Aurelio Platform API]
    C --> D[Processing Results]
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style B fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style C fill:#f0f0f0,stroke:#666,stroke-width:2px
    style D fill:#f5fff5,stroke:#060,stroke-width:2px
```

This structure allows for clean separation of concerns, with the SDK handling authentication, request formatting, and response parsing, letting you focus on your application logic.

## Getting Started

To start using the SDK, continue to [Quickstart Guide](quickstart) for installation instructions and basic usage examples.