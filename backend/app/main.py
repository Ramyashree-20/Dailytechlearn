from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import CORS_ORIGINS
from app.database import get_db
from app.routers import ai, auth, categories, chat, content, external, learning, questions, topics

app = FastAPI(title="DailyTechLearn API")
print("CORS_ORIGINS:", CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(topics.router)
app.include_router(questions.router)
app.include_router(learning.router)
app.include_router(chat.router)
app.include_router(external.router)
app.include_router(content.router)
app.include_router(ai.router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/api/db-health")
def db_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected"},
        )
    return {"status": "healthy", "database": "connected"}
