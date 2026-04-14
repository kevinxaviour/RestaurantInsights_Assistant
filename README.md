# Restaurant Insights Assistant (OOP + LangGraph + Streamlit)

This implementation was refactored from notebook-style code into a professional multi-file Python design.

## What was done

- Split logic into multiple modules under `Restaurant_Sector/assistant`:
  - `config.py` -> assistant configuration
  - `providers.py` -> OpenAI primary and Groq/OpenRouter fallback router
  - `warehouse.py` -> CSV to in-memory SQLite loader and query executor
  - `formatters.py` -> payload formatters (`JSON` and `TOON`)
  - `service.py` -> main orchestration service (`RestaurantInsightsAssistant`)
  - `graph.py` -> LangGraph workflow compile and image export
- Added CLI entrypoint: `Restaurant_Sector/restaurant_insights_assistant.py`.
- Added Streamlit UI: `Restaurant_Sector/streamlit_app.py`.
- Added workflow export script: `Restaurant_Sector/export_workflow.py`.
- Saved LangGraph image to: `Restaurant_Sector/assets/langgraph_workflow.png`.

## LLM provider order

1. OpenAI (primary)
2. Groq (fallback)
3. OpenRouter (fallback)

The router attempts providers in order for both SQL planning and final analysis.

## Structured outputs and TOON

- SQL planning output schema: `SQLPlan`
- Final analysis schema: `InsightReport`
- Intermediate data packet schema: `QueryPayload`
- Payload delivery mode:
  - `JSON` when payload size is normal
  - `TOON` (Token Optimized Object Notation) when JSON is large

TOON is a compact line format designed to reduce prompt tokens while preserving structured content.

## Accuracy guardrails added

- Date boundary enforcement uses dataset min/max date from the loaded CSV.
- The assistant is instructed to never reason beyond the available range.
- LLM-driven planning step creates an analysis plan first (objective, metric, dimensions, period logic).
- ReAct-style refinement loop validates SQL relevance and regenerates SQL with feedback up to 3 iterations.
- For driver questions, planner is instructed to include `Purchase_Type` and `Payment_Method` when needed.

## Environment variables

Set at least one key (OpenAI strongly recommended):

- `OPENAI_API_KEY`
- `GROQ_API_KEY`
- `OPENROUTER_API_KEY`

## Run instructions

Install dependencies first (`requirements.txt` / `pyproject.toml`).

### 1) CLI mode

```bash
python Restaurant_Sector/restaurant_insights_assistant.py
```

Expected output sections:

- Provider used for SQL generation
- Provider used for final analysis
- Generated SQL query
- Structured payload (`JSON` or `TOON`)
- Structured insight report

### 2) Streamlit UI

```bash
streamlit run Restaurant_Sector/streamlit_app.py
```

Expected UI behavior:

- Ask a business question
- See generated SQL
- See payload mode and payload body
- See final insights (`executive_summary`, findings, risks, actions)
- View workflow image on the right panel

### 3) Export LangGraph workflow image

```bash
python Restaurant_Sector/export_workflow.py
```

Expected result:

- PNG generated at `Restaurant_Sector/assets/langgraph_workflow.png`

## LangGraph workflow stages

`plan_sql -> run_sql -> format_payload -> analyze -> END`
