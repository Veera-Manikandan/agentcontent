
import re

from google import genai
from app.config import settings


async def rerank_score(
    post_title: str,
    post_content: str,
    manifesto: str,
    vector_score: float
) -> float:
    """Calculate business relevance using Gemini."""

    if settings.gemini_api_key:
        try:
            client = genai.Client(
                api_key=settings.gemini_api_key
            )

            prompt = f"""
You are a business-to-business agent matching evaluator.

Evaluate whether this company should receive this post.

Return ONLY one decimal number between 0.0 and 1.0.

Post title: {post_title[:500]}
Post content: {post_content[:3000]}
Agent interests: {manifesto[:3000]}

Consider:
- Business relevance
- Shared customer interests
- Partnership opportunities
- Marketing opportunities
- Payment or promotional opportunities
"""

            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt
            )

            match = re.search(
                r"\b(?:0(?:\.\d+)?|1(?:\.0+)?)\b",
                response.text or ""
            )

            if match:
                return max(0.0, min(1.0, float(match.group())))

        except Exception as error:
            print(f"Gemini reranking failed: {error}")

    # Fallback scoring
    post_words = set(
        (post_title + " " + post_content).lower().split()
    )

    agent_words = set(manifesto.lower().split())

    overlap = len(post_words & agent_words) / max(1, len(post_words))

    return max(
        0.0,
        min(1.0, 0.75 * float(vector_score) + 0.25 * overlap)
    )
