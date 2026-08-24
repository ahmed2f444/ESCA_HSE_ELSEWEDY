package com.esca.hse;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:esca-security;MODE=MySQL;DB_CLOSE_DELAY=-1;DATABASE_TO_LOWER=TRUE",
        "app.security.enabled=true",
        "app.security.demo-users-enabled=false",
        "app.demo-data.enabled=false"
})
@AutoConfigureMockMvc
class SecurityApiIntegrationTests {
    @Autowired MockMvc mvc;
    @Autowired JdbcTemplate jdbc;
    @Autowired PasswordEncoder encoder;
    @Autowired ObjectMapper objectMapper;

    @BeforeEach
    void prepareSecurityFixtures() {
        jdbc.update("DELETE FROM automation_actions");
        jdbc.update("DELETE FROM notifications");
        jdbc.update("DELETE FROM audit_log");
        jdbc.update("DELETE FROM permits");
        jdbc.update("DELETE FROM user_roles");
        jdbc.update("DELETE FROM users");
        jdbc.update("DELETE FROM roles");
        jdbc.update("INSERT INTO roles (role_id, role_name, description, scope_level) VALUES (1, 'HSE Manager', 'HSE oversight', 'SITE')");
        jdbc.update("INSERT INTO users (user_id, employee_id, username, password_hash, status_id) VALUES (1, 1, 'hse.manager', ?, 1)",
                encoder.encode("HseDemo@2026"));
        jdbc.update("INSERT INTO user_roles (user_id, role_id, status_id) VALUES (1, 1, 1)");
    }


    @Test
    void protectedEndpointsRequireAuthenticationAndAcceptUserJwt() throws Exception {
        mvc.perform(get("/api/v1/dashboard"))
                .andExpect(status().isUnauthorized());

        String loginResponse = mvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"hse.manager\",\"password\":\"HseDemo@2026\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token_type").value("Bearer"))
                .andExpect(jsonPath("$.user.role").value("HSE_MANAGER"))
                .andReturn().getResponse().getContentAsString();

        JsonNode login = objectMapper.readTree(loginResponse);
        String token = login.get("access_token").asText();
        mvc.perform(get("/api/v1/dashboard").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("ready"));
    }

    @Test
    void serviceTokenSecuresAutomationActionAndIdempotency() throws Exception {
        jdbc.update("INSERT INTO permits (permit_id,permit_type,work_description,start_at,expiry_at,risk_level,status) "
                        + "VALUES ('PTW-SEC-1','HOT_WORK','Security integration test',CURRENT_TIMESTAMP,DATEADD('HOUR',-2,CURRENT_TIMESTAMP),'HIGH','ACTIVE')");

        String tokenResponse = mvc.perform(post("/api/v1/internal/auth/service-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"client_id\":\"esca-hse-automation\",\"client_secret\":\"test-automation-secret\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.scope").value("automation:write"))
                .andReturn().getResponse().getContentAsString();
        String serviceToken = objectMapper.readTree(tokenResponse).get("access_token").asText();

        String eventId = "evt_0123456789abcdef0123456789abcdef";
        String key = "hse-automation:v1:" + "a".repeat(64);
        String event = """
                {
                  "schema_version":"1.0",
                  "event_id":"%s",
                  "idempotency_key":"%s",
                  "rule_id":"AUT-001",
                  "entity_type":"PERMIT",
                  "entity_id":"PTW-SEC-1",
                  "alert_code":"PERMIT_OVERDUE",
                  "action":"FLAG_OVERDUE_PERMIT",
                  "evaluated_at_utc":"2026-08-23T12:00:00Z",
                  "business_date":"2026-08-23",
                  "payload":{"permit_id":"PTW-SEC-1","status":"ACTIVE","minutes_overdue":120}
                }
                """.formatted(eventId, key);

        mvc.perform(post("/api/v1/internal/automation/actions")
                        .contentType(MediaType.APPLICATION_JSON)
                        .header("Idempotency-Key", key)
                        .header("X-Correlation-ID", eventId)
                        .header("X-Event-Schema-Version", "1.0")
                        .content(event))
                .andExpect(status().isUnauthorized());

        mvc.perform(post("/api/v1/internal/automation/actions")
                        .contentType(MediaType.APPLICATION_JSON)
                        .header("Authorization", "Bearer " + serviceToken)
                        .header("Idempotency-Key", key)
                        .header("X-Correlation-ID", eventId)
                        .header("X-Event-Schema-Version", "1.0")
                        .content(event))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("APPLIED"));

        mvc.perform(post("/api/v1/internal/automation/actions")
                        .contentType(MediaType.APPLICATION_JSON)
                        .header("Authorization", "Bearer " + serviceToken)
                        .header("Idempotency-Key", key)
                        .header("X-Correlation-ID", eventId)
                        .header("X-Event-Schema-Version", "1.0")
                        .content(event))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("DUPLICATE"));

        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM automation_actions WHERE idempotency_key=?", Integer.class, key)).isEqualTo(1);
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM notifications WHERE entity_id='PTW-SEC-1'", Integer.class)).isEqualTo(1);
    }
}
