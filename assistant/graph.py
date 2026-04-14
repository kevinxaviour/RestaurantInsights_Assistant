from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from .service import RestaurantInsightsAssistant, build_default_assistant


class GraphState(TypedDict):
    question: str
    analysis_plan: dict[str, Any]
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    payload_mode: str
    payload: str
    sql_provider: str
    analysis_provider: str
    report: dict[str, Any]


def build_graph(assistant: RestaurantInsightsAssistant | None = None):
    service = assistant or build_default_assistant()
    graph = StateGraph(GraphState)

    def plan_sql(state: GraphState) -> GraphState:
        _, plan = service._plan_analysis(state["question"])
        provider, sql = service._build_sql(state["question"], plan)
        return {
            "analysis_plan": plan.model_dump(),
            "sql": sql,
            "sql_provider": provider,
        }

    def run_sql(state: GraphState) -> GraphState:
        columns, rows = service.warehouse.run(state["sql"])
        return {"columns": columns, "rows": rows}

    def format_payload(state: GraphState) -> GraphState:
        payload = service._to_payload(
            state["question"], state["sql"], state["columns"], state["rows"]
        )
        mode, text = service._choose_payload(payload)
        return {"payload_mode": mode, "payload": text}

    def analyze(state: GraphState) -> GraphState:
        provider, report = service._analyze(
            state["question"], state["payload_mode"], state["payload"]
        )
        return {"analysis_provider": provider, "report": report.model_dump()}

    graph.add_node("plan_sql", plan_sql)
    graph.add_node("run_sql", run_sql)
    graph.add_node("format_payload", format_payload)
    graph.add_node("analyze", analyze)

    graph.set_entry_point("plan_sql")
    graph.add_edge("plan_sql", "run_sql")
    graph.add_edge("run_sql", "format_payload")
    graph.add_edge("format_payload", "analyze")
    graph.add_edge("analyze", END)

    return graph.compile()


def save_workflow_image(
    output_path: Path, assistant: RestaurantInsightsAssistant | None = None
) -> Path:
    app = build_graph(assistant)
    png_bytes = app.get_graph().draw_mermaid_png()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes)
    return output_path
