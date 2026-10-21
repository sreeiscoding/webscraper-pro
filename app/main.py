"""Application entry point for the local WebScraper Pro interface."""

import sys
from pathlib import Path

# Streamlit only adds the *script's* folder to ``sys.path``, so the project
# root that contains the ``app`` package is not guaranteed to be importable.
# Locally the launcher happens to run from the project root, but on Streamlit
# Community Cloud the package cannot be found and the application fails with
# ``ModuleNotFoundError: No module named 'app'``.  Adding the project root
# here makes the absolute imports work in both environments.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui import render_app  # noqa: E402  (import must follow the path setup)


if __name__ == "__main__":
    render_app()
