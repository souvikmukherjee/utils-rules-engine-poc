from fastapi.testclient import TestClient

from rules_api.main import app


def test_benchmark_run_and_compare(tmp_path, monkeypatch):
    db = tmp_path / "bench.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    # Force fresh store
    import rules_api.main as main

    main._store = None
    main._bench_store = None
    main._conn_ref = None

    client = TestClient(app)
    resp = client.post(
        "/v1/benchmark/run",
        json={
            "column_count": 4,
            "rule_count": 40,
            "fire_count": 100,
            "seed": 9,
            "label": "unit-cell",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["kind"] == "single"
    assert body["result"]["parity"]["agree_pct"] == 100.0

    compare = client.get("/v1/benchmark/compare")
    assert compare.status_code == 200
    data = compare.json()
    assert data["row_count"] >= 1
    assert data["summary"]["cells"] >= 1
