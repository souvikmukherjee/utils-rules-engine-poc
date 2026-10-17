package com.axiom.compare.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record CompareResponse(
    String mode,
    EvaluateRequest request,
    EngineRunResult zen,
    EngineRunResult kogito,
    DiffSummary diff,
    long totalWallMillis,
    List<String> notes) {

  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record DiffSummary(
      boolean bothOk,
      boolean decisionsAgree,
      String zenDecision,
      String kogitoDecision,
      Long zenWallMillis,
      Long kogitoWallMillis,
      Long wallDeltaMillis,
      String fasterEngine,
      Map<String, Object> caveats) {}
}
