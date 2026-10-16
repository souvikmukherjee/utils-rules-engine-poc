package com.axiom.compare.web;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.axiom.compare.config.CompareProperties;
import com.axiom.compare.model.CompareResponse;
import com.axiom.compare.model.CompareResponse.DiffSummary;
import com.axiom.compare.model.ComparisonNotes;
import com.axiom.compare.model.EngineRunResult;
import com.axiom.compare.model.EvaluateRequest;
import com.axiom.compare.model.HealthResponse;
import com.axiom.compare.model.HealthResponse.BackendStatus;
import com.axiom.compare.service.BenchmarkService;
import com.axiom.compare.service.ComparisonNotesService;
import com.axiom.compare.service.EngineCompareService;
import com.axiom.compare.service.HotReloadProbeService;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(controllers = {CompareController.class, RootController.class})
class CompareControllerTest {

  @Autowired MockMvc mockMvc;

  @MockBean EngineCompareService compareService;
  @MockBean BenchmarkService benchmarkService;
  @MockBean HotReloadProbeService hotReloadProbeService;
  @MockBean ComparisonNotesService notesService;
  @MockBean CompareProperties properties;

  @Test
  void healthEndpoint() throws Exception {
    when(properties.getPlatformUrl()).thenReturn("http://127.0.0.1:8000");
    when(properties.getKogitoUrl()).thenReturn("http://127.0.0.1:8081");
    when(compareService.health(anyString(), anyString()))
        .thenReturn(
            new HealthResponse(
                true,
                new BackendStatus("http://127.0.0.1:8000", true, 200, "ok"),
                new BackendStatus("http://127.0.0.1:8081", true, 200, "ok"),
                "ready"));

    mockMvc
        .perform(get("/v1/compare/health"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.ready").value(true));
  }

  @Test
  void compareEndpointDefaultsEmptyBody() throws Exception {
    EvaluateRequest req = new EvaluateRequest();
    EngineRunResult zen =
        EngineRunResult.success("zen", "p", "allow", 11L, null, Map.of("decision", "allow"));
    EngineRunResult kogito =
        EngineRunResult.success("kogito", "p", "allow", 22L, null, Map.of("decision", "allow"));
    when(compareService.compareViaPlatform(any()))
        .thenReturn(
            new CompareResponse(
                "platform",
                req,
                zen,
                kogito,
                new DiffSummary(true, true, "allow", "allow", 11L, 22L, 11L, "zen", Map.of()),
                40L,
                List.of()));

    mockMvc
        .perform(post("/v1/compare").contentType(MediaType.APPLICATION_JSON).content("{}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.mode").value("platform"))
        .andExpect(jsonPath("$.diff.fasterEngine").value("zen"));
  }

  @Test
  void notesEndpoint() throws Exception {
    when(notesService.notes())
        .thenReturn(
            new ComparisonNotes(
                "summary",
                Map.of(),
                List.of("step"),
                List.of("caveat")));

    mockMvc
        .perform(get("/v1/compare/notes"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.summary").value("summary"));
  }
}
