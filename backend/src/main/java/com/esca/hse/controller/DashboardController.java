package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1")
public class DashboardController {
    private final PlatformService service;
    private final NamedParameterJdbcTemplate jdbc;

    public DashboardController(PlatformService service, @org.springframework.beans.factory.annotation.Autowired(required = false) NamedParameterJdbcTemplate jdbc) {
        this.service = service;
        this.jdbc = jdbc;
    }

    @GetMapping("/dashboard")
    public Map<String, Object> dashboard() {
        Map<String, Object> kpis = new LinkedHashMap<>();
        kpis.put("openIncidents", service.countWhere("incidents", "status", "OPEN"));
        kpis.put("activePermits", service.countWhere("permits", "status", "ACTIVE"));
        kpis.put("openCapa", service.countWhere("capa", "status", "OPEN"));
        kpis.put("openRisks", service.countWhere("risks", "status", "OPEN"));
        kpis.put("scheduledInspections", service.countWhere("inspections", "status", "SCHEDULED"));
        kpis.put("employees", service.count("employees"));
        kpis.put("chemicals", service.count("hazmat"));
        kpis.put("certificates", service.count("certificates"));

        List<Map<String, Object>> priorities = jdbc.queryForList(
                "SELECT 'PERMIT' entity_type, permit_id entity_id, work_description title, expiry_at due_at, risk_level priority "
                        + "FROM permits WHERE status = 'ACTIVE' AND expiry_at < CURRENT_TIMESTAMP "
                        + "UNION ALL SELECT 'CAPA', capa_id, title, due_date, priority FROM capa WHERE status IN ('OPEN','IN_PROGRESS') AND due_date < CURRENT_DATE "
                        + "ORDER BY due_at LIMIT 12", Map.of());
        return Map.of("status", "ready", "kpis", kpis, "priorities", priorities);
    }

    @GetMapping("/reports/summary")
    public Map<String, Object> reportSummary() {
        return Map.of(
                "incidentsBySeverity", jdbc.queryForList("SELECT severity label, COUNT(*) total FROM incidents GROUP BY severity ORDER BY total DESC", Map.of()),
                "permitsByStatus", jdbc.queryForList("SELECT status label, COUNT(*) total FROM permits GROUP BY status ORDER BY total DESC", Map.of()),
                "risksByLevel", jdbc.queryForList("SELECT risk_level label, COUNT(*) total FROM risk_register GROUP BY risk_level ORDER BY total DESC", Map.of()),
                "capaByStatus", jdbc.queryForList("SELECT status label, COUNT(*) total FROM capa GROUP BY status ORDER BY total DESC", Map.of()));
    }

    @GetMapping("/audit")
    public List<Map<String, Object>> audit(@RequestParam(defaultValue = "100") int limit) { return service.auditLog(limit); }

    @GetMapping("/field/tasks")
    public Map<String, Object> fieldTasks() {
        return Map.of(
                "permits", service.list("permits", null, null, 20),
                "inspections", service.list("inspections", null, null, 20),
                "capa", service.list("capa", null, null, 20),
                "notifications", service.list("notifications", null, "UNREAD", 20));
    }
}
