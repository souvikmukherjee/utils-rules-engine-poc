from rules_engine.conditions import eval_condition, get_path


def test_get_path_nested():
    assert get_path({"a": {"b": 1}}, "a.b") == 1
    assert get_path({"a": {}}, "a.b") is None


def test_ops_eq_neq_in_contains_exists():
    facts = {"tier": "gold", "tags": ["a", "b"], "score": 10}
    assert eval_condition({"path": "tier", "op": "eq", "value": "gold"}, facts)
    assert eval_condition({"path": "tier", "op": "neq", "value": "silver"}, facts)
    assert eval_condition({"path": "tier", "op": "in", "value": ["gold", "plat"]}, facts)
    assert eval_condition({"path": "tags", "op": "contains", "value": "a"}, facts)
    assert eval_condition({"path": "tier", "op": "exists", "value": True}, facts)
    assert not eval_condition({"path": "missing", "op": "exists", "value": True}, facts)


def test_ops_comparisons():
    facts = {"n": 5}
    assert eval_condition({"path": "n", "op": "gt", "value": 4}, facts)
    assert eval_condition({"path": "n", "op": "gte", "value": 5}, facts)
    assert eval_condition({"path": "n", "op": "lt", "value": 6}, facts)
    assert eval_condition({"path": "n", "op": "lte", "value": 5}, facts)
    assert not eval_condition({"path": "n", "op": "gt", "value": 5}, facts)


def test_combinators_all_any_not():
    facts = {"a": 1, "b": 2}
    assert eval_condition(
        {
            "all": [
                {"path": "a", "op": "eq", "value": 1},
                {"path": "b", "op": "eq", "value": 2},
            ]
        },
        facts,
    )
    assert eval_condition(
        {
            "any": [
                {"path": "a", "op": "eq", "value": 9},
                {"path": "b", "op": "eq", "value": 2},
            ]
        },
        facts,
    )
    assert eval_condition(
        {"not": {"path": "a", "op": "eq", "value": 9}},
        facts,
    )
