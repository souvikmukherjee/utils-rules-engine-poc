package com.axiom.compare.service;

import com.axiom.compare.client.KogitoRulesClient;
import com.axiom.compare.client.PlatformRulesClient;
import com.axiom.compare.model.CompareResponse;
import com.axiom.compare.model.CompareResponse.DiffSummary;
import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import com.axiom.compare.model.HealthResponse;
import com.axiom.compare.model.HealthResponse.BackendStatus;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.springframework.stereotype.Service;

@Service
public class EngineCompareService {

  public static final String MODE_PLATFORM = "platform";
  public static final String MODE_DIRECT_KOGITO = "direct-kogito";

  private final PlatformRulesClient platformRulesClient;
  private final KogitoRulesClient kogitoRulesClient;
  private final ComparisonNotesService notesService;

  public EngineCompareService(
      PlatformRulesClient platformRulesClient,
      KogitoRulesClient kogitoRulesClient,
      ComparisonNotesService notesService) {
    this.platformRulesClient = platformRulesClient;
    this.kogitoRulesClient = kogitoRulesClient;
    this.notesService = notesService;
  }

  /**
   * Call Zen then Kogito (one after the other) through the FastAPI platform.
   *
   * <p>Both paths share entitlements, pack resolution, and response shaping — fairest
   * apples-to-apples platform comparison.
   */
  public CompareResponse compareViaPlatform(EvaluateRequest request) {
    long start = System.nanoTime();
    EngineRunResult zen = platformRulesClient.evaluate(request, "zen");
    EngineRunResult kogito = platformRulesClient.evaluate(request, "kogito");
    return buildResponse(MODE_PLATFORM, request, zen, kogito, start);
  }

  /**
   * Call Zen via the platform, then Kogito directly on {@code :8081/LoungeAccess}.
   *
   * <p>Useful to isolate Quarkus DMN HTTP latency from FastAPI overhead.
   */
  public CompareResponse compareWithDirectKogito(EvaluateRequest request) {
    long start = System.nanoTime();
    EngineRunResult zen = platformRulesClient.evaluate(request, "zen");
    EngineRunResult kogito = kogitoRulesClient.evaluateDirect(request);
    return buildResponse(MODE_DIRECT_KOGITO, request, zen, kogito, start);
  }

  public HealthResponse health(String platformUrl, String kogitoUrl) {
    Integer platformStatus = platformRulesClient.probeStatus();
    Integer kogitoStatus = kogitoRulesClient.probeStatus();
    boolean platformUp = platformRulesClient.healthUp();
    boolean kogitoUp = kogitoRulesClient.healthUp();
    boolean ready = platformUp && kogitoUp;
    String hint =
        ready
            ? "Both backends reachable. POST /v1/compare to run Zen then Kogito."
            : "Start missing services: `make api` (Zen via FastAPI :8000) and `make kogito` (:8081).";
    return new HealthResponse(
        ready,
        new BackendStatus(platformUrl, platformUp, platformStatus, platformUp ? "ok" : "down"),
        new BackendStatus(kogitoUrl, kogitoUp, kogitoStatus, kogitoUp ? "ok" : "down"),
        hint);
  }

  private CompareResponse buildResponse(
      String mode,
      EvaluateRequest request,
      EngineRunResult zen,
      EngineRunResult kogito,
      long startNanos) {
    DiffSummary diff = diff(zen, kogito, mode);
    List<String> notes = new ArrayList<>();
    notes.add("Engines were invoked sequentially: Zen first, then Kogito.");
    notes.addAll(notesService.shortRuntimeNotes(mode));
    if (!diff.decisionsAgree() && diff.bothOk()) {
      notes.add(
          "Decisions differ — Zen lounge JDM is a richer tier×cabin matrix; Kogito DMN is a simpler eligibility table. See GET /v1/compare/notes.");
    }
    return new CompareResponse(
        mode, request, zen, kogito, diff, (System.nanoTime() - startNanos) / 1_000_000L, notes);
  }

  private DiffSummary diff(EngineRunResult zen, EngineRunResult kogito, String mode) {
    boolean bothOk = zen.ok() && kogito.ok();
    boolean agree =
        bothOk && Objects.equals(normalizeDecision(zen.decision()), normalizeDecision(kogito.decision()));
    Long zenMs = zen.ok() ? zen.wallMillis() : null;
    Long kogitoMs = kogito.ok() ? kogito.wallMillis() : null;
    Long delta = zenMs != null && kogitoMs != null ? Math.abs(zenMs - kogitoMs) : null;
    String faster = null;
    if (zenMs != null && kogitoMs != null) {
      if (zenMs < kogitoMs) {
        faster = "zen";
      } else if (kogitoMs < zenMs) {
        faster = "kogito";
      } else {
        faster = "tie";
      }
    }
    Map<String, Object> caveats = new LinkedHashMap<>();
    caveats.put(
        "rule_parity",
        "Zen evaluates published JDM packs; Kogito evaluates seeded LoungeAccess.dmn — models are not equivalent.");
    caveats.put(
        "timing",
        MODE_PLATFORM.equals(mode)
            ? "Both timings include FastAPI platform overhead (store, entitlements, mapping)."
            : "Zen timing includes FastAPI; Kogito timing is direct Quarkus HTTP only.");
    if (zen.engineReportedMicros() != null) {
      caveats.put("zen_engine_reported_micros", zen.engineReportedMicros());
    }
    return new DiffSummary(
        bothOk,
        agree,
        zen.decision(),
        kogito.decision(),
        zenMs,
        kogitoMs,
        delta,
        faster,
        caveats);
  }

  private static String normalizeDecision(String decision) {
    return decision == null ? null : decision.trim().toLowerCase();
  }
}
