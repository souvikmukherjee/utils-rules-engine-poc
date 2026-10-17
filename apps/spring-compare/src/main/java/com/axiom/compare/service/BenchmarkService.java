package com.axiom.compare.service;

import com.axiom.compare.client.KogitoRulesClient;
import com.axiom.compare.client.PlatformRulesClient;
import com.axiom.compare.config.CompareProperties;
import com.axiom.compare.model.BenchmarkResponse;
import com.axiom.compare.model.BenchmarkResponse.LatencyStats;
import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.function.Supplier;
import org.springframework.stereotype.Service;

@Service
public class BenchmarkService {

  private final PlatformRulesClient platformRulesClient;
  private final KogitoRulesClient kogitoRulesClient;
  private final CompareProperties properties;
  private final ComparisonNotesService notesService;

  public BenchmarkService(
      PlatformRulesClient platformRulesClient,
      KogitoRulesClient kogitoRulesClient,
      CompareProperties properties,
      ComparisonNotesService notesService) {
    this.platformRulesClient = platformRulesClient;
    this.kogitoRulesClient = kogitoRulesClient;
    this.properties = properties;
    this.notesService = notesService;
  }

  public BenchmarkResponse benchmark(EvaluateRequest request, String mode, Integer iterations) {
    int n = resolveIterations(iterations);
    int warmup = Math.min(3, Math.max(1, n / 10));

    Supplier<EngineRunResult> zenCall = () -> platformRulesClient.evaluate(request, "zen");
    Supplier<EngineRunResult> kogitoCall =
        EngineCompareService.MODE_DIRECT_KOGITO.equals(mode)
            ? () -> kogitoRulesClient.evaluateDirect(request)
            : () -> platformRulesClient.evaluate(request, "kogito");

    // Warmup (discarded) — sequential Zen then Kogito each round.
    for (int i = 0; i < warmup; i++) {
      zenCall.get();
      kogitoCall.get();
    }

    List<Long> zenSamples = new ArrayList<>(n);
    List<Long> kogitoSamples = new ArrayList<>(n);
    int zenErrors = 0;
    int kogitoErrors = 0;

    for (int i = 0; i < n; i++) {
      EngineRunResult zen = zenCall.get();
      EngineRunResult kogito = kogitoCall.get();
      if (zen.ok()) {
        zenSamples.add(zen.wallMillis());
      } else {
        zenErrors++;
      }
      if (kogito.ok()) {
        kogitoSamples.add(kogito.wallMillis());
      } else {
        kogitoErrors++;
      }
    }

    LatencyStats zenStats = stats(zenSamples, zenErrors);
    LatencyStats kogitoStats = stats(kogitoSamples, kogitoErrors);
    String faster = fasterEngine(zenStats, kogitoStats);

    List<String> notes = new ArrayList<>();
    notes.add(
        "Each iteration calls Zen then Kogito sequentially. Wall times are HTTP round-trips as seen by Spring.");
    notes.add("Warmup iterations discarded: " + warmup);
    notes.addAll(notesService.shortRuntimeNotes(mode));

    return new BenchmarkResponse(mode, n, warmup, zenStats, kogitoStats, faster, notes);
  }

  private int resolveIterations(Integer iterations) {
    int n =
        iterations == null || iterations <= 0
            ? properties.getDefaultBenchmarkIterations()
            : iterations;
    return Math.min(n, properties.getMaxBenchmarkIterations());
  }

  private static LatencyStats stats(List<Long> samples, int errors) {
    if (samples.isEmpty()) {
      return new LatencyStats(0, 0, 0, 0, 0, 0, errors);
    }
    long[] arr = samples.stream().mapToLong(Long::longValue).sorted().toArray();
    long min = arr[0];
    long max = arr[arr.length - 1];
    double mean = Arrays.stream(arr).average().orElse(0);
    double p50 = percentile(arr, 0.50);
    double p95 = percentile(arr, 0.95);
    return new LatencyStats(arr.length, min, max, round1(mean), round1(p50), round1(p95), errors);
  }

  private static double percentile(long[] sorted, double p) {
    if (sorted.length == 1) {
      return sorted[0];
    }
    double idx = p * (sorted.length - 1);
    int lo = (int) Math.floor(idx);
    int hi = (int) Math.ceil(idx);
    if (lo == hi) {
      return sorted[lo];
    }
    double w = idx - lo;
    return sorted[lo] * (1 - w) + sorted[hi] * w;
  }

  private static double round1(double v) {
    return Math.round(v * 10.0) / 10.0;
  }

  private static String fasterEngine(LatencyStats zen, LatencyStats kogito) {
    if (zen.samples() == 0 || kogito.samples() == 0) {
      return null;
    }
    if (zen.p50Millis() < kogito.p50Millis()) {
      return "zen";
    }
    if (kogito.p50Millis() < zen.p50Millis()) {
      return "kogito";
    }
    return "tie";
  }
}
