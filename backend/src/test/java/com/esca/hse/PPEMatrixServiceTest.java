package com.esca.hse;

import com.esca.hse.model.PPEMatrix;
import com.esca.hse.repository.PPEMatrixRepository;
import com.esca.hse.service.PPEMatrixService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PPEMatrixServiceTest {

    @Mock
    private PPEMatrixRepository repository;

    @InjectMocks
    private PPEMatrixService service;

    private PPEMatrix rule1;
    private PPEMatrix rule2;

    @BeforeEach
    void setUp() {
        rule1 = new PPEMatrix("PPM-001", "ZN-A1", "PPE-1001", 1, "Mandatory safety helmet");
        rule2 = new PPEMatrix("PPM-002", "ZN-A1", "PPE-1002", 1, "Mandatory gloves");
    }

    @Test
    @DisplayName("getAllMatrixEntries returns all rules from repository")
    void getAllMatrixEntries_returnsList() {
        when(repository.findAll()).thenReturn(List.of(rule1, rule2));

        List<PPEMatrix> result = service.getAllMatrixEntries();

        assertThat(result).hasSize(2).contains(rule1, rule2);
    }

    @Test
    @DisplayName("getMatrixByZone returns rules matching zone ID")
    void getMatrixByZone_returnsMatching() {
        when(repository.findByZoneIdIgnoreCase("ZN-A1")).thenReturn(List.of(rule1, rule2));

        List<PPEMatrix> result = service.getMatrixByZone("ZN-A1");

        assertThat(result).hasSize(2);
    }

    @Test
    @DisplayName("createMatrixEntry saves and generates ID if blank")
    void createMatrixEntry_savesEntity() {
        PPEMatrix newRule = new PPEMatrix(null, "ZN-B1", "PPE-1004", 1, "Safety boots");
        when(repository.save(any(PPEMatrix.class))).thenAnswer(inv -> inv.getArgument(0));

        PPEMatrix created = service.createMatrixEntry(newRule);

        assertThat(created.getMatrixId()).isNotNull().startsWith("PPM-");
        verify(repository).save(newRule);
    }

    @Test
    @DisplayName("getSummary calculates zone and mandatory item counts")
    void getSummary_returnsStatistics() {
        when(repository.findAll()).thenReturn(List.of(rule1, rule2));

        Map<String, Object> summary = service.getSummary();

        assertThat(summary.get("totalRules")).isEqualTo(2);
        assertThat(summary.get("totalZones")).isEqualTo(1);
        assertThat(summary.get("mandatoryRules")).isEqualTo(2L);
    }
}
