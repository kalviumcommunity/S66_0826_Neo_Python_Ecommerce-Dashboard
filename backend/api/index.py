"""Vercel's standard FastAPI entrypoint.

Importing through this module ensures the application is loaded as the
``server.main`` package, so its absolute imports work in Vercel Functions.
"""

from server.main import app

