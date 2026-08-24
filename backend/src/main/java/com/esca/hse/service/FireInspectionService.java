package com.esca.hse.service;

import com.esca.hse.model.FireInspection;
import com.esca.hse.platform.EntityIdUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Service;

import java.sql.Date;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class FireInspectionService {

    private static final RowMapper<FireInspection> ROW_MAPPER = (rs, rowNum) -> {
        FireInspection fi = new FireInspection();
        int id = rs.getInt("fire_inspection_id");
        int eqId = rs.getInt("equipment_id");
        fi.setId(EntityIdUtils.formatId("INSP", id));
        fi.setEquipmentId(EntityIdUtils.formatId("FE", eqId));

        Timestamp inspAt = rs.getTimestamp("inspected_at");
        if (inspAt != null) {
            fi.setInspectionDate(inspAt.toLocalDateTime().toLocalDate());
        }

        fi.setInspectorName(rs.getString("inspector_name"));
        String res = rs.getString("result_name");
        fi.setStatus("PASS".equalsIgnoreCase(res) ? "PASSED" : "FAIL".equalsIgnoreCase(res) ? "FAILED" : "MAINTENANCE_REQUIRED");
        fi.setNotes(rs.getString("action_required"));
        return fi;
    };

    private final NamedParameterJdbcTemplate jdbc;

    public FireInspectionService(@Autowired(required = false) NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<FireInspection> getAllInspections() {
        if (jdbc != null) {
            try {
                String sql = "SELECT fi.fire_inspection_id, fi.equipment_id, fi.inspected_at, fi.inspector_id, " +
                        "fi.present_flag, fi.access_clear, fi.pressure_ok, fi.hose_ok, fi.safety_pin_ok, " +
                        "fi.expiry_valid, fi.body_ok, fi.signage_ok, fi.result_id, fi.action_required, " +
                        "fi.next_due_date, fi.work_order_id, " +
                        "COALESCE(fir.name, 'PASS') as result_name, " +
                        "COALESCE(e.display_name, 'Safety Inspector') as inspector_name " +
                        "FROM fire_inspections fi " +
                        "LEFT JOIN fire_inspection_results fir ON fi.result_id = fir.fire_inspection_result_id " +
                        "LEFT JOIN employees e ON fi.inspector_id = e.employee_id " +
                        "ORDER BY fi.fire_inspection_id DESC";

                return jdbc.query(sql, ROW_MAPPER);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return Collections.emptyList();
    }

    public FireInspection getInspectionById(String id) {
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(id);
                String sql = "SELECT fi.fire_inspection_id, fi.equipment_id, fi.inspected_at, fi.inspector_id, " +
                        "fi.present_flag, fi.access_clear, fi.pressure_ok, fi.hose_ok, fi.safety_pin_ok, " +
                        "fi.expiry_valid, fi.body_ok, fi.signage_ok, fi.result_id, fi.action_required, " +
                        "fi.next_due_date, fi.work_order_id, " +
                        "COALESCE(fir.name, 'PASS') as result_name, " +
                        "COALESCE(e.display_name, 'Safety Inspector') as inspector_name " +
                        "FROM fire_inspections fi " +
                        "LEFT JOIN fire_inspection_results fir ON fi.result_id = fir.fire_inspection_result_id " +
                        "LEFT JOIN employees e ON fi.inspector_id = e.employee_id " +
                        "WHERE fi.fire_inspection_id = :id";
                List<FireInspection> list = jdbc.query(sql, Map.of("id", numId), ROW_MAPPER);
                if (!list.isEmpty()) return list.get(0);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return null;
    }

    public List<FireInspection> getInspectionsByEquipment(String equipmentId) {
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(equipmentId);
                String sql = "SELECT fi.fire_inspection_id, fi.equipment_id, fi.inspected_at, fi.inspector_id, " +
                        "fi.present_flag, fi.access_clear, fi.pressure_ok, fi.hose_ok, fi.safety_pin_ok, " +
                        "fi.expiry_valid, fi.body_ok, fi.signage_ok, fi.result_id, fi.action_required, " +
                        "fi.next_due_date, fi.work_order_id, " +
                        "COALESCE(fir.name, 'PASS') as result_name, " +
                        "COALESCE(e.display_name, 'Safety Inspector') as inspector_name " +
                        "FROM fire_inspections fi " +
                        "LEFT JOIN fire_inspection_results fir ON fi.result_id = fir.fire_inspection_result_id " +
                        "LEFT JOIN employees e ON fi.inspector_id = e.employee_id " +
                        "WHERE fi.equipment_id = :eqId " +
                        "ORDER BY fi.fire_inspection_id DESC";

                return jdbc.query(sql, Map.of("eqId", numId), ROW_MAPPER);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return Collections.emptyList();
    }

    public FireInspection createInspection(FireInspection inspection) {
        if (jdbc != null) {
            try {
                int eqId = EntityIdUtils.parseNumericId(inspection.getEquipmentId());
                try {
                    Integer validId = jdbc.queryForObject("SELECT equipment_id FROM fire_equipment WHERE equipment_id = :id LIMIT 1", Map.of("id", eqId), Integer.class);
                    if (validId != null) eqId = validId;
                    else eqId = 1;
                } catch (Exception e) {
                    eqId = 1;
                }

                int resultId = resolveResultId(inspection.getStatus());
                LocalDate inspDate = inspection.getInspectionDate() != null ? inspection.getInspectionDate() : LocalDate.now();
                String action = inspection.getNotes() != null ? inspection.getNotes() : "فحص دوري معتمد";
                if (action.length() > 250) action = action.substring(0, 247) + "...";

                String sql = "INSERT INTO fire_inspections (equipment_id, inspected_at, inspector_id, present_flag, " +
                        "access_clear, pressure_ok, hose_ok, safety_pin_ok, expiry_valid, body_ok, signage_ok, " +
                        "result_id, action_required, next_due_date, work_order_id) " +
                        "VALUES (:eqId, :inspected_at, 1, 1, 1, 1, 1, 1, 1, 1, 1, :result_id, :action_required, :next_due_date, NULL)";

                MapSqlParameterSource params = new MapSqlParameterSource()
                        .addValue("eqId", eqId)
                        .addValue("inspected_at", Timestamp.valueOf(inspDate.atStartOfDay()))
                        .addValue("result_id", resultId)
                        .addValue("action_required", action)
                        .addValue("next_due_date", Date.valueOf(inspDate.plusMonths(1)));

                KeyHolder keyHolder = new GeneratedKeyHolder();
                jdbc.update(sql, params, keyHolder, new String[]{"fire_inspection_id"});
                Number newKey = keyHolder.getKey();
                int newId = newKey != null ? newKey.intValue() : 100;
                inspection.setId(EntityIdUtils.formatId("INSP", newId));

                // Synchronize equipment status and inspection dates in fire_equipment
                int newEqStatusId = 1; // VALID (مطابقة)
                if ("FAILED".equalsIgnoreCase(inspection.getStatus()) || resultId == 3) {
                    newEqStatusId = 5; // OUT_OF_SERVICE (معيبة / خارج الخدمة)
                } else if ("MAINTENANCE_REQUIRED".equalsIgnoreCase(inspection.getStatus()) || resultId == 2) {
                    newEqStatusId = 3; // ACTION_REQUIRED (تحتاج صيانة)
                } else {
                    newEqStatusId = 1; // VALID (صالحة ومطابقة)
                }

                jdbc.update("UPDATE fire_equipment SET last_inspection_date = :dt, next_inspection_date = :nextDt, status_id = :statusId WHERE equipment_id = :eqId",
                        Map.of("dt", Date.valueOf(inspDate), "nextDt", Date.valueOf(inspDate.plusMonths(1)), "statusId", newEqStatusId, "eqId", eqId));

                return inspection;
            } catch (Exception e) {
                e.printStackTrace();
                throw new RuntimeException("Failed to record inspection: " + e.getMessage(), e);
            }
        }
        return inspection;
    }

    public FireInspection updateInspection(String id, FireInspection updated) {
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(id);
                int resultId = resolveResultId(updated.getStatus());
                String action = updated.getNotes() != null ? updated.getNotes() : "";
                if (action.length() > 250) action = action.substring(0, 247) + "...";
                jdbc.update("UPDATE fire_inspections SET result_id = :res, action_required = :action WHERE fire_inspection_id = :id",
                        Map.of("res", resultId, "action", action, "id", numId));

                // Synchronize equipment status
                Integer eqId = jdbc.queryForObject("SELECT equipment_id FROM fire_inspections WHERE fire_inspection_id = :id", Map.of("id", numId), Integer.class);
                if (eqId != null) {
                    int newEqStatusId = (resultId == 3) ? 5 : (resultId == 2) ? 3 : 1;
                    jdbc.update("UPDATE fire_equipment SET status_id = :statusId WHERE equipment_id = :eqId",
                            Map.of("statusId", newEqStatusId, "eqId", eqId));
                }

                updated.setId(id);
                return updated;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return updated;
    }

    public boolean deleteInspection(String id) {
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(id);
                jdbc.update("DELETE FROM fire_inspections WHERE fire_inspection_id = :numId", Map.of("numId", numId));
                return true;
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        return false;
    }

    public Map<String, Object> getInspectionSummary() {
        List<FireInspection> all = getAllInspections();
        Map<String, Object> summary = new LinkedHashMap<>();

        long passed = all.stream().filter(i -> "PASSED".equalsIgnoreCase(i.getStatus())).count();
        long failed = all.stream().filter(i -> "FAILED".equalsIgnoreCase(i.getStatus())).count();
        long maintenance = all.stream().filter(i -> "MAINTENANCE_REQUIRED".equalsIgnoreCase(i.getStatus())).count();

        Set<String> distinctEquipment = all.stream().map(FireInspection::getEquipmentId).filter(Objects::nonNull).collect(Collectors.toSet());

        summary.put("totalInspections", all.size());
        summary.put("distinctEquipmentInspected", distinctEquipment.size());
        summary.put("passed", passed);
        summary.put("failed", failed);
        summary.put("maintenanceRequired", maintenance);

        return summary;
    }

    private int resolveResultId(String status) {
        if (status == null) return 1;
        String s = status.toUpperCase().trim();
        if (s.contains("FAIL")) return 3;
        if (s.contains("MAINT") || s.contains("ACTION")) return 2;
        return 1;
    }
}
