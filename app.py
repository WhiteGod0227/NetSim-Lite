"""Vercel ASGI entrypoint: built React frontend and FastAPI on one origin."""
from backend.production import create_app

app = create_app()
