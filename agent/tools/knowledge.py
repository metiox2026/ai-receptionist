"""Knowledge base tools — P1.

search_knowledge: vector search against the `knowledge_items` table.
log_unanswered: capture questions the agent could not answer so the dashboard
can suggest FAQ entries to add.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


def search_knowledge_tool() -> dict[str, Any]:
    return {
        "name": "search_knowledge",
        "description": (
            "Look up an answer in the business's knowledge base. Use this when "
            "the caller asks something not in your system prompt. Return only "
            "what the knowledge base says; do not invent."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to search for.",
                },
            },
            "required": ["query"],
        },
    }


def log_unanswered_tool() -> dict[str, Any]:
    return {
        "name": "log_unanswered",
        "description": (
            "Record that the agent could not answer this question. Use this "
            "before offering the caller a message or transfer."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question the agent could not answer.",
                },
            },
            "required": ["question"],
        },
    }


async def handle_search(
    *,
    business_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    query = (args.get("query") or "").strip()
    if not query:
        return {"ok": False, "error": "query is required"}

    logger.info("search_knowledge", business_id=business_id, query=query)
    # TODO: pgvector cosine search over knowledge_items. Return top 3 snippets.
    return {"ok": True, "results": []}


async def handle_log_unanswered(
    *,
    business_id: str,
    call_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    question = (args.get("question") or "").strip()
    if not question:
        return {"ok": False, "error": "question is required"}

    logger.info("log_unanswered", business_id=business_id, call_id=call_id, question=question)
    # TODO: insert into knowledge_gaps table.
    return {"ok": True}