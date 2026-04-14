from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .config import AssistantConfig
from .formatters import JSONPayloadFormatter, TOONPayloadFormatter
from .providers import LLMProviderRouter
from .schemas import (
    AnalysisPlan,
    InsightReport,
    QueryPayload,
    RelevanceVerdict,
    SQLPlan,
)
from .warehouse import CSVSQLiteWarehouse


def _enable_langchain_tracing() -> None:
    if not os.getenv("LANGCHAIN_API_KEY"):
        return

    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "restaurantproject")


class RestaurantInsightsAssistant:
    def __init__(self, config: AssistantConfig):
        self.config = config
        self.router = LLMProviderRouter(config)
        self.warehouse = CSVSQLiteWarehouse(config)
        self.min_date, self.max_date = self.warehouse.get_date_bounds()
        self.json_formatter = JSONPayloadFormatter()
        self.toon_formatter = TOONPayloadFormatter()

    def _schema_hint(self) -> str:
        return (
            f"Table: {self.config.sqlite_table}\n"
            "Columns:\n"
            "- Order_ID (INTEGER)\n"
            "- Date (TEXT, YYYY-MM-DD)\n"
            "- Product (TEXT)\n"
            "- Price (REAL)\n"
            "- Quantity (REAL)\n"
            "- Purchase_Type (TEXT)\n"
            "- Payment_Method (TEXT)\n"
            "- Manager (TEXT)\n"
            "- City (TEXT)\n"
            "Revenue formula: (Price * Quantity).\n"
            "No cost column exists: interpret profit/loss as revenue delta only.\n"
            f"Date boundaries: {self.min_date} to {self.max_date}.\n"
            "Use TRIM on text dimensions for grouping/filtering."
        )

    def _plan_analysis(self, question: str) -> tuple[str, AnalysisPlan]:
        prompt = (
            "You are a senior restaurant data strategist.\n"
            "Create an analysis plan before SQL.\n"
            "Plan should capture metrics, time logic, and dimensions needed to answer fully.\n"
            "If user asks where profit/revenue was taken, include channel dimensions such as"
            " Purchase_Type and Payment_Method.\n"
            "Keep plan practical for one SQL query.\n\n"
            f"{self._schema_hint()}\n\n"
            f"Question: {question}"
        )
        provider, plan = self.router.invoke_structured(prompt, AnalysisPlan)
        return provider, plan

    def _build_sql(
        self, question: str, plan: AnalysisPlan, feedback: str = ""
    ) -> tuple[str, str]:
        prompt = (
            "You are a senior analytics SQL planner.\n"
            "Return one valid SQLite SELECT query only.\n"
            "No DML/DDL.\n"
            "Stay strictly inside date boundaries.\n"
            "Ensure output is sufficient for business comparison and driver analysis.\n"
            "If needed, include row_type labels to mix summary rows and breakdown rows in one result.\n\n"
            f"{self._schema_hint()}\n\n"
            f"Question: {question}\n"
            f"Analysis plan objective: {plan.objective}\n"
            f"Metric definition: {plan.metric_definition}\n"
            f"Dimensions: {plan.dimensions}\n"
            f"Period logic: {plan.period_logic}\n"
            f"Channel breakdown required: {plan.must_include_channel_breakdown}\n"
        )
        if feedback.strip():
            prompt += f"\nImprove previous SQL using this feedback:\n{feedback}\n"

        provider, result = self.router.invoke_structured(prompt, SQLPlan)
        sql = result.sql.strip().rstrip(";") + ";"
        return provider, sql

    @staticmethod
    def _to_payload(
        question: str, sql: str, columns: list[str], rows: list[list[Any]]
    ) -> QueryPayload:
        return QueryPayload(
            question=question,
            sql=sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
        )

    def _choose_payload(self, payload: QueryPayload) -> tuple[str, str]:
        json_blob = self.json_formatter.format(payload)
        if len(json_blob) > self.config.toon_threshold_chars:
            return "TOON", self.toon_formatter.format(payload)
        return "JSON", json_blob

    def _judge_relevance(
        self,
        question: str,
        plan: AnalysisPlan,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
    ) -> tuple[str, RelevanceVerdict]:
        sample_rows = rows[:20]
        prompt = (
            "You are a strict relevance judge for analytics completeness.\n"
            "Decide if query output is sufficient to answer the user question fully.\n"
            "If insufficient, explain exactly what is missing.\n"
            "If question asks where gains/losses came from, require segment/channel breakdown when needed.\n"
            "If sufficient, mark relevant true and give short feedback.\n\n"
            f"Question: {question}\n"
            f"Plan: {plan.model_dump_json()}\n"
            f"SQL: {sql}\n"
            f"Columns: {columns}\n"
            f"Row count: {len(rows)}\n"
            f"Row sample: {sample_rows}"
        )
        provider, verdict = self.router.invoke_structured(prompt, RelevanceVerdict)
        return provider, verdict

    def _analyze(
        self, question: str, payload_mode: str, payload_text: str
    ) -> tuple[str, InsightReport]:
        prompt = (
            "You are a Senior Business Analyst for restaurants and hospitality.\n"
            "Read the structured payload and provide precise executive insight.\n"
            "Use only provided numbers.\n"
            "No cost column exists, so interpret profit/loss as revenue delta only.\n"
            "Never reference dates outside dataset boundaries.\n"
            f"Dataset boundaries: {self.min_date} to {self.max_date}.\n"
            "Be analytical: compare performance, identify drivers, and quantify impact.\n"
            "When channel fields exist, explicitly explain contribution by Purchase_Type and Payment_Method.\n"
            "Return structured output.\n\n"
            f"Payload format: {payload_mode}\n"
            f"Payload:\n{payload_text}\n\n"
            f"Original question: {question}"
        )
        provider, report = self.router.invoke_structured(prompt, InsightReport)
        return provider, report

    def ask(self, question: str) -> dict[str, Any]:
        planner_provider, plan = self._plan_analysis(question)

        sql_provider = ""
        sql = ""
        columns: list[str] = []
        rows: list[list[Any]] = []
        relevance_provider = ""
        relevance_feedback = ""

        for _ in range(3):
            sql_provider, sql = self._build_sql(question, plan, relevance_feedback)
            columns, rows = self.warehouse.run(sql)
            relevance_provider, verdict = self._judge_relevance(
                question, plan, sql, columns, rows
            )
            if verdict.relevant:
                break
            relevance_feedback = verdict.feedback

        payload = self._to_payload(question, sql, columns, rows)
        payload_mode, payload_text = self._choose_payload(payload)
        analysis_provider, report = self._analyze(question, payload_mode, payload_text)

        return {
            "question": question,
            "planner_provider": planner_provider,
            "relevance_provider": relevance_provider,
            "sql_provider": sql_provider,
            "analysis_provider": analysis_provider,
            "analysis_plan": plan.model_dump(),
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "payload_mode": payload_mode,
            "payload": payload_text,
            "report": report.model_dump(),
        }


def build_default_assistant(
    toon_threshold_chars: int = 2200,
    preferred_provider: str = "openai",
    openai_model: str = "gpt-4o-mini",
    groq_model: str = "openai/gpt-oss-120b",
    openrouter_model: str = "openai/gpt-oss-120b:free",
) -> RestaurantInsightsAssistant:
    load_dotenv()
    _enable_langchain_tracing()
    base_dir = Path(__file__).resolve().parent.parent
    config = AssistantConfig(
        csv_path=base_dir / "9. Sales-Data-Analysis.csv",
        toon_threshold_chars=toon_threshold_chars,
        preferred_provider=preferred_provider,
        openai_model=openai_model,
        groq_model=groq_model,
        openrouter_model=openrouter_model,
    )
    return RestaurantInsightsAssistant(config)
