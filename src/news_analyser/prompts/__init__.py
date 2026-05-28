"""Prompt loader – reads .md files from the prompts/ package directory.

Supports {{PLACEHOLDER}} substitution via the optional context dict:
    load_prompt("system", "pass2", context={"ROLES": "..."})
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(category: str, name: str, context: dict | None = None) -> str:
    """Return the content of prompts/<category>/<name>.md as a string.

    Args:
        category: Subdirectory name (e.g. "system").
        name:     File name without extension (e.g. "pass2").
        context:  Optional dict of {{KEY}} → value replacements.
    """
    path = _PROMPTS_DIR / category / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    if context:
        for key, value in context.items():
            text = text.replace(f"{{{{{key}}}}}", value)
    return text
