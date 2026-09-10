"""FastAPI application entrypoint (forwarding to server.main)."""

from __future__ import annotations

from server.main import app, health_check, main

__all__ = ["app", "health_check", "main"]


if __name__ == "__main__":
    main()
