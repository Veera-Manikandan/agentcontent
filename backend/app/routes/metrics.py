from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models import Agent, Post, RoutingLog, Comment
router=APIRouter(prefix="/metrics",tags=["metrics"])
@router.get("")
def metrics(db: Session=Depends(get_db)):
    return {"agents":db.scalar(select(func.count()).select_from(Agent)) or 0,
            "active_agents":db.scalar(select(func.count()).select_from(Agent).where(Agent.is_active.is_(True))) or 0,
            "posts":db.scalar(select(func.count()).select_from(Post)) or 0,
            "notifications":db.scalar(select(func.count()).select_from(RoutingLog)) or 0,
            "comments":db.scalar(select(func.count()).select_from(Comment)) or 0}
