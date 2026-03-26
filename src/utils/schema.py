import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_DIR = PROJECT_ROOT / "prompt" / "json_schema"
PROMPT_DIR = PROJECT_ROOT / "prompt" / "system"

# Default system prompt files per step
_DEFAULT_PROMPTS = {
    "chart_review": "system_prompt_chart_review_2.txt",
    "feedback": "system_prompt_feedback_1_sans_json.txt",
}


def load_schema(name: str, version: str = "v2") -> dict:
    """Load a JSON schema by name and version.

    Args:
        name: Schema name ('chart_review' or 'cr_feedback').
        version: 'v1' or 'v2'. v1 loads the original file, v2 loads the _v2 variant.

    Returns:
        Parsed JSON schema dict.
    """
    suffix = f"_{version}" if version != "v1" else ""
    filename = f"{name}{suffix}.json"
    path = SCHEMA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_system_prompt(step: str, path: Optional[str] = None) -> str:
    """Load a system prompt for a given pipeline step.

    Args:
        step: 'chart_review' or 'feedback'.
        path: Optional explicit path override.

    Returns:
        System prompt text.
    """
    if path:
        prompt_path = Path(path)
    else:
        filename = _DEFAULT_PROMPTS.get(step)
        if not filename:
            raise ValueError(f"Unknown step '{step}'. Valid steps: {list(_DEFAULT_PROMPTS.keys())}")
        prompt_path = PROMPT_DIR / filename

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
