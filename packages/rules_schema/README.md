# Rule pack schema

Pack versions stored by the API are **platform envelopes** around a [GoRules JSON Decision Model (JDM)](https://docs.gorules.io/developers/jdm/standard):

- **Platform fields** (evaluated / governed by Axiom): `domain`, `pack_id`, `version`, `lifecycle`
- **JDM fields** (executed by [GoRules Zen](https://docs.gorules.io/developers/sdks/python)): `nodes`, `edges`

Zen ignores unknown top-level fields, so governance metadata can ride alongside the executable graph.

See [`rule-pack.schema.json`](./rule-pack.schema.json).
