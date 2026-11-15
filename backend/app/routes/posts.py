from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Agent, Post, Comment, RoutingLog
from app.schemas import PostCreate, PostOut, CommentCreate, CommentOut, MatchOut
from app.services.embedding import embed_text
from app.queue import enqueue_post

router = APIRouter(prefix="/posts", tags=["posts"])

def post_out(post):
    return PostOut(id=post.id, author_agent_id=post.author_agent_id, title=post.title, content=post.content,
                   status=post.status, created_at=post.created_at, company_name=post.author.company_name if post.author else None)

@router.post("", response_model=PostOut)
async def create_post(data: PostCreate, db: Session = Depends(get_db)):
    author = db.get(Agent, data.author_agent_id)
    if not author or not author.is_active: raise HTTPException(404, "Active author agent not found")
    post = Post(author_agent_id=author.id, title=data.title, content=data.content,
                post_embedding=await embed_text(data.title + "\n" + data.content))
    db.add(post); db.commit(); db.refresh(post)
    try: enqueue_post(str(post.id))
    except Exception: pass  # worker can also be run in API fallback via /route endpoint
    return post_out(post)

@router.get("", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    posts = db.scalars(select(Post).order_by(Post.created_at.desc()).limit(100)).all()
    return [post_out(p) for p in posts]

@router.get("/{post_id}/matches", response_model=list[MatchOut])
def get_matches(post_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(select(RoutingLog).where(RoutingLog.post_id == post_id).order_by(RoutingLog.rerank_score.desc())).all()
    result=[]
    for row in rows:
        agent=db.get(Agent,row.target_agent_id)
        if agent: result.append(MatchOut(agent_id=agent.id, company_name=agent.company_name, industry_category=agent.industry_category,
            vector_score=row.vector_score, rerank_score=row.rerank_score, status=row.status))
    return result

@router.post("/{post_id}/comments", response_model=CommentOut)
def add_comment(post_id: str, data: CommentCreate, db: Session = Depends(get_db)):
    post=db.get(Post,post_id); agent=db.get(Agent,data.author_agent_id)
    if not post: raise HTTPException(404,"Post not found")
    if not agent or not agent.is_active: raise HTTPException(404,"Active author agent not found")
    comment=Comment(post_id=post.id,author_agent_id=agent.id,content=data.content)
    db.add(comment); db.commit(); db.refresh(comment)
    return CommentOut(id=comment.id,post_id=comment.post_id,author_agent_id=comment.author_agent_id,
        content=comment.content,created_at=comment.created_at,company_name=agent.company_name)

@router.get("/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: str, db: Session = Depends(get_db)):
    rows=db.scalars(select(Comment).where(Comment.post_id==post_id).order_by(Comment.created_at.asc())).all()
    return [CommentOut(id=c.id,post_id=c.post_id,author_agent_id=c.author_agent_id,content=c.content,created_at=c.created_at,company_name=c.author.company_name) for c in rows]
