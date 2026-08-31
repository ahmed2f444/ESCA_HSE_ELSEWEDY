package com.esca.hse;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class WorkPermitControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void testListPermitsEndpoint() throws Exception {
        mvc.perform(get("/api/v1/permits"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON));
    }

    @Test
    void testPermitStatsAndSimopsEndpoints() throws Exception {
        mvc.perform(get("/api/v1/permits/stats"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.total").isNumber());

        mvc.perform(get("/api/v1/permits/simops"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.rules").isArray());

        mvc.perform(get("/api/v1/permits/checklist"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(1))));
    }

    @Test
    void testFullPermitCrudAndWorkflowLifecycle() throws Exception {
        // 1. CREATE
        String createPayload = """
                {
                    "permitType": "HOT_WORK",
                    "workDescription": "Spring Test Welding Pipeline in Zone 1",
                    "zoneId": 1,
                    "riskLevel": "HIGH",
                    "durationHours": 6,
                    "executorName": "QA Testing Maintenance Team",
                    "gasTestRequired": true,
                    "gasO2": 20.9,
                    "gasLel": 0.0,
                    "status": "ACTIVE"
                }
                """;

        String createRes = mvc.perform(post("/api/v1/permits")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createPayload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.permitId").isNumber())
                .andExpect(jsonPath("$.permitCode", startsWith("PTW-")))
                .andReturn().getResponse().getContentAsString();

        // Extract Permit ID
        int permitId = com.jayway.jsonpath.JsonPath.read(createRes, "$.permitId");
        String ptwCode = "PTW-" + String.format("%03d", permitId);

        // 2. GET DETAILS
        mvc.perform(get("/api/v1/permits/" + permitId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.permit.permitId").value(permitId))
                .andExpect(jsonPath("$.permit.status").value("ACTIVE"));

        // 2b. GET APPROVALS WORKFLOW & DIGITAL SIGNATURES
        mvc.perform(get("/api/v1/permits/" + permitId + "/approvals"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.steps", hasSize(greaterThanOrEqualTo(1))))
                .andExpect(jsonPath("$.signature.hash").exists());

        // 3. UPDATE
        String updatePayload = """
                {
                    "workDescription": "Spring Test Welding and Grinding Updated",
                    "durationHours": 10
                }
                """;
        mvc.perform(put("/api/v1/permits/" + ptwCode)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(updatePayload))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));

        // 4. SUSPEND
        String suspendPayload = "{\"reason\": \"Temporary halt for inspection\"}";
        mvc.perform(post("/api/v1/permits/" + permitId + "/suspend")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(suspendPayload))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SUSPENDED"));

        // 5. APPROVE / RE-ACTIVATE
        mvc.perform(post("/api/v1/permits/" + permitId + "/approve"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("ACTIVE"));

        // 6. CLOSE
        mvc.perform(post("/api/v1/permits/" + permitId + "/close"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CLOSED"));

        // 7. DELETE
        mvc.perform(delete("/api/v1/permits/" + permitId).param("reason", "Spring Test cleanup"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }
}
