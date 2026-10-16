from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DatasetOut(ORM):
    id: str
    name: str
    original_filename: str
    file_format: str
    file_size: int
    status: str
    error: str | None
    row_count: int | None
    column_count: int | None
    created_at: datetime
    updated_at: datetime


class DatasetPatch(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class AnalyzeRequest(BaseModel):
    dataset_id: str
    question: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = None


class ExecuteRequest(BaseModel):
    dataset_id: str
    sql: str = Field(min_length=1, max_length=10000)


class MessageRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class AnalysisOut(BaseModel):
    query_id: str
    question: str | None
    sql: str
    columns: list[dict]
    rows: list[list]
    row_count: int
    truncated: bool
    duration_ms: int
    visualization: dict | None
    explanation: str | None
    attempts: int
    conversation_id: str | None = None


class HistoryOut(ORM):
    id: str
    dataset_id: str
    conversation_id: str | None
    question: str | None
    sql: str | None
    status: str
    error_category: str | None
    duration_ms: int | None
    row_count: int | None
    created_at: datetime


class SavedQueryIn(BaseModel):
    dataset_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    sql: str = Field(min_length=1, max_length=10000)


class SavedQueryPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    sql: str | None = Field(default=None, min_length=1, max_length=10000)


class SavedQueryOut(ORM):
    id: str
    dataset_id: str
    title: str
    description: str | None
    sql: str
    created_at: datetime
    updated_at: datetime


class ConversationIn(BaseModel):
    dataset_id: str
    title: str | None = Field(default=None, max_length=200)


class ConversationOut(ORM):
    id: str
    dataset_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(ORM):
    id: str
    role: str
    content: str
    sql: str | None
    query_id: str | None
    created_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
