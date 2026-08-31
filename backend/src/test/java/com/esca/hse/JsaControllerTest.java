package com.esca.hse;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import tools.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class JsaControllerTest {

    @Autowired
    private MockMvc mvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void testJsaStatsEndpoint() throws Exception {
        mvc.perform(get("/api/v1/jsa/stats"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.approved").isNumber())
                .andExpect(jsonPath("$.criticalTaskCoverage").isNumber());
    }

    @Test
    void testJsaListEndpoint() throws Exception {
        mvc.perform(get("/api/v1/jsa"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    void testJsaAvailablePermitsEndpoint() throws Exception {
        mvc.perform(get("/api/v1/jsa/available-permits"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    void testFullJsaCrudWorkflowAndPermitLink() throws Exception {
        // 1. CREATE
        String createPayload = """
                {
                    "taskName": "Test Overhead Cable Jointing & LOTO",
                    "zoneId": 1,
                    "permitRequired": true,
                    "permitType": "HOT_WORK",
                    "frequency": "AS_NEEDED",
                    "inherentScore": 16,
                    "residualScore": 4,
                    "status": "DRAFT",
                    "steps": [
                        {
                            "step": "عزل القواطع الكهربائية والتأكد من انعدام الجهد",
                            "hazard": "صعق كهربائي وقوس عالي",
                            "control": "تطبيق إجراءات LOTO وفحص الجهد بمقياس معتمد",
                            "before": 16,
                            "after": 4,
                            "responsible": "مسؤول السلامة"
                        },
                        {
                            "step": "تأمين موقع العمل ومراقبة الحريق",
                            "hazard": "تطاير الشرر واشتعال المواد المجاورة",
                            "control": "توفير مراقب حريق ومطفأة بودرة 6 كجم",
                            "before": 15,
                            "after": 3,
                            "responsible": "مراقب الحريق"
                        }
                    ]
                }
                """;

        MvcResult createResult = mvc.perform(post("/api/v1/jsa")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(createPayload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.taskName").value("Test Overhead Cable Jointing & LOTO"))
                .andExpect(jsonPath("$.steps", hasSize(2)))
                .andReturn();

        String responseJson = createResult.getResponse().getContentAsString();
        Map<?, ?> createdJsa = objectMapper.readValue(responseJson, Map.class);
        String jsaId = String.valueOf(createdJsa.get("numericId"));

        // 2. GET BY ID
        mvc.perform(get("/api/v1/jsa/" + jsaId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taskName").value("Test Overhead Cable Jointing & LOTO"))
                .andExpect(jsonPath("$.steps", hasSize(2)));

        // 3. APPROVE JSA
        mvc.perform(patch("/api/v1/jsa/" + jsaId + "/approve"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.statusId").value(3));

        // 4. ADD STEP
        String stepPayload = """
                {
                    "step": "فحص نهائي وإخلاء الموقع",
                    "hazard": "ترك أدوات أو مواد غير مستقرة",
                    "control": "التنظيف والترتيب وإعادة تشغيل المعدات تحت إشراف",
                    "before": 10,
                    "after": 2,
                    "responsible": "مشرف الوردية"
                }
                """;

        mvc.perform(post("/api/v1/jsa/" + jsaId + "/steps")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(stepPayload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.steps", hasSize(3)));

        // 5. LINK PERMIT
        mvc.perform(post("/api/v1/jsa/" + jsaId + "/link-permit")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"permitId\": 1}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));

        // 6. DELETE JSA
        mvc.perform(delete("/api/v1/jsa/" + jsaId))
                .andExpect(status().isNoContent());
    }
}
