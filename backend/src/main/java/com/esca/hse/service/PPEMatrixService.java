package com.esca.hse.service;

import com.esca.hse.model.PPEMatrix;
import com.esca.hse.platform.EntityIdUtils;
import com.esca.hse.repository.PPEMatrixRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class PPEMatrixService {

    private static final RowMapper<PPEMatrix> ROW_MAPPER = (rs, rowNum) -> {
        PPEMatrix m = new PPEMatrix();
        int id = rs.getInt("matrix_id");
        int pid = rs.getInt("ppe_item_id");
        m.setMatrixId(EntityIdUtils.formatId("PPM", id));
        m.setZoneId(rs.getString("zone_name"));
        m.setPpeItemId(EntityIdUtils.formatId("PPE", pid));
        m.setRequiredFlag(rs.getInt("required_flag"));
        m.setNotes(rs.getString("notes"));
        return m;
    };

    private final PPEMatrixRepository repository;
    private final NamedParameterJdbcTemplate jdbc;

    public PPEMatrixService(
            @Autowired(required = false) PPEMatrixRepository repository,
            @Autowired(required = false) NamedParameterJdbcTemplate jdbc) {
        this.repository = repository;
        this.jdbc = jdbc;
    }

    public List<PPEMatrix> getAllMatrixEntries() {
        if (jdbc != null) {
            try {
                String sql = "SELECT pm.matrix_id, pm.zone_id, pm.ppe_item_id, pm.required_flag, pm.notes, " +
                        "COALESCE(z.name_ar, 'Zone A') as zone_name, " +
                        "COALESCE(p.name_ar, 'معدة وقاية') as item_name " +
                        "FROM ppe_matrix pm " +
                        "LEFT JOIN zones z ON pm.zone_id = z.zone_id " +
                        "LEFT JOIN ppe_inventory p ON pm.ppe_item_id = p.ppe_item_id " +
                        "ORDER BY pm.matrix_id ASC";

                return jdbc.query(sql, ROW_MAPPER);
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            return repository.findAll();
        }
        return Collections.emptyList();
    }

    public PPEMatrix getMatrixEntryById(String id) {
        if (repository != null) {
            return repository.findByMatrixIdIgnoreCase(id).orElse(null);
        }
        return null;
    }

    public List<PPEMatrix> getMatrixByZone(String zoneId) {
        if (repository != null) {
            return repository.findByZoneIdIgnoreCase(zoneId);
        }
        return Collections.emptyList();
    }

    public List<PPEMatrix> getMatrixByItem(String ppeItemId) {
        if (repository != null) {
            return repository.findByPpeItemIdIgnoreCase(ppeItemId);
        }
        return Collections.emptyList();
    }

    public PPEMatrix createMatrixEntry(PPEMatrix matrix) {
        if (matrix.getMatrixId() == null || matrix.getMatrixId().isBlank()) {
            matrix.setMatrixId("PPM-" + System.currentTimeMillis());
        }
        if (repository != null) {
            return repository.save(matrix);
        }
        return matrix;
    }

    public PPEMatrix updateMatrixEntry(String id, PPEMatrix updated) {
        if (repository != null) {
            if (!repository.existsById(id)) return null;
            updated.setMatrixId(id);
            return repository.save(updated);
        }
        return updated;
    }

    public boolean deleteMatrixEntry(String id) {
        if (repository != null) {
            if (!repository.existsById(id)) return false;
            repository.deleteById(id);
            return true;
        }
        return true;
    }

    public Map<String, Object> getSummary() {
        List<PPEMatrix> all = (repository != null) ? repository.findAll() : getAllMatrixEntries();
        Map<String, Object> summary = new LinkedHashMap<>();

        Set<String> distinctZones = all.stream()
                .map(PPEMatrix::getZoneId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());

        Set<String> distinctItems = all.stream()
                .map(PPEMatrix::getPpeItemId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());

        long mandatoryCount = all.stream().filter(m -> m.getRequiredFlag() != null && m.getRequiredFlag() == 1).count();
        long taskDependentCount = all.stream().filter(m -> m.getRequiredFlag() != null && m.getRequiredFlag() == 2).count();
        long notRequiredCount = all.stream().filter(m -> m.getRequiredFlag() != null && m.getRequiredFlag() == 0).count();

        summary.put("totalRules", all.size());
        summary.put("totalZones", distinctZones.size());
        summary.put("mandatoryRules", mandatoryCount);
        summary.put("distinctZones", distinctZones.size());
        summary.put("distinctItems", distinctItems.size());
        summary.put("mandatoryCount", mandatoryCount);
        summary.put("taskDependentCount", taskDependentCount);
        summary.put("notRequiredCount", notRequiredCount);

        return summary;
    }
}
