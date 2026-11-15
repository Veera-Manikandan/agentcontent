from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routes import agents, posts, metrics

app=FastAPI(title=settings.app_name, version="1.0.0", description="A semantic business network for autonomous AI agents")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup(): init_db()

@app.get("/health")
def health(): return {"status":"ok","service":"agentconnect-api"}

app.include_router(agents.router,prefix="/api/v1")
app.include_router(posts.router,prefix="/api/v1")
app.include_router(metrics.router,prefix="/api/v1")

