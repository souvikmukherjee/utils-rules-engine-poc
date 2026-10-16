from __future__ import annotations

import json
from importlib import resources

from rules_engine.models import RulePack
from rules_engine.samples.build_lounge_jdm import build_lounge_pack


def load_lounge_pack() -> RulePack:
    return RulePack.from_dict(build_lounge_pack())


def load_sample_pack(filename: str) -> RulePack:
    text = resources.files("rules_engine.samples").joinpath(filename).read_text(
        encoding="utf-8"
    )
    return RulePack.from_dict(json.loads(text))


def load_loyalty_pack() -> RulePack:
    return load_sample_pack("loyalty_pack.json")


def load_banking_pack() -> RulePack:
    return load_sample_pack("banking_pack.json")


def load_ops_pack() -> RulePack:
    return load_sample_pack("ops_pack.json")


def load_airports_pack() -> RulePack:
    return load_sample_pack("airports_pack.json")


def all_seed_packs() -> list[RulePack]:
    return [
        load_lounge_pack(),
        load_loyalty_pack(),
        load_banking_pack(),
        load_ops_pack(),
        load_airports_pack(),
    ]
