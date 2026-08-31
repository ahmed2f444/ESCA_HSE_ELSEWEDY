package com.esca.hse;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class HazmatControllerTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void testHazmatStatsAndCompatibilityEndpoints() throws Exception {
        mvc.perform(get("/api/v1/hazmat/stats"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.total").isNumber())
                .andExpect(jsonPath("$.flammable").isNumber());

        mvc.perform(get("/api/v1/hazmat/compatibility"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.groups").isArray())
                .andExpect(jsonPath("$.grid").isArray());
    }

    @Test
    void testChemicalsCrudLifecycle() throws Exception {
        // 1. CREATE CHEMICAL
        String createPayload = """
                {
                    "tradeName": "ACETONE 99.5% PURITY",
                    "chemicalName": "Acetone / Dimethyl Ketone",
                    "casNumber": "67-64-1",
                    "supplier": "Elsewedy Chemical Supply",
                    "quantity": 350.0,
                    "unit": "L",
                    "ghsClasses": "FLAMMABLE",
                    "storageClass": "Class 3",
                    "zoneId": 1,
                    "statusId": 1,
                    "sdsVersion": "Rev 1",
                    "emergencySummary": "عزل المنطقة والابتعاد عن مصادر اللهب وتوفير رغوة إطفاء."
                }
                """;

        String res = mvc.perform(post("/api/v1/hazmat/chemicals")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createPayload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.chemicalId").isNumber())
                .andExpect(jsonPath("$.tradeName").value("ACETONE 99.5% PURITY"))
                .andExpect(jsonPath("$.code", startsWith("CHM-")))
                .andReturn().getResponse().getContentAsString();

        int chemId = com.jayway.jsonpath.JsonPath.read(res, "$.chemicalId");

        // 2. GET BY ID
        mvc.perform(get("/api/v1/hazmat/chemicals/" + chemId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.chemicalId").value(chemId))
                .andExpect(jsonPath("$.casNumber").value("67-64-1"))
                .andExpect(jsonPath("$.ghs").exists());

        // 3. UPDATE CHEMICAL
        String updatePayload = """
                {
                    "tradeName": "ACETONE 99.5% PURITY UPDATED",
                    "quantity": 500.0
                }
                """;

        mvc.perform(put("/api/v1/hazmat/chemicals/" + chemId)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(updatePayload))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tradeName").value("ACETONE 99.5% PURITY UPDATED"))
                .andExpect(jsonPath("$.quantity").value(500.0));

        // 4. LIST CHEMICALS WITH QUERY
        mvc.perform(get("/api/v1/hazmat/chemicals").param("query", "ACETONE"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(1))));

        // 5. DELETE CHEMICAL
        mvc.perform(delete("/api/v1/hazmat/chemicals/" + chemId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    void testSdsArchiveLifecycle() throws Exception {
        // 1. LIST SDS
        mvc.perform(get("/api/v1/hazmat/sds"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON));

        // 2. CREATE SDS
        String sdsPayload = """
                {
                    "chemicalId": 1,
                    "versionNo": "Rev 2026-X",
                    "issueDate": "2026-01-15",
                    "expiryDate": "2028-01-15",
                    "language": "EN/AR",
                    "emergencySummary": "استخدام أقنعة التنفس وحفظ المادة في مكان جاف وجيد التهوية."
                }
                """;

        String res = mvc.perform(post("/api/v1/hazmat/sds")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(sdsPayload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.sdsId").isNumber())
                .andReturn().getResponse().getContentAsString();

        int sdsId = com.jayway.jsonpath.JsonPath.read(res, "$.sdsId");

        // 3. DELETE SDS
        if (sdsId > 0) {
            mvc.perform(delete("/api/v1/hazmat/sds/" + sdsId))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.success").value(true));
        }
    }
}
