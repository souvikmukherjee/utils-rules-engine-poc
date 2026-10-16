package com.axiom.compare.config;

import java.time.Duration;
import org.springframework.boot.web.client.ClientHttpRequestFactories;
import org.springframework.boot.web.client.ClientHttpRequestFactorySettings;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.ClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class RestClientConfig {

  @Bean
  RestClient.Builder restClientBuilder(CompareProperties properties) {
    ClientHttpRequestFactory factory =
        ClientHttpRequestFactories.get(
            ClientHttpRequestFactorySettings.DEFAULTS
                .withConnectTimeout(properties.getConnectTimeout())
                .withReadTimeout(properties.getReadTimeout()));
    return RestClient.builder().requestFactory(factory);
  }

  @Bean
  RestClient platformRestClient(RestClient.Builder builder, CompareProperties properties) {
    return builder.baseUrl(trimSlash(properties.getPlatformUrl())).build();
  }

  @Bean
  RestClient kogitoRestClient(RestClient.Builder builder, CompareProperties properties) {
    return builder.baseUrl(trimSlash(properties.getKogitoUrl())).build();
  }

  private static String trimSlash(String url) {
    if (url == null || url.isBlank()) {
      return url;
    }
    return url.endsWith("/") ? url.substring(0, url.length() - 1) : url;
  }
}
