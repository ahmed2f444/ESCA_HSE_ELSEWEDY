package com.esca.hse;

import com.esca.hse.model.PPEMatrix;
import com.esca.hse.service.PPEMatrixService;
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

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

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
class PPEMatrixControllerTest {

    private MockMvcTester mvc;

    @Autowired
    private WebApplicationContext wac;

    @MockitoBean
    private PPEMatrixService service;

    private PPEMatrix sampleRule;

    @BeforeEach
    void setUp() {
        mvc = MockMvcTester.from(wac);
        sampleRule = new PPEMatrix("PPM-001", "ZN-A1", "PPE-1001", 1, "Mandatory safety helmet");
    }

    @Test
    @DisplayName("GET /api/ppe/matrix returns list of rules")
    void getAllMatrix_returns200() {
        when(service.getAllMatrixEntries()).thenReturn(List.of(sampleRule));

        assertThat(mvc.get().uri("/api/ppe/matrix"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$[0].matrixId").asString().isEqualTo("PPM-001");
    }

    @Test
    @DisplayName("GET /api/ppe/matrix/{id} returns single rule")
    void getMatrixById_found_returns200() {
        when(service.getMatrixEntryById("PPM-001")).thenReturn(sampleRule);

        assertThat(mvc.get().uri("/api/ppe/matrix/PPM-001"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.zoneId").asString().isEqualTo("ZN-A1");
    }

    @Test
    @DisplayName("POST /api/ppe/matrix with valid body creates rule")
    void createMatrix_valid_returns201() {
        when(service.createMatrixEntry(any(PPEMatrix.class))).thenReturn(sampleRule);

        String json = """
            {
                "matrixId": "PPM-001",
                "zoneId": "ZN-A1",
                "ppeItemId": "PPE-1001",
                "requiredFlag": 1,
                "notes": "Mandatory safety helmet"
            }
            """;

        assertThat(mvc.post().uri("/api/ppe/matrix")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .hasStatus(201)
                .bodyJson()
                .extractingPath("$.matrixId").asString().isEqualTo("PPM-001");
    }

    @Test
    @DisplayName("DELETE /api/ppe/matrix/{id} deletes rule")
    void deleteMatrix_returns204() {
        when(service.deleteMatrixEntry("PPM-001")).thenReturn(true);

        assertThat(mvc.delete().uri("/api/ppe/matrix/PPM-001"))
                .hasStatus(204);
    }
}
