package com.axiom.compare.client;

import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

/**
 * Direct HTTP client for {@code apps/kogito} Quarkus DMN REST ({@code POST /LoungeAccess}).
 *
 * <p>Mirrors the fact mapping in {@code rules_api.kogito_client.facts_to_kogito_context}.
 */
@Component
public class KogitoRulesClient {

  private static final ParameterizedTypeReference<Map<String, Object>> MAP =
      new ParameterizedTypeReference<>() {};

  private final RestClient kogitoRestClient;

  public KogitoRulesClient(@Qualifier("kogitoRestClient") RestClient kogitoRestClient) {
    this.kogitoRestClient = kogitoRestClient;
  }

  public EngineRunResult evaluateDirect(EvaluateRequest request) {
    long start = System.nanoTime();
    String path = "kogito:/LoungeAccess";
    Map<String, Object> context = toKogitoContext(request.getFacts(), request.getAsOf());
    try {
      Map<String, Object> body =
          kogitoRestClient
              .post()
              .uri("/LoungeAccess")
              .contentType(MediaType.APPLICATION_JSON)
              .body(context)
              .retrieve()
              .body(MAP);
      long wallMillis = elapsedMillis(start);
      String decision = mapEligibility(body);
      return EngineRunResult.success("kogito", path, decision, wallMillis, null, body);
    } catch (RestClientResponseException ex) {
      return EngineRunResult.failure(
          "kogito",
          path,
          elapsedMillis(start),
          "HTTP " + ex.getStatusCode().value() + ": " + truncate(ex.getResponseBodyAsString()));
    } catch (Exception ex) {
      return EngineRunResult.failure("kogito", path, elapsedMillis(start), ex.getMessage());
    }
  }

  public boolean healthUp() {
    try {
      kogitoRestClient.get().uri("/q/health/ready").retrieve().toBodilessEntity();
      return true;
    } catch (Exception ex) {
      try {
        kogitoRestClient.get().uri("/q/health").retrieve().toBodilessEntity();
        return true;
      } catch (Exception ignored) {
        return false;
      }
    }
  }

  public Integer probeStatus() {
    try {
      return kogitoRestClient
          .get()
          .uri("/q/health/ready")
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
  public static Map<String, Object> toKogitoContext(Map<String, Object> facts, String asOf) {
    Map<String, Object> safe = facts != null ? facts : Map.of();
    Object membershipObj = safe.get("membership");
    Map<String, Object> membership =
        membershipObj instanceof Map<?, ?> m ? (Map<String, Object>) m : Map.of();
    Object partnerObj = safe.get("partner");
    Map<String, Object> partner =
        partnerObj instanceof Map<?, ?> m ? (Map<String, Object>) m : Map.of();

    Map<String, Object> context = new LinkedHashMap<>();
    context.put("MembershipTier", membership.get("tier"));
    context.put("PartnerEliteTier", partner.get("elite_tier"));
    Object companion = membership.get("companion_eligible");
    context.put("CompanionEligible", companion instanceof Boolean b ? b : Boolean.FALSE);
    context.put("AsOf", asOfDate(asOf));
    return context;
  }

  private static String asOfDate(String asOf) {
    if (asOf == null || asOf.isBlank()) {
      return LocalDate.now().toString();
    }
    return asOf.length() >= 10 ? asOf.substring(0, 10) : asOf;
  }

  private static String mapEligibility(Map<String, Object> body) {
    if (body == null) {
      return null;
    }
    Object eligibility = body.get("Eligibility");
    if (eligibility == null) {
      return "inconclusive";
    }
    return String.valueOf(eligibility);
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
