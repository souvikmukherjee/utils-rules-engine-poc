package com.axiom.compare.service;

import com.axiom.compare.model.ComparisonNotes;
import com.axiom.compare.model.ComparisonNotes.Dimension;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class ComparisonNotesService {

  public ComparisonNotes notes() {
    Map<String, Dimension> dimensions = new LinkedHashMap<>();
    dimensions.put(
        "ease_of_implementation",
        new Dimension(
            "In-process Python binding (`zen-engine`) inside FastAPI; JDM packs live in SQLite and are authored in the shared JDM editor. From Spring, one RestClient POST to `/v1/evaluate` with `engine=zen` is enough — no DMN tooling, no code gen.",
            "Quarkus + `drools-quarkus-decisions` auto-exposes REST from `LoungeAccess.dmn`. Almost no handwritten Java. From Spring, either call the platform with `engine=kogito` or POST flat facts to `:8081/LoungeAccess`. DMN authoring is a separate editor/format from the JDM UI.",
            "Platform path is equally easy for both. Native engine ownership differs: Zen stays in the Python adapter + JDM; Kogito is a tiny Quarkus service seeded with DMN."));
    dimensions.put(
        "speed_of_execution",
        new Dimension(
            "Zen evaluates in-process inside the API (native Rust core via Python). Trace may include `zen_performance`. Spring wall time still includes FastAPI RTT.",
            "Kogito evaluates inside Quarkus (Drools DMN). Platform path adds FastAPI mapping RTT; `direct-kogito` mode measures Quarkus alone.",
            "Use POST `/v1/compare/benchmark` for p50/p95. Prefer `mode=platform` for fair platform cost; `mode=direct-kogito` to isolate Quarkus."));
    dimensions.put(
        "hot_reload",
        new Dimension(
            "Rule content: publish a new pack version (or edit draft) — next evaluate picks it up with no process restart. Adapter code: `uvicorn --reload` watching `apps/api` and `packages/rules_engine`.",
            "Rule content: edit `LoungeAccess.dmn` under `quarkus:dev` (`make kogito`) — Quarkus live-reloads resources. Production image rebuild required for DMN changes.",
            "Zen pack hot-path is DB-backed publish; Kogito hot-path is Quarkus Dev Mode file reload. Measure with the hot-reload probe after changing rules."));
    dimensions.put(
        "authoring_format",
        new Dimension(
            "GoRules JDM (`nodes`/`edges`) in the Axiom UI.",
            "OMG DMN 1.2 XML (`LoungeAccess.dmn`).",
            "Same business domain today does not imply identical rule fidelity — lounge JDM is richer than the seeded DMN."));
    dimensions.put(
        "spring_boot_integration",
        new Dimension(
            "Call platform HTTP, or embed `io.gorules:zen-engine` (JDK 22+ FFM) for in-process Java evaluation of JDM.",
            "Call Quarkus HTTP from Spring, or embed Drools DMN in the same JVM (heavier footprint).",
            "This harness stays HTTP-only so both engines share the same Spring RestClient surface and JDK 21."));

    return new ComparisonNotes(
        "Spring Boot comparison harness for Axiom: invoke GoRules Zen and Kogito one after the other, capture wall latency, decision agreement, and qualitative trade-offs.",
        dimensions,
        List.of(
            "Start `make kogito`, `make api`, then `make spring-compare`.",
            "GET `/v1/compare/health` until both backends are up.",
            "POST `/v1/compare` with lounge facts — Zen runs first, then Kogito via the platform.",
            "POST `/v1/compare?mode=direct-kogito` to time Quarkus DMN without FastAPI on the Kogito leg.",
            "POST `/v1/compare/benchmark?iterations=50` for p50/p95.",
            "Hot reload: change Zen pack (Author UI / pack API) or Kogito DMN (`make kogito` Dev Mode), then POST `/v1/compare/hot-reload/probe` before/after to observe first-hit latency."),
        List.of(
            "Zen and Kogito lounge models are intentionally not feature-parity; decision disagreements are expected for cabin-heavy scenarios.",
            "Wall times include network + serialization; they are comparative, not micro-benchmarks of the native engines alone.",
            "In-process Zen Java SDK requires JDK 22+; this app targets JDK 21 and calls Zen through the existing FastAPI runtime."));
  }

  public List<String> shortRuntimeNotes(String mode) {
    if (EngineCompareService.MODE_DIRECT_KOGITO.equals(mode)) {
      return List.of(
          "mode=direct-kogito: Zen via FastAPI; Kogito via Quarkus /LoungeAccess.",
          "See GET /v1/compare/notes for ease / speed / hot-reload write-up.");
    }
    return List.of(
        "mode=platform: both engines via FastAPI `engine` toggle.",
        "See GET /v1/compare/notes for ease / speed / hot-reload write-up.");
  }
}
