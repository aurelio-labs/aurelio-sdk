from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChunkingOptions(BaseModel):
    max_chunk_length: Optional[int] = Field(
        default=400, description="The maximum chunk length for the chunker"
    )
    chunker_type: Optional[Literal["regex", "semantic"]] = Field(
        default="regex",
        description="The chunker type, either regex or semantic",
    )
    window_size: Optional[int] = Field(
        default=1, description="The window size for the semantic chunker"
    )
    delimiters: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional. The regex delimiters for the regex chunker",
    )


class ChunkRequestPayload(BaseModel):
    content: str = Field(..., description="Input text to chunk.")
    processing_options: Optional[ChunkingOptions] = Field(
        default=None,
        description="The processing options for the chunker",
    )


class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Usage(BaseModel):
    tokens: Optional[int] = None
    pages: Optional[int] = None
    seconds: Optional[int] = None

    class Config:
        exclude_none = True


class ResponseChunk(BaseModel):
    id: str = Field(..., description="ID of the chunk")
    content: str = Field(..., description="Content of the chunk")
    chunk_index: int = Field(..., description="Index of the chunk in the document")
    num_tokens: int = Field(..., description="Number of tokens in the chunk")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata of the chunk"
    )


class SourceType(str, Enum):
    application_pdf = "application/pdf"
    text_plain = "text/plain"
    video_mp4 = "video/mp4"


class ResponseDocument(BaseModel):
    id: str = Field(..., description="ID of the document")
    content: str = Field(..., description="Content of the document")
    source: str = Field(..., description="Source of the document")
    source_type: SourceType = Field(
        ..., description="Type of the document e.g. video/mp4, application/pdf"
    )
    num_chunks: int = Field(..., description="Total number of chunks in the document")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata for users"
    )
    chunks: List[ResponseChunk] = Field(
        default_factory=list, description="Chunks of the document"
    )


class ChunkResponse(BaseModel):
    status: TaskStatus = Field(..., description="The status of the chunking process")
    usage: Usage = Field(..., description="Usage")
    message: Optional[str] = Field(None, description="Message")
    processing_options: ChunkingOptions = Field(
        ..., description="The processing options for the chunker"
    )
    document: ResponseDocument = Field(..., description="Processed document")


class ProcessingQuality(str, Enum):
    low = "low"
    high = "high"


class ExtractProcessingOptions(BaseModel):
    chunk: bool = Field(..., description="Whether the document should be chunked")
    quality: ProcessingQuality = Field(
        ..., description="Processing quality of the document"
    )


class ExtractResponse(BaseModel):
    status: TaskStatus = Field(..., description="The status of the extraction process")
    usage: Usage = Field(..., description="Usage")
    message: Optional[str] = Field(None, description="Message")
    processing_options: ExtractProcessingOptions = Field(
        ..., description="The processing options for the document processor"
    )
    document: ResponseDocument = Field(..., description="Processed document")

    class Config:
        arbitrary_types_allowed = True
        exclude_none = True


# Embeddings Response
# ----------------------
class BM25Embedding(BaseModel):
    indices: list[int]
    values: list[float]


class EmbeddingUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingDataObject(BaseModel):
    object: str = Field(default="embedding", description="The object type")
    index: int = Field(description="The index of the embedding")
    embedding: BM25Embedding = Field(description="The embedding object")


class EmbeddingResponse(BaseModel):
    """Response object for embeddings"""

    message: str | None = Field(default=None, description="Message")
    model: str = Field(description="The model name used for embedding")
    object: str = Field(default="list", description="The object type")
    usage: EmbeddingUsage = Field(description="Usage")
    data: list[EmbeddingDataObject] = Field(description="The embedded documents")

    class Config:
        exclude_none = True
