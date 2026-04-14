import json

from assistant.service import build_default_assistant


def main() -> None:
    assistant = build_default_assistant()
    question = input("Ask restaurant insight question: ").strip()
    result = assistant.ask(question)

    print("\n=== Providers ===")
    print(f"SQL Provider      : {result['sql_provider']}")
    print(f"Analysis Provider : {result['analysis_provider']}")

    print("\n=== SQL ===")
    print(result["sql"])

    print(f"\n=== Structured Payload ({result['payload_mode']}) ===")
    print(result["payload"])

    print("\n=== Insights ===")
    print(json.dumps(result["report"], indent=2))


if __name__ == "__main__":
    main()
