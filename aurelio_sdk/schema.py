from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChunkerType(str, Enum):
    semantic = "semantic"
    regex = "regex"


class ChunkingOptions(BaseModel):
    max_chunk_length: int = Field(
        default=400, description="The maximum chunk length for the chunker"
    )
    chunker_type: ChunkerType = Field(
        default=ChunkerType.regex,
        description="The chunker type, either semantic or regex",
    )
    window_size: int = Field(
        default=1, description="The window size for the semantic chunker"
    )
    delimiters: List[str] = Field(
        default_factory=list,
        description="Optional. The regex delimiters for the regex chunker",
    )


class ChunkRequestPayload(BaseModel):
    content: str = Field(..., description="Input text to chunk.")
    processing_options: ChunkingOptions = Field(
        default_factory=ChunkingOptions,
        description="The processing options for the chunker",
    )


class TaskStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Usage(BaseModel):
    tokens: Optional[int] = Field(None, description="Number of tokens used")
    pages: Optional[int] = Field(None, description="Number of pages processed")
    seconds: Optional[int] = Field(None, description="Processing time in seconds")


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


class ChunkResponsePayload(BaseModel):
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


class ExtractResponsePayload(BaseModel):
    status: TaskStatus = Field(..., description="The status of the extraction process")
    usage: Usage = Field(..., description="Usage")
    message: Optional[str] = Field(None, description="Message")
    processing_options: ExtractProcessingOptions = Field(
        ..., description="The processing options for the document processor"
    )
    document: ResponseDocument = Field(..., description="Processed document")


class BodyProcessDocumentFileV1ExtractFilePost(BaseModel):
    file: Any = Field(..., description="The file to extract text from.")
    quality: ProcessingQuality = Field(
        ..., description="Processing quality of the document."
    )
    chunk: bool = Field(..., description="Whether the document should be chunked")
    timeout: int = Field(
        default=30,
        description="The timeout to keep open the connection to the client in seconds, defaults to 30 seconds, -1 means no timeout.",
    )


class BodyProcessUrlV1ExtractUrlPost(BaseModel):
    url: str = Field(..., description="The URL of the document file.")
    quality: ProcessingQuality = Field(
        ..., description="Processing quality of the document."
    )
    chunk: bool = Field(..., description="Whether the document should be chunked")
    timeout: int = Field(
        default=30,
        description="The timeout to keep open the connection to the client in seconds, defaults to 30 seconds, -1 means no timeout.",
    )
