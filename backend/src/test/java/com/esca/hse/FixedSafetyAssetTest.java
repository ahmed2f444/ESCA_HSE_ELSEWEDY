package com.esca.hse;

import com.esca.hse.model.FixedSafetyAsset;
import com.esca.hse.service.FixedSafetyAssetService;
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
class FixedSafetyAssetTest {

    private MockMvcTester mvc;

    @Autowired
    private WebApplicationContext wac;

    @MockitoBean
    private FixedSafetyAssetService service;

    private FixedSafetyAsset sampleAsset;

    @BeforeEach
    void setUp() {
        mvc = MockMvcTester.from(wac);
        sampleAsset = new FixedSafetyAsset("FSA-001", "Emergency Eyewash 1", "EYEWASH_STATION", "ZN-CHEM", "Chemical Bay Entrance", "OPERATIONAL");
    }

    @Test
    @DisplayName("GET /api/safety/fixed-assets returns list of fixed assets")
    void getAllAssets_returns200() {
        when(service.getAllAssets()).thenReturn(List.of(sampleAsset));

        assertThat(mvc.get().uri("/api/safety/fixed-assets"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$[0].id").asString().isEqualTo("FSA-001");
    }

    @Test
    @DisplayName("GET /api/safety/fixed-assets/{id} returns single asset")
    void getAssetById_found_returns200() {
        when(service.getAssetById("FSA-001")).thenReturn(sampleAsset);

        assertThat(mvc.get().uri("/api/safety/fixed-assets/FSA-001"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.assetName").asString().isEqualTo("Emergency Eyewash 1");
    }

    @Test
    @DisplayName("POST /api/safety/fixed-assets creates new asset")
    void createAsset_valid_returns201() {
        when(service.createAsset(any(FixedSafetyAsset.class))).thenReturn(sampleAsset);

        String json = """
            {
                "id": "FSA-001",
                "assetName": "Emergency Eyewash 1",
                "assetType": "EYEWASH_STATION",
                "zoneId": "ZN-CHEM",
                "locationDetail": "Chemical Bay Entrance",
                "status": "OPERATIONAL"
            }
            """;

        assertThat(mvc.post().uri("/api/safety/fixed-assets")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
                .hasStatus(201)
                .bodyJson()
                .extractingPath("$.id").asString().isEqualTo("FSA-001");
    }

    @Test
    @DisplayName("GET /api/safety/fixed-assets/summary returns summary stats")
    void getSummary_returns200() {
        when(service.getAssetSummary()).thenReturn(Map.of("totalAssets", 6, "operational", 5));

        assertThat(mvc.get().uri("/api/safety/fixed-assets/summary"))
                .hasStatusOk()
                .bodyJson()
                .extractingPath("$.totalAssets").asNumber().isEqualTo(6);
    }
}
