package com.esca.hse.controller;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

    private final JdbcTemplate jdbcTemplate;

    public HealthController(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @GetMapping
    public Map<String, Object> health() {
        Integer databaseCheck = jdbcTemplate.queryForObject("SELECT 1", Integer.class);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "ready");
        response.put("service", "esca-hse-api");
        response.put("database", databaseCheck != null && databaseCheck == 1 ? "connected" : "unavailable");
        response.put("timestamp", Instant.now().toString());
        return response;
    }
}
