"""
Analysis agents — pipeline orchestration on top of connectors/.

Currently:
    analyze_article  — two-pass LLM analysis (Pass 1: anonymised, Pass 2: original)
"""

from .analyzer import analyze_article

__all__ = ["analyze_article"]
