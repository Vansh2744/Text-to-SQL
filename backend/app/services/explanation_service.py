import json

from app.services.llm_service import LLMError, LLMProvider

SYSTEM = (
    "You explain query results to non-technical users in 1-3 sentences. Use ONLY the data "
    'provided; never speculate or add outside facts. Reply with JSON: {"explanation": "..."}'
)


def explain(provider: LLMProvider, question: str, columns: list[dict], rows: list[list],
            truncated: bool) -> str:
    """Grounded explanation; falls back to a deterministic summary if the LLM fails."""
    if not rows:
        return "The query returned no rows."
    fallback = f"The query returned {len(rows)} row(s) with columns: " + ", ".join(
        c["name"] for c in columns) + ("." if not truncated else " (results were truncated).")
    payload = {"question": question[:1000], "columns": [c["name"] for c in columns],
               "rows": rows[:20], "rows_returned": len(rows), "truncated": truncated}
    try:
        data = json.loads(provider.complete(SYSTEM, json.dumps(payload, default=str)))
        text = data.get("explanation")
        if isinstance(text, str) and text.strip():
            return text.strip()[:1000]
    except (LLMError, json.JSONDecodeError, AttributeError):
        pass
    return fallback
