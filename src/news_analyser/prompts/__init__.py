"""Prompt loader – reads .md files from the prompts/ package directory."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(category: str, name: str = "default") -> str:
    """Return the content of prompts/<category>/<name>.md as a string."""
    path = _PROMPTS_DIR / category / f"{name}.md"
    return path.read_text(encoding="utf-8")
