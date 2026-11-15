
from sqlalchemy import select, text

from app.models import Agent, RoutingLog
from app.config import settings
from app.services.reranking import rerank_score


async def find_matches(db, post, author, limit=None):
    """
    Find relevant agents for a published post.

    Matching process:
    1. Retrieve active agents except the author.
    2. Calculate cosine similarity using pgvector.
    3. Calculate final relevance using Gemini reranking.
    4. Filter candidates using the configured threshold.
    5. Save matching results in RoutingLog.
    """

    limit = limit or settings.max_matches

    print("\n========== AGENT MATCHING STARTED ==========")
    print(f"Post: {post.title}")
    print(f"Author: {author.company_name}")
    print(f"Threshold: {settings.match_threshold}")

    # 1. Retrieve candidate agents
    query = select(Agent).where(
        Agent.is_active.is_(True),
        Agent.id != author.id
    )

    candidates = db.scalars(query).all()

    print(f"Candidate agents found: {len(candidates)}")

    scored = []

    # 2. Calculate scores for each candidate
    for agent in candidates:

        try:
            if agent.interest_embedding is None:
                print(
                    f"Skipping {agent.company_name}: "
                    "interest embedding missing"
                )
                continue

            if post.post_embedding is None:
                print("Post embedding is missing")
                continue

            # Calculate cosine similarity
            distance_query = text("""
                SELECT interest_embedding <=> CAST(:embedding AS vector)
                FROM agents
                WHERE id = :agent_id
            """)

            distance = db.execute(
                distance_query,
                {
                    "embedding": str(post.post_embedding),
                    "agent_id": str(agent.id)
                }
            ).scalar()

            if distance is None:
                print(
                    f"Skipping {agent.company_name}: "
                    "similarity calculation failed"
                )
                continue

            vector_score = max(
                0.0,
                min(1.0, 1.0 - float(distance))
            )

            # 3. Gemini reranking
            final_score = await rerank_score(
                post.title,
                post.content,
                agent.interest_manifesto,
                vector_score
            )

            print(
                f"DEBUG MATCH: {agent.company_name} | "
                f"Vector: {vector_score:.4f} | "
                f"Final: {final_score:.4f} | "
                f"Threshold: {settings.match_threshold}"
            )

            # 4. Apply matching threshold
            if final_score >= settings.match_threshold:

                scored.append(
                    (agent, vector_score, final_score)
                )

                print(
                    f"MATCH FOUND: {agent.company_name}"
                )

            else:
                print(
                    f"NOT MATCHED: {agent.company_name}"
                )

        except Exception as error:
            print(
                f"MATCHING ERROR for {agent.company_name}: {error}"
            )
            continue

    # 5. Sort by final relevance score
    scored.sort(
        key=lambda item: item[2],
        reverse=True
    )

    results = []

    # 6. Save matching records
    for agent, vector_score, final_score in scored[:limit]:

        log = RoutingLog(
            post_id=post.id,
            target_agent_id=agent.id,
            vector_score=vector_score,
            rerank_score=final_score,
            status="QUEUED"
        )

        db.add(log)

        results.append({
            "agent": agent,
            "vector_score": vector_score,
            "rerank_score": final_score,
            "log": log
        })

    db.commit()

    print(f"Total matching agents: {len(results)}")
    print("========== AGENT MATCHING COMPLETED ==========\n")

    return results
