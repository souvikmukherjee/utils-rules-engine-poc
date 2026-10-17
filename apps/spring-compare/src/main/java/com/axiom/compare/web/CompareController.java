package com.axiom.compare.web;

import com.axiom.compare.config.CompareProperties;
import com.axiom.compare.model.BenchmarkResponse;
import com.axiom.compare.model.CompareResponse;
import com.axiom.compare.model.ComparisonNotes;
import com.axiom.compare.model.EvaluateRequest;
import com.axiom.compare.model.HealthResponse;
import com.axiom.compare.service.BenchmarkService;
import com.axiom.compare.service.ComparisonNotesService;
import com.axiom.compare.service.EngineCompareService;
import com.axiom.compare.service.HotReloadProbeService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(path = "/v1/compare", produces = MediaType.APPLICATION_JSON_VALUE)
public class CompareController {

  private final EngineCompareService compareService;
  private final BenchmarkService benchmarkService;
  private final HotReloadProbeService hotReloadProbeService;
  private final ComparisonNotesService notesService;
  private final CompareProperties properties;

  public CompareController(
      EngineCompareService compareService,
      BenchmarkService benchmarkService,
      HotReloadProbeService hotReloadProbeService,
      ComparisonNotesService notesService,
      CompareProperties properties) {
    this.compareService = compareService;
    this.benchmarkService = benchmarkService;
    this.hotReloadProbeService = hotReloadProbeService;
    this.notesService = notesService;
    this.properties = properties;
  }

  @GetMapping("/health")
  public HealthResponse health() {
    return compareService.health(properties.getPlatformUrl(), properties.getKogitoUrl());
  }

  @GetMapping("/notes")
  public ComparisonNotes notes() {
    return notesService.notes();
  }

  /**
   * Run Zen then Kogito sequentially and return side-by-side decisions + wall timings.
   *
   * @param mode {@code platform} (default) or {@code direct-kogito}
   */
  @PostMapping
  public CompareResponse compare(
      @Valid @RequestBody(required = false) EvaluateRequest request,
      @RequestParam(defaultValue = EngineCompareService.MODE_PLATFORM) String mode) {
    EvaluateRequest effective = request != null ? request : new EvaluateRequest();
    if (EngineCompareService.MODE_DIRECT_KOGITO.equalsIgnoreCase(mode)) {
      return compareService.compareWithDirectKogito(effective);
    }
    return compareService.compareViaPlatform(effective);
  }

  @PostMapping("/benchmark")
  public BenchmarkResponse benchmark(
      @Valid @RequestBody(required = false) EvaluateRequest request,
      @RequestParam(defaultValue = EngineCompareService.MODE_PLATFORM) String mode,
      @RequestParam(required = false) Integer iterations) {
    EvaluateRequest effective = request != null ? request : new EvaluateRequest();
    String resolved =
        EngineCompareService.MODE_DIRECT_KOGITO.equalsIgnoreCase(mode)
            ? EngineCompareService.MODE_DIRECT_KOGITO
            : EngineCompareService.MODE_PLATFORM;
    return benchmarkService.benchmark(effective, resolved, iterations);
  }

  @PostMapping("/hot-reload/probe")
  public Map<String, Object> hotReloadProbe(
      @Valid @RequestBody(required = false) EvaluateRequest request,
      @RequestParam(defaultValue = EngineCompareService.MODE_PLATFORM) String mode) {
    EvaluateRequest effective = request != null ? request : new EvaluateRequest();
    String resolved =
        EngineCompareService.MODE_DIRECT_KOGITO.equalsIgnoreCase(mode)
            ? EngineCompareService.MODE_DIRECT_KOGITO
            : EngineCompareService.MODE_PLATFORM;
    return hotReloadProbeService.probe(effective, resolved);
  }
}
