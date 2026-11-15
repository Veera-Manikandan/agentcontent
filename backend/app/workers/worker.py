"""Redis Streams worker. Start with: python -m app.workers.worker"""
import asyncio, json, time
from redis import Redis
from sqlalchemy import select
from app.config import settings
from app.database import SessionLocal
from app.models import Post, Agent, RoutingLog
from app.services.matching import find_matches
from app.services.webhook import deliver_webhook

r=Redis.from_url(settings.redis_url,decode_responses=True)
STREAM="agentconnect:events"; GROUP="routing-workers"; CONSUMER="worker-1"

def ensure_group():
    try: r.xgroup_create(STREAM,GROUP,id="0",mkstream=True)
    except Exception: pass

async def handle(post_id):
    db=SessionLocal()
    try:
        post=db.get(Post,post_id)
        if not post: return
        author=db.get(Agent,post.author_agent_id)
        matches=await find_matches(db,post,author)
        for item in matches:
            agent=item["agent"]
            payload={"event":"post.published","post":{"id":str(post.id),"title":post.title,"content":post.content},
                     "author":{"id":str(author.id),"company_name":author.company_name},
                     "match":{"score":round(item["rerank_score"],4)}}
            status=await deliver_webhook(agent,payload)
            item["log"].status=status
        db.commit()
    finally: db.close()

async def main():
    ensure_group(); print("AgentConnect routing worker started")
    while True:
        batches=r.xreadgroup(GROUP,CONSUMER,{STREAM: ">"},count=10,block=5000)
        for _,messages in batches:
            for message_id,fields in messages:
                try: await handle(fields["post_id"])
                except Exception as exc: print("routing error:",exc)
                finally: r.xack(STREAM,GROUP,message_id)

if __name__=="__main__": asyncio.run(main())
