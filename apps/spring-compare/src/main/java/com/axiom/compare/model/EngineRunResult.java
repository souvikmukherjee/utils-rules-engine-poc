package com.axiom.compare.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record EngineRunResult(
    String engine,
    String path,
    boolean ok,
    String decision,
    long wallMillis,
    Long engineReportedMicros,
    Map<String, Object> response,
    String error) {

  public static EngineRunResult success(
      String engine,
      String path,
      String decision,
      long wallMillis,
      Long engineReportedMicros,
      Map<String, Object> response) {
    return new EngineRunResult(
        engine, path, true, decision, wallMillis, engineReportedMicros, response, null);
  }

  public static EngineRunResult failure(
      String engine, String path, long wallMillis, String error) {
    return new EngineRunResult(engine, path, false, null, wallMillis, null, null, error);
  }
}
