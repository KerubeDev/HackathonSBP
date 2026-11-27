from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

API_VERSION = "v1"

class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=2000)
    schema_context: str | None = Field(default=None, max_length=12000)
    requested_chart_types: list[str] = Field(default_factory=list, max_length=5)
    execution_mode: Literal["sync", "async"] | None = None
    api_version: Literal["v1"] = "v1"

class ErrorBody(BaseModel):
    code: str
    message: str
    run_id: str | None = None

class RunEnvelope(BaseModel):
    api_version: str = API_VERSION
    run_id: str
    status: str
    execution_mode: str
    created_at: str
    poll_url: str
    result: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    error: ErrorBody | None = None

class RankingQuery(BaseModel):
    period: str | None = None
    ranking: str | None = None
    bank: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class UploadConfirmation(BaseModel):
    period: str = Field(min_length=8, max_length=8, pattern=r"^\d{8}$")
    source_sha256: str | None = Field(default=None, min_length=64, max_length=64)

class LoadCancellation(BaseModel):
    reason: str = Field(default="cancelled by administrator", max_length=500)
