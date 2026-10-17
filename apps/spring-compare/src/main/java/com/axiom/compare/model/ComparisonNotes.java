package com.axiom.compare.model;

import java.util.List;
import java.util.Map;

public record ComparisonNotes(
    String summary,
    Map<String, Dimension> dimensions,
    List<String> howToMeasure,
    List<String> caveats) {

  public record Dimension(String zen, String kogito, String takeaway) {}
}
