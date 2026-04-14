# Restaurant Insights Assistant

An AI-powered restaurant analytics assistant built with **LangChain**, **LangGraph**, and **Streamlit**.

It converts natural-language business questions into SQL over a restaurant sales CSV, validates result relevance, and returns structured executive insights.

## Live App

- Streamlit Cloud URL: `https://restaurantinsightsassistant.streamlit.app/`

## Project Structure

- `Restaurant_Sector/assistant/` - core assistant modules
  - `config.py` - configuration dataclass
  - `providers.py` - provider router with fallback chain
  - `warehouse.py` - CSV to in-memory SQLite + query execution
  - `formatters.py` - JSON/TOON payload formatters
  - `service.py` - main orchestration service
  - `graph.py` - LangGraph workflow + image export
- `Restaurant_Sector/streamlit_app.py` - Streamlit app entrypoint
- `Restaurant_Sector/restaurant_insights_assistant.py` - CLI entrypoint
- `Restaurant_Sector/export_workflow.py` - workflow image export utility

## Key Features

- Multi-provider LLM routing with fallback chain
- Structured planning (`AnalysisPlan`) before SQL generation
- SQL relevance loop (up to 3 attempts) with feedback refinement
- Compact payload mode (`TOON`) for large result sets
- Business-focused structured outputs (`InsightReport`)
- LangGraph workflow visualization
- Sidebar graph viewer toggle (graph loads only when selected)
- Optional **LangChain tracing** (auto-enabled when `LANGCHAIN_API_KEY` is present)

## Environment Variables

Set at least one provider key:

- `OPENAI_API_KEY` (recommended primary)
- `GROQ_API_KEY` (optional fallback)
- `OPENROUTER_API_KEY` (optional fallback)

Optional tracing keys:

- `LANGCHAIN_API_KEY` - enables LangChain/LangSmith tracing automatically
- `LANGCHAIN_PROJECT` - optional project name (default: `restaurant-sector`)

## Install

```bash
pip install -r requirements.txt
```

## Run Locally

CLI mode:

```bash
python Restaurant_Sector/restaurant_insights_assistant.py
```

Streamlit mode:

```bash
streamlit run Restaurant_Sector/streamlit_app.py
```

In the Streamlit sidebar, you can:

- use `Graph Viewer` to show/hide the workflow image on demand

Export workflow image:

```bash
python Restaurant_Sector/export_workflow.py
```

## Streamlit Cloud Deployment

You can deploy directly from GitHub.

1. Push the repository to GitHub.
2. In Streamlit Cloud, select app file:
   - `Restaurant_Sector/streamlit_app.py`
3. Add secrets in Streamlit Cloud settings:
   - `OPENAI_API_KEY`
   - optional: `GROQ_API_KEY`, `OPENROUTER_API_KEY`
   - optional tracing: `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`
4. Ensure `.env` is **not** committed.

## Plan and Approach Followed

- Refactored notebook-style logic into modular OOP components (`config`, `providers`, `warehouse`, `formatters`, `service`, `graph`).
- Built a staged analytics pipeline: question planning -> SQL generation -> SQL execution -> payload formatting -> insight generation.
- Added a relevance-validation loop so SQL is regenerated with feedback when the first result is incomplete.
- Kept output structured with typed schemas (`AnalysisPlan`, `SQLPlan`, `RelevanceVerdict`, `InsightReport`) for reliability.
- Added payload optimization (`JSON` or `TOON`) to control token usage on larger result sets.
- Exposed app through Streamlit with a clean UI and optional sidebar graph viewer for workflow visualization.
- Enabled LangChain tracing support (auto-on when `LANGCHAIN_API_KEY` exists) to monitor LLM runs in LangSmith.
- Deployed to Streamlit Cloud from GitHub with secret-managed API keys.

## Notes

- The assistant enforces dataset date boundaries from the CSV.
- Revenue is computed as `Price * Quantity`.
- No cost column exists; profit/loss interpretation is revenue delta only.
