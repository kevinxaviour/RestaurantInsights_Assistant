from pathlib import Path

import streamlit as st

from assistant.graph import save_workflow_image
from assistant.service import build_default_assistant


st.set_page_config(page_title="Restaurant Insights Assistant", layout="wide")
st.title("Restaurant Insights Assistant")
st.caption(
    "Configurable provider/model routing with fallback and structured payload pipeline"
)


@st.cache_resource
def get_assistant(toon_threshold_chars: int):
    return build_default_assistant(
        toon_threshold_chars=toon_threshold_chars,
    )


@st.cache_data
def get_workflow_image_path() -> str:
    output = Path(__file__).resolve().parent / "assets" / "langgraph_workflow.png"
    save_workflow_image(output)
    return str(output)


threshold = st.sidebar.slider(
    "TOON threshold (chars)", min_value=500, max_value=5000, value=2200, step=100
)
show_graph = st.sidebar.checkbox("Graph Viewer", value=False)

question = st.text_area(
    "Business Question",
    value="Compare total revenue between November and December.",
    height=120,
)

if st.button("Generate Insights", type="primary"):
    if not question.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("Running SQL planning, retrieval, and analysis..."):
            assistant = get_assistant(threshold)
            result = assistant.ask(question.strip())

        with st.expander("LLM Analysis Plan"):
            st.json(result["analysis_plan"])

        st.subheader("Generated SQL")
        st.code(result["sql"], language="sql")

        st.subheader(f"Structured Payload ({result['payload_mode']})")
        st.code(result["payload"], language="text")

        st.subheader("Insights")
        report = result["report"]
        st.markdown(f"**Executive Summary:** {report['executive_summary']}")
        st.markdown("**Key Findings**")
        for item in report["key_findings"]:
            st.write(f"- {item}")
        st.markdown("**Risks / Gaps**")
        for item in report["risks_or_gaps"]:
            st.write(f"- {item}")
        st.markdown("**Actions**")
        for item in report["actions"]:
            st.write(f"- {item}")

if show_graph:
    st.subheader("LangGraph Workflow")
    try:
        image_path = get_workflow_image_path()
        st.image(image_path, use_container_width=True)
        st.caption(f"Saved at: {Path(image_path).as_posix()}")
    except Exception as exc:
        st.warning(f"Workflow image generation failed: {exc}")
