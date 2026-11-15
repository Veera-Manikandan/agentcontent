import secrets, hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Agent
from app.schemas import AgentCreate, AgentOut, AgentRegistered
from app.services.embedding import embed_text

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/register", response_model=AgentRegistered)
async def register_agent(data: AgentCreate, db: Session = Depends(get_db)):
    embedding = await embed_text(data.interest_manifesto)
    raw_key = secrets.token_urlsafe(32)
    agent = Agent(company_name=data.company_name, industry_category=data.industry_category,
                  webhook_url=str(data.webhook_url) if data.webhook_url else None,
                  interest_manifesto=data.interest_manifesto, interest_embedding=embedding,
                  api_key_hash=hashlib.sha256(raw_key.encode()).hexdigest())
    db.add(agent); db.commit(); db.refresh(agent)
    result = AgentOut.model_validate(agent).model_dump()
    result["api_key"] = raw_key  # shown only once at registration
    return result

@router.get("", response_model=list[AgentOut])
def list_agents(db: Session = Depends(get_db)):
    return db.scalars(select(Agent).order_by(Agent.created_at.desc())).all()

@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent: raise HTTPException(404, "Agent not found")
    return agent
