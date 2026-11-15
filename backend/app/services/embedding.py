
import hashlib
import math

from app.config import settings


async def embed_text(text: str) -> list[float]:
    """Generate a 1536-dimensional embedding using Gemini."""

    # Gemini embedding (preferred)
    if settings.gemini_api_key:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)

        result = await client.aio.models.embed_content(
            model="gemini-embedding-001",
            contents=text[:8000],
            config=types.EmbedContentConfig(
                output_dimensionality=1536
            )
        )

        return [float(x) for x in result.embeddings[0].values]

    # OpenAI fallback
    if settings.openai_api_key:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        result = await client.embeddings.create(
            model=settings.embedding_model,
            input=text[:8000],
            dimensions=1536
        )

        return result.data[0].embedding

    # Local feature-hashing fallback
    vec = [0.0] * 1536

    words = [w.lower() for w in text.split() if w.strip()]

    for word in words:
        digest = hashlib.sha256(word.encode()).digest()
        idx = int.from_bytes(digest[:4], "big") % len(vec)
        vec[idx] += 1.0 if digest[4] % 2 else -1.0

    norm = math.sqrt(sum(x * x for x in vec)) or 1.0

    return [x / norm for x in vec]
