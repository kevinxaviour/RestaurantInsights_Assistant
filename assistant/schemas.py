from typing import Any

from pydantic import BaseModel, Field


class SQLPlan(BaseModel):
    sql: str = Field(description="Single SELECT query for SQLite only.")


class AnalysisPlan(BaseModel):
    objective: str
    metric_definition: str
    dimensions: list[str]
    period_logic: str
    must_include_channel_breakdown: bool


class RelevanceVerdict(BaseModel):
    relevant: bool
    feedback: str


class InsightReport(BaseModel):
    executive_summary: str
    key_findings: list[str]
    risks_or_gaps: list[str]
    actions: list[str]


class QueryPayload(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class WorkflowState(BaseModel):
    question: str
    sql: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    payload_mode: str | None = None
    payload_text: str | None = None
    sql_provider: str | None = None
    analysis_provider: str | None = None
    report: dict[str, Any] | None = None
