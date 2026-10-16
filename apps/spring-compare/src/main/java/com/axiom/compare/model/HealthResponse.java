package com.axiom.compare.model;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record HealthResponse(
    boolean ready, BackendStatus platform, BackendStatus kogito, String hint) {

  public record BackendStatus(String url, boolean up, Integer status, String detail) {}
}
