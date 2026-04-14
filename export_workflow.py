from pathlib import Path

from assistant.graph import save_workflow_image


def main() -> None:
    output = Path(__file__).resolve().parent / "assets" / "langgraph_workflow.png"
    path = save_workflow_image(output)
    print(f"Saved workflow image: {path}")


if __name__ == "__main__":
    main()
