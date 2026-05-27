"""Root-level entry point. Delegates to the package main."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from news_analyser.main import main

if __name__ == "__main__":
    main()
