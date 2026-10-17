package com.axiom.compare.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.axiom.compare.client.KogitoRulesClient;
import com.axiom.compare.client.PlatformRulesClient;
import com.axiom.compare.model.CompareResponse;
import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class EngineCompareServiceTest {

  @Mock PlatformRulesClient platformRulesClient;
  @Mock KogitoRulesClient kogitoRulesClient;
  @Mock ComparisonNotesService notesService;

  EngineCompareService service;

  @BeforeEach
  void setUp() {
    when(notesService.shortRuntimeNotes(any())).thenReturn(List.of("note"));
    service = new EngineCompareService(platformRulesClient, kogitoRulesClient, notesService);
  }

  @Test
  void compareViaPlatformCallsZenThenKogito() {
    EvaluateRequest request = new EvaluateRequest();
    when(platformRulesClient.evaluate(any(), eq("zen")))
        .thenReturn(
            EngineRunResult.success("zen", "platform", "allow", 12L, 800L, Map.of("decision", "allow")));
    when(platformRulesClient.evaluate(any(), eq("kogito")))
        .thenReturn(
            EngineRunResult.success(
                "kogito", "platform", "allow", 18L, null, Map.of("decision", "allow")));

    CompareResponse response = service.compareViaPlatform(request);

    InOrder order = Mockito.inOrder(platformRulesClient);
    order.verify(platformRulesClient).evaluate(request, "zen");
    order.verify(platformRulesClient).evaluate(request, "kogito");
    verifyNoInteractions(kogitoRulesClient);

    assertThat(response.mode()).isEqualTo("platform");
    assertThat(response.diff().bothOk()).isTrue();
    assertThat(response.diff().decisionsAgree()).isTrue();
    assertThat(response.diff().fasterEngine()).isEqualTo("zen");
    assertThat(response.zen().wallMillis()).isEqualTo(12L);
    assertThat(response.kogito().wallMillis()).isEqualTo(18L);
  }

  @Test
  void compareWithDirectKogitoUsesHttpKogito() {
    EvaluateRequest request = new EvaluateRequest();
    when(platformRulesClient.evaluate(any(), eq("zen")))
        .thenReturn(EngineRunResult.success("zen", "platform", "deny", 10L, null, Map.of()));
    when(kogitoRulesClient.evaluateDirect(any()))
        .thenReturn(EngineRunResult.success("kogito", "direct", "allow", 5L, null, Map.of()));

    CompareResponse response = service.compareWithDirectKogito(request);

    verify(platformRulesClient).evaluate(request, "zen");
    verify(kogitoRulesClient).evaluateDirect(request);
    assertThat(response.mode()).isEqualTo("direct-kogito");
    assertThat(response.diff().decisionsAgree()).isFalse();
    assertThat(response.diff().fasterEngine()).isEqualTo("kogito");
  }
}
