package com.esca.hse;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class CoreApiIntegrationTests {
    @Autowired MockMvc mvc;
    @Autowired JdbcTemplate jdbc;

    @BeforeEach
    void cleanCoreTables() {
        jdbc.update("DELETE FROM automation_actions");
        jdbc.update("DELETE FROM notifications");
        jdbc.update("DELETE FROM audit_log");
        jdbc.update("DELETE FROM incidents");
        jdbc.update("DELETE FROM permits");
        jdbc.update("DELETE FROM capa");
    }

    @Test
    void incidentCrudAndAuditAreIntegrated() throws Exception {
        String body = """
                {"incidentType":"OBSERVATION","title":"Emergency exit blocked","description":"Training test", "occurredAt":"2026-08-23T10:00:00","severity":"HIGH"}
                """;
        String response = mvc.perform(post("/api/v1/incidents").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status").value("OPEN"))
                .andReturn().getResponse().getContentAsString();
        assertThat(response).contains("Emergency exit blocked");
        assertThat(jdbc.queryForObject("SELECT COUNT(*) FROM audit_log WHERE action='CREATE' AND entity_type='INCIDENTS'", Integer.class)).isEqualTo(1);
    }

    @Test
    void workflowTransitionUpdatesIncident() throws Exception {
        jdbc.update("INSERT INTO incidents (incident_id,incident_type,title,occurred_at,severity,status) VALUES ('INC-T1','OBSERVATION','Test',CURRENT_TIMESTAMP,'LOW','OPEN')");
        mvc.perform(patch("/api/v1/incidents/INC-T1/close").contentType(MediaType.APPLICATION_JSON).content("{\"rootCause\":\"Procedure gap\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CLOSED"));
        assertThat(jdbc.queryForObject("SELECT closed_at FROM incidents WHERE incident_id='INC-T1'", java.sql.Timestamp.class)).isNotNull();
    }

    @Test
    void dashboardAndReportsReturnStableContracts() throws Exception {
        mvc.perform(get("/api/v1/dashboard"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("ready"))
                .andExpect(jsonPath("$.kpis.openIncidents").isNumber());
        mvc.perform(get("/api/v1/reports/summary"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.incidentsBySeverity").isArray());
    }
}
