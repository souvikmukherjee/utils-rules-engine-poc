# Kogito lounge decisions

Parallel [Kogito](https://kie.apache.org/docs/) (Drools DMN on Quarkus) service for Axiom.

## Run

```bash
# from repo root
make install-kogito
make kogito          # http://localhost:8081
```

Or:

```bash
cd apps/kogito
mvn quarkus:dev -Dquarkus.http.port=8081
```

## Evaluate

```bash
curl -s http://localhost:8081/LoungeAccess \
  -H 'content-type: application/json' \
  -d '{
    "MembershipTier": "gold",
    "PartnerEliteTier": null,
    "CompanionEligible": false,
    "AsOf": "2026-06-01"
  }'
```

Axiom’s API redirects here when the UI toggle is **Kogito** (`engine: "kogito"`, `KOGITO_URL` env, default `http://127.0.0.1:8081`).

## Model

`src/main/resources/LoungeAccess.dmn` — lounge eligibility (tier / partner elite / seasonal deny) plus companion allowance.
