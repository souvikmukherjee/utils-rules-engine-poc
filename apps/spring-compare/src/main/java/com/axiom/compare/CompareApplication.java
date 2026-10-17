package com.axiom.compare;

import com.axiom.compare.config.CompareProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(CompareProperties.class)
public class CompareApplication {

  public static void main(String[] args) {
    SpringApplication.run(CompareApplication.class, args);
  }
}
