package com.axiom.compare.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record BenchmarkResponse(
    String mode,
    int iterations,
    int warmup,
    LatencyStats zen,
    LatencyStats kogito,
    String fasterEngine,
    List<String> notes) {

  public record LatencyStats(
      int samples,
      long minMillis,
      long maxMillis,
      double meanMillis,
      double p50Millis,
      double p95Millis,
      int errors) {}
}
