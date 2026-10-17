package com.axiom.compare.service;

import com.axiom.compare.client.KogitoRulesClient;
import com.axiom.compare.client.PlatformRulesClient;
import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;

/**
 * Lightweight helper for hot-reload experiments: run Zen then Kogito once and stamp the wall times
 * so you can compare before/after editing a JDM pack or {@code LoungeAccess.dmn}.
 */
@Service
public class HotReloadProbeService {

  private final PlatformRulesClient platformRulesClient;
  private final KogitoRulesClient kogitoRulesClient;

  public HotReloadProbeService(
      PlatformRulesClient platformRulesClient, KogitoRulesClient kogitoRulesClient) {
    this.platformRulesClient = platformRulesClient;
    this.kogitoRulesClient = kogitoRulesClient;
  }

  public Map<String, Object> probe(EvaluateRequest request, String mode) {
    long start = System.nanoTime();
    EngineRunResult zen = platformRulesClient.evaluate(request, "zen");
    EngineRunResult kogito =
        EngineCompareService.MODE_DIRECT_KOGITO.equals(mode)
            ? kogitoRulesClient.evaluateDirect(request)
            : platformRulesClient.evaluate(request, "kogito");

    Map<String, Object> body = new LinkedHashMap<>();
    body.put("probed_at", Instant.now().toString());
    body.put("mode", mode);
    body.put("total_wall_millis", (System.nanoTime() - start) / 1_000_000L);
    body.put("zen", slim(zen));
    body.put("kogito", slim(kogito));
    body.put(
        "instructions",
        List.of(
            "1. Capture a baseline probe.",
            "2. Hot-reload Zen: publish/update the lounge pack via Author UI or pack API (no API restart).",
            "3. Hot-reload Kogito: edit apps/kogito/.../LoungeAccess.dmn while `make kogito` (quarkus:dev) is running.",
            "4. Probe again; compare wall_millis and decisions.",
            "5. For adapter-code reload: touch Python under packages/rules_engine (uvicorn --reload) vs change Java under apps/kogito (Quarkus live reload)."));
    return body;
  }

  private static Map<String, Object> slim(EngineRunResult run) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("ok", run.ok());
    m.put("decision", run.decision());
    m.put("wall_millis", run.wallMillis());
    m.put("path", run.path());
    m.put("engine_reported_micros", run.engineReportedMicros());
    m.put("error", run.error());
    return m;
  }
}
