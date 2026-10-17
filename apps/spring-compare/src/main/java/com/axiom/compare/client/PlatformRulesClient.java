package com.axiom.compare.client;

import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import java.util.Map;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

@Component
public class PlatformRulesClient {

  private static final ParameterizedTypeReference<Map<String, Object>> MAP =
      new ParameterizedTypeReference<>() {};

  private final RestClient platformRestClient;

  public PlatformRulesClient(@Qualifier("platformRestClient") RestClient platformRestClient) {
    this.platformRestClient = platformRestClient;
  }

  public EngineRunResult evaluate(EvaluateRequest request, String engine) {
    long start = System.nanoTime();
    String path = "platform:/v1/evaluate?engine=" + engine;
    try {
      Map<String, Object> body =
          platformRestClient
              .post()
              .uri("/v1/evaluate")
              .contentType(MediaType.APPLICATION_JSON)
              .body(request.toPlatformBody(engine))
              .retrieve()
              .body(MAP);
      long wallMillis = elapsedMillis(start);
      String decision = body == null ? null : stringOrNull(body.get("decision"));
      Long reported = extractZenPerformanceMicros(body);
      return EngineRunResult.success(engine, path, decision, wallMillis, reported, body);
    } catch (RestClientResponseException ex) {
      return EngineRunResult.failure(
          engine,
          path,
          elapsedMillis(start),
          "HTTP " + ex.getStatusCode().value() + ": " + truncate(ex.getResponseBodyAsString()));
    } catch (Exception ex) {
      return EngineRunResult.failure(engine, path, elapsedMillis(start), ex.getMessage());
    }
  }

  public boolean healthUp() {
    try {
      platformRestClient.get().uri("/docs").retrieve().toBodilessEntity();
      return true;
    } catch (Exception ex) {
      try {
        platformRestClient.get().uri("/v1/catalog").retrieve().toBodilessEntity();
        return true;
      } catch (Exception ignored) {
        return false;
      }
    }
  }

  public Integer probeStatus() {
    try {
      return platformRestClient
          .get()
          .uri("/v1/catalog")
          .retrieve()
          .toBodilessEntity()
          .getStatusCode()
          .value();
    } catch (RestClientResponseException ex) {
      return ex.getStatusCode().value();
    } catch (Exception ex) {
      return null;
    }
  }

  @SuppressWarnings("unchecked")
  private Long extractZenPerformanceMicros(Map<String, Object> body) {
    if (body == null) {
      return null;
    }
    Object traceObj = body.get("trace");
    if (!(traceObj instanceof Map<?, ?> trace)) {
      return null;
    }
    Object perf = trace.get("zen_performance");
    if (perf == null) {
      return null;
    }
    if (perf instanceof Number number) {
      return number.longValue();
    }
    String text = String.valueOf(perf).trim();
    // Zen may report "123µs", "1.2ms", or a raw number string.
    try {
      if (text.endsWith("µs") || text.endsWith("us")) {
        String num = text.replace("µs", "").replace("us", "").trim();
        return Math.round(Double.parseDouble(num));
      }
      if (text.endsWith("ms")) {
        String num = text.substring(0, text.length() - 2).trim();
        return Math.round(Double.parseDouble(num) * 1000.0);
      }
      if (text.endsWith("s") && !text.endsWith("ms")) {
        String num = text.substring(0, text.length() - 1).trim();
        return Math.round(Double.parseDouble(num) * 1_000_000.0);
      }
      return Math.round(Double.parseDouble(text));
    } catch (NumberFormatException ignored) {
      return null;
    }
  }

  private static String stringOrNull(Object value) {
    return value == null ? null : String.valueOf(value);
  }

  private static long elapsedMillis(long startNanos) {
    return (System.nanoTime() - startNanos) / 1_000_000L;
  }

  private static String truncate(String text) {
    if (text == null) {
      return "";
    }
    return text.length() <= 400 ? text : text.substring(0, 400) + "…";
  }
}
