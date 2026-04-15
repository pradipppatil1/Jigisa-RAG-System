from fastapi import FastAPI
from app.ingestion.router import router as ingestion_router
from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.evaluation.router import router as evaluation_router
from app.core.database import init_db, SessionLocal
from app.auth.service import seed_demo_users

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FinBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup Event ────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    """Create all MySQL tables (idempotent) when the server starts."""
    init_db()
    # Seed predefined users. SessionLocal is safe to use here directly.
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(evaluation_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to FinBot AI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
