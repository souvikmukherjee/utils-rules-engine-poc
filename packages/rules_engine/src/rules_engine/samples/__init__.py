from __future__ import annotations

import json
from importlib import resources

from rules_engine.models import RulePack


def load_lounge_pack() -> RulePack:
    text = resources.files("rules_engine.samples").joinpath("lounge_pack.json").read_text(
        encoding="utf-8"
    )
    return RulePack.from_dict(json.loads(text))
