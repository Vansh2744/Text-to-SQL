from app.services.visualization_service import recommend

C = lambda *p: [{"name": n, "type": t} for n, t in p]


def test_scalar_and_single_row_get_no_chart():
    assert recommend(C(("n", "BIGINT")), [[1]]) is None
    assert recommend(C(("a", "VARCHAR"), ("n", "BIGINT")), [["x", 1]]) is None


def test_time_series_is_line():
    cols = C(("month", "DATE"), ("rev", "DOUBLE"))
    assert recommend(cols, [["2025-01-01", 1.0], ["2025-02-01", 2.0]])["type"] == "line"


def test_two_numeric_is_scatter_and_too_many_points_none():
    cols = C(("a", "DOUBLE"), ("b", "DOUBLE"))
    assert recommend(cols, [[1, 2], [3, 4]])["type"] == "scatter"
    assert recommend(cols, [[1, 2]] * 500) is None


def test_pie_hint_rejected_when_too_many_categories():
    cols = C(("c", "VARCHAR"), ("v", "BIGINT"))
    rows = [[str(i), i] for i in range(20)]
    assert recommend(cols, rows, {"type": "pie", "x": "c", "y": ["v"]})["type"] == "bar"
