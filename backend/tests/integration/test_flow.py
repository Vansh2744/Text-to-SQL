from tests.conftest import REVENUE_SQL, H

API = "/api/v1"


def analyze(client, ds, q="Revenue by region?", user="alice", **extra):
    return client.post(f"{API}/queries/analyze", headers=H(user),
                       json={"dataset_id": ds["id"], "question": q, **extra})


def test_full_flow(client, dataset):
    assert dataset["status"] == "ready" and dataset["row_count"] == 500
    schema = client.get(f"{API}/datasets/{dataset['id']}/schema", headers=H()).json()
    assert {c["name"] for c in schema["columns"]} >= {"order_date", "unit_price", "region"}
    prev = client.get(f"{API}/datasets/{dataset['id']}/preview?rows=5", headers=H()).json()
    assert len(prev["rows"]) == 5
    prof = client.get(f"{API}/datasets/{dataset['id']}/profile", headers=H()).json()
    qty = next(c for c in prof["columns"] if c["name"] == "quantity")
    assert qty["min"] == 1 and qty["max"] == 10 and qty["null_count"] == 0

    r = analyze(client, dataset)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["row_count"] == 4 and not body["truncated"] and body["attempts"] == 1
    assert body["visualization"] == {"type": "bar", "x": "region", "y": ["revenue"]}
    assert body["explanation"] == "North leads in revenue."

    hist = client.get(f"{API}/queries/history", headers=H()).json()
    assert len(hist) == 1 and hist[0]["status"] == "success"
    dash = client.get(f"{API}/dashboard", headers=H()).json()
    assert dash["dataset_count"] == 1 and dash["query_count"] == 1

    rerun = client.post(f"{API}/queries/{body['query_id']}/rerun", headers=H())
    assert rerun.status_code == 200 and rerun.json()["row_count"] == 4


def test_invalid_chart_hint_falls_back(client, dataset, llm):
    llm.sql_replies = [{"sql": REVENUE_SQL, "visualization": {"type": "bar", "x": "nope", "y": ["x"]}}]
    viz = analyze(client, dataset).json()["visualization"]
    assert viz["x"] == "region" and viz["y"] == ["revenue"]


def test_explanation_fallback_never_fabricates(client, dataset, llm):
    llm.explain_fails = True
    assert "returned 4 row(s)" in analyze(client, dataset).json()["explanation"]


def test_retry_then_success(client, dataset, llm):
    llm.sql_replies = [{"sql": "SELECT nope FROM data"}, {"sql": REVENUE_SQL}]
    body = analyze(client, dataset).json()
    assert body["attempts"] == 2
    assert "Error" in llm.prompts[1]


def test_retry_limit_and_unsafe_sql_rejected(client, dataset, llm):
    llm.sql_replies = [{"sql": "DROP TABLE data"}]
    r = analyze(client, dataset)
    assert r.status_code == 422 and r.json()["error"]["code"] == "sql_validation_failed"
    assert len(llm.prompts) == 2
    assert client.get(f"{API}/queries/history", headers=H()).json()[0]["status"] == "validation_error"


def test_edited_sql_is_validated(client, dataset):
    for sql in ["DELETE FROM data", "SELECT * FROM read_csv('/etc/passwd')", "SELECT 1; SELECT 2"]:
        r = client.post(f"{API}/queries/execute", headers=H(),
                        json={"dataset_id": dataset["id"], "sql": sql})
        assert r.status_code == 422, sql
    ok = client.post(f"{API}/queries/execute", headers=H(),
                     json={"dataset_id": dataset["id"], "sql": "SELECT count(*) AS n FROM data"})
    assert ok.json()["rows"] == [[500]] and ok.json()["visualization"] is None


def test_other_user_cannot_touch_dataset(client, dataset):
    did = dataset["id"]
    for method, path, kw in [
        ("get", f"/datasets/{did}", {}), ("get", f"/datasets/{did}/preview", {}),
        ("patch", f"/datasets/{did}", {"json": {"name": "x"}}), ("delete", f"/datasets/{did}", {}),
    ]:
        assert getattr(client, method)(API + path, headers=H("bob"), **kw).status_code == 404
    assert analyze(client, dataset, user="bob").status_code == 404
    assert client.get(f"{API}/datasets", headers=H("bob")).json() == []


def test_history_and_saved_isolated(client, dataset):
    qid = analyze(client, dataset).json()["query_id"]
    assert client.get(f"{API}/queries/{qid}", headers=H("bob")).status_code == 404
    assert client.post(f"{API}/queries/{qid}/rerun", headers=H("bob")).status_code == 404
    assert client.get(f"{API}/queries/history", headers=H("bob")).json() == []


def test_requires_auth(client):
    assert client.get(f"{API}/datasets").status_code == 401
    assert client.get(f"{API}/health").status_code == 200


def test_upload_validation(client):
    def up(name, data):
        return client.post(f"{API}/datasets/upload", files={"file": (name, data)}, headers=H())
    assert up("x.exe", b"abc").json()["error"]["code"] == "unsupported_file_type"
    assert up("e.csv", b"").status_code == 422
    assert up("fake.parquet", b"not parquet").json()["error"]["code"] == "invalid_file"
    assert up("fake.xlsx", b"not a zip").json()["error"]["code"] == "invalid_file"
    assert up("../../evil.csv", b"a,b\n1,2\n").status_code == 201
    assert len(client.get(f"{API}/datasets", headers=H()).json()) == 2


def test_saved_queries_crud_and_revalidation(client, dataset):
    did = dataset["id"]
    bad = client.post(f"{API}/saved-queries", headers=H(),
                      json={"dataset_id": did, "title": "t", "sql": "DROP TABLE data"})
    assert bad.status_code == 422
    sq = client.post(f"{API}/saved-queries", headers=H(),
                     json={"dataset_id": did, "title": "Revenue", "sql": REVENUE_SQL}).json()
    assert client.get(f"{API}/saved-queries/{sq['id']}", headers=H("bob")).status_code == 404
    assert client.patch(f"{API}/saved-queries/{sq['id']}", headers=H(),
                        json={"title": "Rev 2"}).json()["title"] == "Rev 2"
    assert client.post(f"{API}/saved-queries/{sq['id']}/run", headers=H()).json()["row_count"] == 4
    assert client.delete(f"{API}/saved-queries/{sq['id']}", headers=H()).status_code == 204


def test_conversation_followup_keeps_context_and_dataset_scope(client, dataset, llm):
    conv = client.post(f"{API}/conversations", headers=H(),
                       json={"dataset_id": dataset["id"]}).json()
    url = f"{API}/conversations/{conv['id']}/messages"
    assert client.post(url, headers=H(), json={"question": "Revenue by region"}).status_code == 200
    assert client.post(url, headers=H(), json={"question": "Top 2 only"}).status_code == 200
    assert "SUM(quantity * unit_price)" in llm.prompts[1]
    detail = client.get(f"{API}/conversations/{conv['id']}", headers=H()).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"] * 2
    assert client.get(f"{API}/conversations/{conv['id']}", headers=H("bob")).status_code == 404
    with open(__import__("tests.conftest").conftest.SAMPLE, "rb") as f:
        ds2 = client.post(f"{API}/datasets/upload", files={"file": ("b.csv", f)}, headers=H()).json()
    r = analyze(client, ds2, conversation_id=conv["id"])
    assert r.json()["error"]["code"] == "dataset_mismatch"
    assert client.delete(f"{API}/conversations/{conv['id']}", headers=H()).status_code == 204


def test_delete_dataset_removes_everything(client, dataset):
    analyze(client, dataset)
    assert client.delete(f"{API}/datasets/{dataset['id']}", headers=H()).status_code == 204
    assert client.get(f"{API}/datasets/{dataset['id']}", headers=H()).status_code == 404
    assert client.get(f"{API}/queries/history", headers=H()).json() == []


def test_llm_not_configured_is_clean_error(client, dataset):
    app = __import__("app.main", fromlist=["app"]).app
    app.dependency_overrides.pop(__import__("app.api.deps", fromlist=["get_llm"]).get_llm)
    r = analyze(client, dataset)
    assert r.status_code == 503 and r.json()["error"]["code"] == "llm_not_configured"


def test_readiness(client):
    assert client.get(f"{API}/health/ready").status_code == 200


def test_missing_dataset_file_is_clean_410(client, dataset):
    import shutil

    from app.storage import storage
    from tests.conftest import H as _H
    qid = analyze(client, dataset).json()["query_id"]
    shutil.rmtree(storage.root)
    for r in (client.post(f"{API}/queries/{qid}/rerun", headers=H()),
              client.get(f"{API}/datasets/{dataset['id']}/preview", headers=H()),
              analyze(client, dataset)):
        assert r.status_code == 410 and r.json()["error"]["code"] == "dataset_files_missing"
        assert "/" not in r.json()["error"]["message"]


def test_profile_and_preview_in_parallel(client, dataset):
    from concurrent.futures import ThreadPoolExecutor

    did = dataset["id"]
    urls = [f"{API}/datasets/{did}/profile", f"{API}/datasets/{did}/preview?rows=10"] * 6
    with ThreadPoolExecutor(8) as ex:
        codes = list(ex.map(lambda u: client.get(u, headers=H()).status_code, urls))
    assert codes == [200] * 12
