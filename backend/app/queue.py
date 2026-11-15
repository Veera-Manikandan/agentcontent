import json
from redis import Redis
from app.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
STREAM = "agentconnect:events"

def enqueue_post(post_id: str):
    redis_client.xadd(STREAM, {"event":"post.published", "post_id":post_id})
