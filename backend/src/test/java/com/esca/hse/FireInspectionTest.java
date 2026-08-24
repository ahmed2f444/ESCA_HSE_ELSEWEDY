package com.esca.hse;

import com.esca.hse.model.FireInspection;
import com.esca.hse.service.FireInspectionService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.springframework.web.context.WebApplicationContext;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

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
class FireInspectionTest {

    private MockMvcTester mvc;

    @Autowired
    private WebApplicationContext wac;

    @MockitoBean
    private FireInspectionService service;

    private FireInspection sampleInsp;

    @BeforeEach
    void setUp() {
        mvc = MockMvcTester.from(wac);
        sampleInsp = new FireInspection("INSP-001", "FE-1001", LocalDate.now(), "Inspector Ali", "PASSED", "All good");
    }

    @Test
    @DisplayName("GET /api/fire/inspections returns list of inspections")
    void getAllInspections_returns200() {
        when(service.getAllInspections()).thenReturn(List.of(sampleInsp));

        assertThat(mvc.get().uri("/api/fire/inspections"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$[0].id").asString().isEqualTo("INSP-001");
    }

    @Test
    @DisplayName("GET /api/fire/inspections/{id} returns single inspection")
    void getInspectionById_found_returns200() {
        when(service.getInspectionById("INSP-001")).thenReturn(sampleInsp);

        assertThat(mvc.get().uri("/api/fire/inspections/INSP-001"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.status").asString().isEqualTo("PASSED");
    }

    @Test
    @DisplayName("POST /api/fire/inspections creates new inspection")
    void createInspection_valid_returns201() {
        when(service.createInspection(any(FireInspection.class))).thenReturn(sampleInsp);

        String json = """
            {
                "id": "INSP-001",
                "equipmentId": "FE-1001",
                "inspectionDate": "2026-08-01",
                "inspectorName": "Inspector Ali",
                "status": "PASSED",
                "notes": "All good"
            }
            """;

        assertThat(mvc.post().uri("/api/fire/inspections")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .hasStatus(201)
                .bodyJson()
                .extractingPath("$.id").asString().isEqualTo("INSP-001");
    }

    @Test
    @DisplayName("GET /api/fire/inspections/summary returns summary stats")
    void getSummary_returns200() {
        when(service.getInspectionSummary()).thenReturn(Map.of("totalInspections", 5, "passed", 4));

        assertThat(mvc.get().uri("/api/fire/inspections/summary"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.totalInspections").asNumber().isEqualTo(5);
    }
}
