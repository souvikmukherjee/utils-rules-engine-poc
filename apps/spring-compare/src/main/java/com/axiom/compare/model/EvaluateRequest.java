package com.axiom.compare.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.validation.constraints.NotBlank;
import java.util.LinkedHashMap;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class EvaluateRequest {

  private String domain = "lounge";

  @NotBlank private String subjectId = "FF-COMPARE-1";

  private Map<String, Object> facts = defaultGoldFacts();

  private String environment = "production";

  private String asOf;

  private boolean commitEntitlements = false;

  private String packId = "lounge-access";

  private String tenantId = "default";

  /** Set by the compare service when dispatching to the platform. */
  private String engine;

  public static Map<String, Object> defaultGoldFacts() {
    Map<String, Object> membership = new LinkedHashMap<>();
    membership.put("tier", "gold");
    membership.put("companion_eligible", false);
    Map<String, Object> booking = new LinkedHashMap<>();
    booking.put("cabin", "economy");
    Map<String, Object> partner = new LinkedHashMap<>();
    partner.put("elite_tier", null);
    Map<String, Object> facts = new LinkedHashMap<>();
    facts.put("membership", membership);
    facts.put("booking", booking);
    facts.put("partner", partner);
    return facts;
  }

  public String getDomain() {
    return domain;
  }

  public void setDomain(String domain) {
    this.domain = domain;
  }

  public String getSubjectId() {
    return subjectId;
  }

  public void setSubjectId(String subjectId) {
    this.subjectId = subjectId;
  }

  public Map<String, Object> getFacts() {
    return facts;
  }

  public void setFacts(Map<String, Object> facts) {
    this.facts = facts;
  }

  public String getEnvironment() {
    return environment;
  }

  public void setEnvironment(String environment) {
    this.environment = environment;
  }

  public String getAsOf() {
    return asOf;
  }

  public void setAsOf(String asOf) {
    this.asOf = asOf;
  }

  public boolean isCommitEntitlements() {
    return commitEntitlements;
  }

  public void setCommitEntitlements(boolean commitEntitlements) {
    this.commitEntitlements = commitEntitlements;
  }

  public String getPackId() {
    return packId;
  }

  public void setPackId(String packId) {
    this.packId = packId;
  }

  public String getTenantId() {
    return tenantId;
  }

  public void setTenantId(String tenantId) {
    this.tenantId = tenantId;
  }

  public String getEngine() {
    return engine;
  }

  public void setEngine(String engine) {
    this.engine = engine;
  }

  /** Platform JSON uses snake_case field names. */
  public Map<String, Object> toPlatformBody(String engineName) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("domain", domain);
    body.put("subject_id", subjectId);
    body.put("facts", facts != null ? facts : Map.of());
    body.put("environment", environment);
    body.put("as_of", asOf);
    body.put("commit_entitlements", false);
    body.put("pack_id", packId);
    body.put("tenant_id", tenantId);
    body.put("engine", engineName);
    return body;
  }
}
