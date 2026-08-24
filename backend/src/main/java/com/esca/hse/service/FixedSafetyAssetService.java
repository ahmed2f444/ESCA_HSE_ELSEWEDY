package com.esca.hse.service;

import com.esca.hse.model.FixedSafetyAsset;
import com.esca.hse.platform.EntityIdUtils;
import com.esca.hse.repository.FixedSafetyAssetRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class FixedSafetyAssetService {

    private static final RowMapper<FixedSafetyAsset> ROW_MAPPER = (rs, rowNum) -> {
        FixedSafetyAsset asset = new FixedSafetyAsset();
        int id = rs.getInt("asset_summary_id");
        asset.setId(EntityIdUtils.formatId("FSA", id));
        asset.setAssetType(rs.getString("asset_type"));
        asset.setAssetName(rs.getString("asset_name"));
        asset.setZoneId("ZONE-A");
        asset.setLocationDetail("الموقع الرئيسي");

        String st = rs.getString("status_name");
        asset.setStatus("VALID".equalsIgnoreCase(st) ? "OPERATIONAL" : st);
        return asset;
    };

    private final FixedSafetyAssetRepository repository;
    private final NamedParameterJdbcTemplate jdbc;

    public FixedSafetyAssetService(
            @Autowired(required = false) FixedSafetyAssetRepository repository,
            @Autowired(required = false) NamedParameterJdbcTemplate jdbc) {
        this.repository = repository;
        this.jdbc = jdbc;
    }

    public List<FixedSafetyAsset> getAllAssets() {
        if (jdbc != null) {
            try {
                String sql = "SELECT fa.asset_summary_id, fa.asset_type, fa.asset_name, fa.total_qty, " +
                        "fa.operational_qty, fa.last_test_date, fa.next_test_date, fa.status_id, fa.notes, " +
                        "COALESCE(fas.name, 'VALID') as status_name " +
                        "FROM fixed_safety_assets fa " +
                        "LEFT JOIN fixed_safety_asset_statuses fas ON fa.status_id = fas.fixed_safety_asset_status_id " +
                        "ORDER BY fa.asset_summary_id ASC";

                return jdbc.query(sql, ROW_MAPPER);
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            return repository.findAll();
        }
        return Collections.emptyList();
    }

    public FixedSafetyAsset getAssetById(String id) {
        if (repository != null) {
            return repository.findById(id).orElse(null);
        }
        return null;
    }

    public List<FixedSafetyAsset> getAssetsByZone(String zoneId) {
        if (repository != null) {
            return repository.findByZoneIdIgnoreCase(zoneId);
        }
        return Collections.emptyList();
    }

    public List<FixedSafetyAsset> getAssetsByType(String assetType) {
        if (repository != null) {
            return repository.findByAssetTypeIgnoreCase(assetType);
        }
        return Collections.emptyList();
    }

    public FixedSafetyAsset createAsset(FixedSafetyAsset asset) {
        if (asset.getId() == null || asset.getId().isBlank()) {
            asset.setId("FSA-" + System.currentTimeMillis());
        }
        if (repository != null) {
            return repository.save(asset);
        }
        return asset;
    }

    public FixedSafetyAsset updateAsset(String id, FixedSafetyAsset updated) {
        if (repository != null) {
            if (!repository.existsById(id)) return null;
            updated.setId(id);
            return repository.save(updated);
        }
        return updated;
    }

    public boolean deleteAsset(String id) {
        if (repository != null) {
            if (!repository.existsById(id)) return false;
            repository.deleteById(id);
            return true;
        }
        return true;
    }

    public Map<String, Object> getAssetSummary() {
        List<FixedSafetyAsset> all = getAllAssets();
        Map<String, Object> summary = new LinkedHashMap<>();

        long operational = all.stream().filter(a -> "OPERATIONAL".equalsIgnoreCase(a.getStatus())).count();
        long maintenance = all.stream().filter(a -> "MAINTENANCE".equalsIgnoreCase(a.getStatus()) || "UNDER_MAINTENANCE".equalsIgnoreCase(a.getStatus())).count();
        long outOfService = all.stream().filter(a -> "OUT_OF_SERVICE".equalsIgnoreCase(a.getStatus()) || "DEFECTIVE".equalsIgnoreCase(a.getStatus())).count();

        summary.put("totalAssets", all.size());
        summary.put("operational", operational);
        summary.put("maintenance", maintenance);
        summary.put("outOfService", outOfService);

        return summary;
    }
}
