package com.axiom.compare.client;

import static org.assertj.core.api.Assertions.assertThat;

import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import java.io.IOException;
import java.util.Map;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;

class KogitoRulesClientTest {

  private MockWebServer server;
  private KogitoRulesClient client;

  @BeforeEach
  void setUp() throws IOException {
    server = new MockWebServer();
    server.start();
    RestClient restClient = RestClient.builder().baseUrl(server.url("/").toString()).build();
    client = new KogitoRulesClient(restClient);
  }

  @AfterEach
  void tearDown() throws IOException {
    server.shutdown();
  }

  @Test
  void mapsFactsAndParsesEligibility() throws Exception {
    server.enqueue(
        new MockResponse()
            .setHeader("Content-Type", "application/json")
            .setBody(
                """
                {"Eligibility":"allow","LoungeClass":"business","CompanionsAllowed":0,"MatchedRule":"gold-tier"}
                """));

    EvaluateRequest request = new EvaluateRequest();
    request.setFacts(EvaluateRequest.defaultGoldFacts());
    request.setAsOf("2026-06-15T12:00:00Z");

    EngineRunResult result = client.evaluateDirect(request);

    assertThat(result.ok()).isTrue();
    assertThat(result.decision()).isEqualTo("allow");
    assertThat(result.path()).isEqualTo("kogito:/LoungeAccess");

    RecordedRequest recorded = server.takeRequest();
    assertThat(recorded.getPath()).isEqualTo("/LoungeAccess");
    assertThat(recorded.getBody().readUtf8())
        .contains("\"MembershipTier\":\"gold\"")
        .contains("\"AsOf\":\"2026-06-15\"");
  }

  @Test
  void toKogitoContextDefaultsCompanionFalse() {
    Map<String, Object> context =
        KogitoRulesClient.toKogitoContext(Map.of("membership", Map.of("tier", "silver")), null);
    assertThat(context.get("MembershipTier")).isEqualTo("silver");
    assertThat(context.get("CompanionEligible")).isEqualTo(false);
    assertThat(context.get("AsOf")).isNotNull();
  }
}
