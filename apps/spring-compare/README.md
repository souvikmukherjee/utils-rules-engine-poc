# Axiom :: Spring Engine Compare

Spring Boot harness that **calls GoRules Zen and Kogito one after the other**, then reports decision agreement, wall-clock latency, and qualitative notes (ease of implementation, execution speed, hot reload).

It does **not** re-implement the rules engines. It orchestrates the existing Axiom runtimes:

| Engine | How this app reaches it |
|--------|-------------------------|
| **GoRules Zen** | FastAPI platform `POST /v1/evaluate` with `engine=zen` (in-process Zen inside `apps/api`) |
| **Kogito** | Same platform path with `engine=kogito`, **or** direct Quarkus `POST /LoungeAccess` on `:8081` |

```text
Spring (:8082) ──► FastAPI (:8000) ──► Zen (in-process)
                └─────────────────────► Kogito client ──► Quarkus (:8081)
   optional:    ──► Quarkus (:8081)/LoungeAccess   (mode=direct-kogito)
```

## Prerequisites

- JDK 21+
- Maven 3.9+ (3.8+ works)
- Running stack: `make kogito` and `make api` (Zen is served by the API)

## Run

```bash
# from repo root
make install-spring-compare
make spring-compare          # http://127.0.0.1:8082
```

Or:

```bash
cd apps/spring-compare
mvn spring-boot:run
```

Env overrides: `PLATFORM_URL` (default `http://127.0.0.1:8000`), `KOGITO_URL` (default `http://127.0.0.1:8081`).

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/compare/health` | Are platform + Kogito reachable? |
| `GET` | `/v1/compare/notes` | Ease / speed / hot-reload write-up |
| `POST` | `/v1/compare` | Zen **then** Kogito; side-by-side result |
| `POST` | `/v1/compare/benchmark?iterations=50` | p50/p95 wall timings |
| `POST` | `/v1/compare/hot-reload/probe` | Baseline / after-change latency stamp |

Query `mode`:

- `platform` (default) — both via FastAPI
- `direct-kogito` — Zen via FastAPI; Kogito direct to Quarkus

### Example

```bash
# health
curl -s localhost:8082/v1/compare/health | jq .

# sequential compare (default gold / economy facts)
curl -s localhost:8082/v1/compare -H 'content-type: application/json' -d '{
  "subjectId": "FF-COMPARE-1",
  "facts": {
    "membership": {"tier": "gold", "companion_eligible": false},
    "booking": {"cabin": "economy"},
    "partner": {"elite_tier": null}
  }
}' | jq '{zen: .zen.wallMillis, kogito: .kogito.wallMillis, diff: .diff}'

# isolate Quarkus on the Kogito leg
curl -s 'localhost:8082/v1/compare?mode=direct-kogito' \
  -H 'content-type: application/json' -d '{}' | jq .diff

# benchmark
curl -s 'localhost:8082/v1/compare/benchmark?iterations=30' \
  -H 'content-type: application/json' -d '{}' | jq '{zen, kogito, fasterEngine}'

# qualitative notes
curl -s localhost:8082/v1/compare/notes | jq .dimensions.ease_of_implementation
```

## Hot-reload experiment

1. `POST /v1/compare/hot-reload/probe` → save baseline wall times  
2. **Zen:** publish / update a lounge pack in the Author UI (or pack API) — no API restart  
3. **Kogito:** edit `apps/kogito/src/main/resources/LoungeAccess.dmn` while `make kogito` (`quarkus:dev`) is running  
4. Probe again and compare `wall_millis` / decisions  

## Tests

```bash
make test-spring-compare
# or: cd apps/spring-compare && mvn -q test
```

## Caveats

- Lounge **JDM (Zen)** and **DMN (Kogito)** are not feature-parity; decision disagreements on cabin-heavy cases are expected.
- Reported times are **HTTP wall clocks** from Spring, not pure native-engine micro-benchmarks.
- Optional in-process GoRules Java SDK (`io.gorules:zen-engine`) needs **JDK 22+** (FFM); this app stays on JDK 21 and calls Zen through the existing FastAPI runtime.
