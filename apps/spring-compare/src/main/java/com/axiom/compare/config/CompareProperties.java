package com.axiom.compare.config;

import java.time.Duration;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "axiom.compare")
public class CompareProperties {

  private String platformUrl = "http://127.0.0.1:8000";
  private String kogitoUrl = "http://127.0.0.1:8081";
  private Duration connectTimeout = Duration.ofSeconds(2);
  private Duration readTimeout = Duration.ofSeconds(15);
  private int defaultBenchmarkIterations = 20;
  private int maxBenchmarkIterations = 200;

  public String getPlatformUrl() {
    return platformUrl;
  }

  public void setPlatformUrl(String platformUrl) {
    this.platformUrl = platformUrl;
  }

  public String getKogitoUrl() {
    return kogitoUrl;
  }

  public void setKogitoUrl(String kogitoUrl) {
    this.kogitoUrl = kogitoUrl;
  }

  public Duration getConnectTimeout() {
    return connectTimeout;
  }

  public void setConnectTimeout(Duration connectTimeout) {
    this.connectTimeout = connectTimeout;
  }

  public Duration getReadTimeout() {
    return readTimeout;
  }

  public void setReadTimeout(Duration readTimeout) {
    this.readTimeout = readTimeout;
  }

  public int getDefaultBenchmarkIterations() {
    return defaultBenchmarkIterations;
  }

  public void setDefaultBenchmarkIterations(int defaultBenchmarkIterations) {
    this.defaultBenchmarkIterations = defaultBenchmarkIterations;
  }

  public int getMaxBenchmarkIterations() {
    return maxBenchmarkIterations;
  }

  public void setMaxBenchmarkIterations(int maxBenchmarkIterations) {
    this.maxBenchmarkIterations = maxBenchmarkIterations;
  }
}
