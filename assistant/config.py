from dataclasses import dataclass
from pathlib import Path


@dataclass
class AssistantConfig:
    csv_path: Path
    sqlite_table: str = "hoteldata"
    preferred_provider: str = "openai"
    openai_model: str = "gpt-4o-mini"
    groq_model: str = "openai/gpt-oss-120b"
    openrouter_model: str = "openai/gpt-oss-120b:free"
    toon_threshold_chars: int = 2200
