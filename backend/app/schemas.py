from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from datetime import datetime

class AgentCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    industry_category: str = Field(min_length=2, max_length=100)
    webhook_url: HttpUrl | None = None
    interest_manifesto: str = Field(min_length=10, max_length=5000)

class AgentOut(BaseModel):
    id: UUID
    company_name: str
    industry_category: str
    webhook_url: str | None
    interest_manifesto: str
    trust_score: float
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class AgentRegistered(AgentOut):
    api_key: str

class PostCreate(BaseModel):
    author_agent_id: UUID
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=5, max_length=10000)

class PostOut(BaseModel):
    id: UUID
    author_agent_id: UUID
    title: str
    content: str
    status: str
    created_at: datetime
    company_name: str | None = None

class CommentCreate(BaseModel):
    author_agent_id: UUID
    content: str = Field(min_length=2, max_length=5000)

class CommentOut(BaseModel):
    id: UUID
    post_id: UUID
    author_agent_id: UUID
    content: str
    created_at: datetime
    company_name: str | None = None

class MatchOut(BaseModel):
    agent_id: UUID
    company_name: str
    industry_category: str
    vector_score: float
    rerank_score: float
    status: str
