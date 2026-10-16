from app.services.types import is_numeric, is_temporal

CHARTS = {"bar", "line", "pie", "area", "scatter"}
MAX_POINTS = 200


def recommend(columns: list[dict], rows: list[list], hint: dict | None = None) -> dict | None:
    """Return {type,x,y,title?} referencing real result columns, or None (table only)."""
    if len(columns) < 2 or len(rows) < 2 or len(rows) > MAX_POINTS:
        return None
    types = {c["name"]: c["type"] for c in columns}
    valid = _validate_hint(hint, types, len(rows))
    return valid or _heuristic(columns, len(rows))


def _validate_hint(hint, types, n_rows) -> dict | None:
    if not isinstance(hint, dict) or hint.get("type") not in CHARTS:
        return None
    x, ys = hint.get("x"), hint.get("y")
    ys = [ys] if isinstance(ys, str) else ys
    if x not in types or not ys or not all(y in types and is_numeric(types[y]) for y in ys):
        return None
    if hint["type"] == "pie" and (len(ys) != 1 or n_rows > 12):
        return None
    if hint["type"] == "scatter" and not is_numeric(types[x]):
        return None
    out = {"type": hint["type"], "x": x, "y": list(ys)}
    if isinstance(hint.get("title"), str):
        out["title"] = hint["title"][:120]
    return out


def _heuristic(columns, n_rows) -> dict | None:
    nums = [c["name"] for c in columns if is_numeric(c["type"])]
    cats = [c for c in columns if not is_numeric(c["type"])]
    if not nums:
        return None
    if not cats:
        return {"type": "scatter", "x": nums[0], "y": [nums[1]]} if len(nums) >= 2 else None
    x = cats[0]
    kind = "line" if is_temporal(x["type"]) else "bar"
    return {"type": kind, "x": x["name"], "y": nums[:3]}
