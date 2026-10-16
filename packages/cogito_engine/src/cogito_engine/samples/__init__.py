from __future__ import annotations

import json
from importlib import resources

from cogito_engine.models import RulePack


def load_lounge_pack() -> RulePack:
    raw = resources.files(__package__).joinpath("lounge_pack.json").read_text(encoding="utf-8")
    return RulePack.from_dict(json.loads(raw))
