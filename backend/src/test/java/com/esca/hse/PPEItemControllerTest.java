package com.esca.hse;

import com.esca.hse.model.PPEItem;
import com.esca.hse.service.PPEItemService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.springframework.web.context.WebApplicationContext;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Spring MVC integration tests for PPEItemController.
 */
@SpringBootTest(
    webEnvironment = SpringBootTest.WebEnvironment.MOCK,
    properties = {
        "spring.autoconfigure.exclude=" +
            "org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration," +
            "org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration," +
            "org.springframework.boot.autoconfigure.data.jpa.JpaRepositoriesAutoConfiguration",
        "spring.sql.init.mode=never"
    }
)
class PPEItemControllerTest {

    private MockMvcTester mvc;

    @Autowired
    private WebApplicationContext wac;

    @MockitoBean
    private PPEItemService service;

    private PPEItem sampleItem;

    @BeforeEach
    void setUp() {
        mvc = MockMvcTester.from(wac);

        sampleItem = new PPEItem();
        sampleItem.setPpeItemId("PPE-001");
        sampleItem.setItemCode("HELM-01");
        sampleItem.setNameAr("Safety Helmet");
        sampleItem.setCategoryId("HEAD_PROTECTION");
        sampleItem.setUnit("pcs");
        sampleItem.setBalanceQty(50);
        sampleItem.setReorderThreshold(10);
        sampleItem.setMonthlyConsumption(5);
    }

    // ──────────────────────────── GET all ────────────────────────────────

    @Test
    @DisplayName("GET /api/ppe-items returns 200 with list of items")
    void getAllItems_returns200() {
        when(service.getAllItems()).thenReturn(List.of(sampleItem));

        assertThat(mvc.get().uri("/api/ppe-items"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$[0].ppeItemId").asString().isEqualTo("PPE-001");
    }

    // ──────────────────────────── GET by ID ──────────────────────────────

    @Test
    @DisplayName("GET /api/ppe-items/{id} returns 200 when item exists")
    void getItemById_exists_returns200() {
        when(service.getItemById("PPE-001")).thenReturn(sampleItem);

        assertThat(mvc.get().uri("/api/ppe-items/PPE-001"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.ppeItemId").asString().isEqualTo("PPE-001");
    }

    @Test
    @DisplayName("GET /api/ppe-items/{id} returns 404 when item does not exist")
    void getItemById_notFound_returns404() {
        when(service.getItemById("PPE-999")).thenReturn(null);

        assertThat(mvc.get().uri("/api/ppe-items/PPE-999"))
                .hasStatus(404);
    }

    // ──────────────────────────── GET summary ────────────────────────────

    @Test
    @DisplayName("GET /api/ppe-items/summary returns 200 with KPI map")
    void getSummary_returns200() {
        Map<String, Object> summary = Map.of(
                "totalItems", 10,
                "belowThreshold", 2,
                "lowStock", 1,
                "available", 7,
                "reorderWithin14Days", 3
        );
        when(service.getSummary()).thenReturn(summary);

        assertThat(mvc.get().uri("/api/ppe-items/summary"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.totalItems").isEqualTo(10);
    }

    // ──────────────────────────── POST ───────────────────────────────────

    @Test
    @DisplayName("POST /api/ppe-items with valid body returns 201")
    void createItem_validBody_returns201() {
        when(service.createItem(any())).thenReturn(sampleItem);

        String validJson = """
            {
              "ppeItemId": "PPE-001",
              "itemCode": "HELM-01",
              "nameAr": "Safety Helmet",
              "categoryId": "HEAD_PROTECTION",
              "unit": "pcs",
              "balanceQty": 50,
              "reorderThreshold": 10,
              "monthlyConsumption": 5
            }
            """;

        assertThat(mvc.post().uri("/api/ppe-items")
                .contentType(MediaType.APPLICATION_JSON)
                .content(validJson))
                .hasStatus(201)
                .bodyJson()
                .extractingPath("$.ppeItemId").asString().isEqualTo("PPE-001");
    }

    @Test
    @DisplayName("POST /api/ppe-items with missing required fields returns 400 with field errors")
    void createItem_missingFields_returns400() {
        String invalidJson = """
            {
              "balanceQty": 10
            }
            """;

        assertThat(mvc.post().uri("/api/ppe-items")
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidJson))
                .hasStatus(400)
                .bodyJson()
                .extractingPath("$.error").asString().isEqualTo("Validation failed");
    }

    @Test
    @DisplayName("POST /api/ppe-items with negative balanceQty returns 400")
    void createItem_negativeQty_returns400() {
        String invalidJson = """
            {
              "ppeItemId": "PPE-002",
              "itemCode": "BOOT-01",
              "nameAr": "Safety Boot",
              "categoryId": "FOOT_PROTECTION",
              "unit": "pair",
              "balanceQty": -5,
              "reorderThreshold": 10,
              "monthlyConsumption": 2
            }
            """;

        assertThat(mvc.post().uri("/api/ppe-items")
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidJson))
                .hasStatus(400)
                .bodyJson()
                .hasPathSatisfying("$.fields.balanceQty", v -> assertThat(v).isNotNull());
    }

    // ──────────────────────────── DELETE ─────────────────────────────────

    @Test
    @DisplayName("DELETE /api/ppe-items/{id} returns 204")
    void deleteItem_returns204() {
        doNothing().when(service).deleteItem("PPE-001");

        assertThat(mvc.delete().uri("/api/ppe-items/PPE-001"))
                .hasStatus(204);
    }

    @Test
    @DisplayName("DELETE /api/ppe-items/{id} with associated transactions returns 409 Conflict")
    void deleteItem_associatedTransactions_returns409() {
        doThrow(new org.springframework.dao.DataIntegrityViolationException("Constraint violation"))
                .when(service).deleteItem("PPE-001");

        assertThat(mvc.delete().uri("/api/ppe-items/PPE-001"))
                .hasStatus(409)
                .bodyJson()
                .extractingPath("$.error").asString()
                .contains("Cannot delete PPE Item because it has associated transaction records");
    }
}
