"""Plain HTML front end for Loanpy. Run it with: uv run flask --app web run --port 4100"""

from .app import create_app

__all__ = ["create_app"]
