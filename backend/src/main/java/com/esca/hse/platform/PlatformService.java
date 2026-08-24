package com.esca.hse.platform;

import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Year;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

@Service
public class PlatformService {
    private final NamedParameterJdbcTemplate jdbc;
    private final ObjectMapper objectMapper;

    public PlatformService(@org.springframework.beans.factory.annotation.Autowired(required = false) NamedParameterJdbcTemplate jdbc, ObjectMapper objectMapper) {
        this.jdbc = jdbc;
        this.objectMapper = objectMapper;
    }

    public List<Map<String, Object>> list(String module, String query, String status, int requestedLimit) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        int limit = Math.max(1, Math.min(requestedLimit, 500));
        List<String> predicates = new ArrayList<>();
        MapSqlParameterSource parameters = new MapSqlParameterSource("limit", limit);
        if (query != null && !query.isBlank()) {
            predicates.add("LOWER(CAST(" + definition.titleColumn() + " AS CHAR)) LIKE :query");
            parameters.addValue("query", "%" + query.trim().toLowerCase(Locale.ROOT) + "%");
        }
        if (status != null && !status.isBlank() && definition.writableColumns().contains("status")) {
            predicates.add("status = :status");
            parameters.addValue("status", status.trim().toUpperCase(Locale.ROOT));
        }
        String where = predicates.isEmpty() ? "" : " WHERE " + String.join(" AND ", predicates);
        String sql = "SELECT * FROM " + definition.table() + where + " ORDER BY created_at DESC LIMIT :limit";
        return jdbc.queryForList(sql, parameters);
    }

    public Map<String, Object> get(String module, String id) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT * FROM " + definition.table() + " WHERE " + definition.idColumn() + " = :id",
                Map.of("id", id));
        if (rows.isEmpty()) {
            throw new ResourceNotFoundException(module + " record not found");
        }
        return rows.get(0);
    }

    @Transactional
    public Map<String, Object> create(String module, Map<String, Object> request) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        Map<String, Object> values = sanitize(definition, request);
        normalize(module, values, true);
        String id = text(request.get(definition.idColumn()));
        if (id == null) {
            id = generateId(definition.idPrefix());
        }
        values.put(definition.idColumn(), id);
        if (values.size() == 1) {
            throw new IllegalArgumentException("At least one writable field is required");
        }
        String columns = String.join(", ", values.keySet());
        String placeholders = ":" + String.join(", :", values.keySet());
        try {
            jdbc.update("INSERT INTO " + definition.table() + " (" + columns + ") VALUES (" + placeholders + ")", values);
        } catch (DuplicateKeyException ex) {
            throw new IllegalArgumentException("A record with the same identifier already exists");
        }
        audit("CREATE", module, id, values, null);
        return get(module, id);
    }

    @Transactional
    public Map<String, Object> update(String module, String id, Map<String, Object> request) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        get(module, id);
        Map<String, Object> values = sanitize(definition, request);
        normalize(module, values, false);
        if (values.isEmpty()) {
            throw new IllegalArgumentException("No writable fields were supplied");
        }
        List<String> assignments = values.keySet().stream().map(column -> column + " = :" + column).toList();
        values.put("_id", id);
        jdbc.update("UPDATE " + definition.table() + " SET " + String.join(", ", assignments)
                + " WHERE " + definition.idColumn() + " = :_id", values);
        values.remove("_id");
        audit("UPDATE", module, id, values, null);
        return get(module, id);
    }

    @Transactional
    public void delete(String module, String id) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        int changed = jdbc.update("DELETE FROM " + definition.table() + " WHERE " + definition.idColumn() + " = :id", Map.of("id", id));
        if (changed == 0) {
            throw new ResourceNotFoundException(module + " record not found");
        }
        audit("DELETE", module, id, Map.of(), null);
    }

    @Transactional
    public Map<String, Object> transition(String module, String id, String status, Map<String, Object> extra) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        if (!definition.writableColumns().contains("status")) {
            throw new IllegalArgumentException("This module does not support status transitions");
        }
        Map<String, Object> changes = new LinkedHashMap<>(extra == null ? Map.of() : extra);
        changes.put("status", status);
        if (module.equals("permits") && status.equals("CLOSED")) {
            changes.put("actual_close_at", LocalDateTime.now());
        }
        if (module.equals("incidents") && status.equals("CLOSED")) {
            changes.put("closed_at", LocalDateTime.now());
        }
        if (module.equals("inspections") && status.equals("COMPLETED")) {
            changes.put("completed_at", LocalDateTime.now());
        }
        if (module.equals("capa") && status.equals("COMPLETED")) {
            changes.put("completion_date", LocalDate.now());
        }
        return update(module, id, changes);
    }

    public long count(String module) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        Long value = jdbc.getJdbcTemplate().queryForObject("SELECT COUNT(*) FROM " + definition.table(), Long.class);
        return value == null ? 0 : value;
    }

    public long countWhere(String module, String column, Object value) {
        ModuleDefinition definition = ModuleCatalog.get(module);
        if (!definition.writableColumns().contains(column)) {
            throw new IllegalArgumentException("Unsupported filter column");
        }
        Long result = jdbc.queryForObject("SELECT COUNT(*) FROM " + definition.table() + " WHERE " + column + " = :value", Map.of("value", value), Long.class);
        return result == null ? 0 : result;
    }

    @Transactional
    public String audit(String action, String entityType, String entityId, Object details, String correlationId) {
        String auditId = "AUD-" + UUID.randomUUID().toString().replace("-", "").substring(0, 20).toUpperCase(Locale.ROOT);
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String actor = authentication != null && authentication.isAuthenticated() ? authentication.getName() : "local-demo";
        String json;
        try {
            json = objectMapper.writeValueAsString(details == null ? Map.of() : details);
        } catch (JacksonException ex) {
            json = "{}";
        }
        jdbc.update("INSERT INTO audit_log (audit_id, actor_type, actor_id, action, entity_type, entity_id, details_json, correlation_id) "
                        + "VALUES (:audit_id, :actor_type, :actor_id, :action, :entity_type, :entity_id, :details_json, :correlation_id)",
                new MapSqlParameterSource()
                        .addValue("audit_id", auditId)
                        .addValue("actor_type", actor.startsWith("service:") ? "SERVICE" : "USER")
                        .addValue("actor_id", actor)
                        .addValue("action", action)
                        .addValue("entity_type", entityType.toUpperCase(Locale.ROOT))
                        .addValue("entity_id", entityId)
                        .addValue("details_json", json)
                        .addValue("correlation_id", correlationId));
        return auditId;
    }

    public List<Map<String, Object>> auditLog(int requestedLimit) {
        int limit = Math.max(1, Math.min(requestedLimit, 500));
        return jdbc.queryForList("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT :limit", Map.of("limit", limit));
    }

    private Map<String, Object> sanitize(ModuleDefinition definition, Map<String, Object> request) {
        Map<String, Object> values = new LinkedHashMap<>();
        for (String column : definition.writableColumns()) {
            Object value = request.get(column);
            if (value == null) {
                value = request.get(toCamel(column));
            }
            if (value != null) {
                values.put(column, value instanceof String string && string.isBlank() ? null : value);
            }
        }
        return values;
    }

    private void normalize(String module, Map<String, Object> values, boolean creating) {
        if (module.equals("risks")) {
            Integer likelihood = integer(values.get("likelihood"));
            Integer severity = integer(values.get("severity"));
            if (likelihood != null && severity != null) {
                int score = likelihood * severity;
                values.put("inherent_score", score);
                values.put("risk_level", riskLevel(score));
            }
            Integer residualLikelihood = integer(values.get("residual_likelihood"));
            Integer residualSeverity = integer(values.get("residual_severity"));
            if (residualLikelihood != null && residualSeverity != null) {
                values.put("residual_score", residualLikelihood * residualSeverity);
            }
        }
        if (creating) {
            Map<String, String> defaults = Map.ofEntries(
                    Map.entry("incidents", "OPEN"), Map.entry("jsa", "DRAFT"), Map.entry("permits", "REQUESTED"),
                    Map.entry("risks", "OPEN"), Map.entry("inspections", "SCHEDULED"), Map.entry("findings", "OPEN"),
                    Map.entry("capa", "OPEN"), Map.entry("hazmat", "ACTIVE"), Map.entry("occupational-health", "COMPLETED"),
                    Map.entry("certificates", "VALID"), Map.entry("notifications", "UNREAD"));
            if (defaults.containsKey(module)) {
                values.putIfAbsent("status", defaults.get(module));
            }
        }
    }

    private String generateId(String prefix) {
        return prefix + "-" + Year.now().getValue() + "-" + UUID.randomUUID().toString().replace("-", "").substring(0, 8).toUpperCase(Locale.ROOT);
    }

    private String riskLevel(int score) {
        if (score >= 20) return "CRITICAL";
        if (score >= 12) return "HIGH";
        if (score >= 6) return "MEDIUM";
        return "LOW";
    }

    private Integer integer(Object value) {
        if (value instanceof Number number) return number.intValue();
        if (value instanceof String string && !string.isBlank()) return Integer.parseInt(string);
        return null;
    }

    private String text(Object value) {
        return value instanceof String string && !string.isBlank() ? string.trim() : null;
    }

    private String toCamel(String value) {
        StringBuilder result = new StringBuilder();
        boolean upper = false;
        for (char c : value.toCharArray()) {
            if (c == '_') upper = true;
            else if (upper) { result.append(Character.toUpperCase(c)); upper = false; }
            else result.append(c);
        }
        return result.toString();
    }
}
