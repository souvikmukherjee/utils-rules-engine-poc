package com.axiom.compare.web;

import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RootController {

  @GetMapping("/")
  public Map<String, Object> index() {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("service", "axiom-spring-compare");
    body.put(
        "description",
        "Spring Boot harness: call GoRules Zen then Kogito and compare latency / decisions.");
    body.put(
        "endpoints",
        Map.of(
            "health", "GET /v1/compare/health",
            "notes", "GET /v1/compare/notes",
            "compare", "POST /v1/compare",
            "benchmark", "POST /v1/compare/benchmark?iterations=20",
            "hotReloadProbe", "POST /v1/compare/hot-reload/probe"));
    return body;
  }
}
