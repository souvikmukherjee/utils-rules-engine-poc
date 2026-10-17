from rules_engine.benchmark import generate_pack, match_dmn_table, run_benchmark


def test_generate_pack_deterministic():
    a = generate_pack(column_count=5, rule_count=50, seed=7)
    b = generate_pack(column_count=5, rule_count=50, seed=7)
    assert a.jdm == b.jdm
    assert len(a.rules) == 51  # + default catch-all


def test_dmn_table_matches_catch_all():
    pack = generate_pack(column_count=3, rule_count=10, seed=3)
    facts = {col: "__miss__" for col in pack.columns}
    out = match_dmn_table(pack, facts)
    assert out["decision"] == "inconclusive"
    assert out["rule_id"] == "r_default"


def test_zen_dmn_parity_small():
    result = run_benchmark(
        column_count=6,
        rule_count=80,
        fire_count=200,
        seed=11,
        parity_sample=200,
    )
    assert result["parity"]["agree_pct"] == 100.0
    engines = {e["engine"]: e for e in result["engines"]}
    assert engines["zen"]["fires"] == 200
    assert engines["dmn_table"]["fires"] == 200
