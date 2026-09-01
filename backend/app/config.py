import os

from dotenv import load_dotenv

load_dotenv()

# Comma-separated list of origins allowed to call this API (e.g. the Vite dev server).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Dev.to's public articles API — no API key required for reading articles.
# Configurable (not secret) so it can be overridden for testing.
DEV_TO_API_BASE_URL = os.getenv("DEV_TO_API_BASE_URL", "https://dev.to/api")

# Groq API (used for AI-generated learning content — see app/services/ai_service.py).
# No default for the key: it's a secret and must come from .env. None if unset —
# the AI service checks for that and fails cleanly rather than crashing at import.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Authentication (Phase 14). JWT_SECRET_KEY is what makes a token
# unforgeable — required, no default, must come from .env (like
# DATABASE_URL, the app can't meaningfully run without it once auth exists).
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
# No refresh tokens this phase (see docs/architecture.md) — a longer expiry
# means fewer forced re-logins during a dev session, at the cost of a
# slightly longer window if a token were ever stolen.
JWT_EXPIRE_MINUTES = 60 * 24
