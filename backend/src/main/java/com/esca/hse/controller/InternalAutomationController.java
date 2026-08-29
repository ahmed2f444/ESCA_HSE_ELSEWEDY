package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import com.esca.hse.platform.ResourceNotFoundException;
import com.esca.hse.security.JwtService;
import tools.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;

@RestController
public class InternalAutomationController {
    private static final Pattern EVENT_ID = Pattern.compile("^evt_[0-9a-f]{32}$");
    private static final Pattern IDEMPOTENCY_KEY = Pattern.compile("^hse-automation:v1:[0-9a-f]{64}$");
    private static final Set<String> BODY_FIELDS = Set.of("schema_version", "event_id", "idempotency_key", "rule_id", "entity_type", "entity_id", "alert_code", "action", "evaluated_at_utc", "business_date", "payload");
    private static final Map<String, RuleContract> RULES = Map.of(
            "AUT-001", new RuleContract("PERMIT", "FLAG_OVERDUE_PERMIT", "permits", Set.of("permit_id", "expiry_at", "status", "minutes_overdue", "department_id", "zone_id", "requester_id", "issuer_id", "risk_level")),
            "AUT-002", new RuleContract("CERTIFICATE", "CREATE_TRAINING_REMINDER", "certificates", Set.of("certificate_id", "expiry_date", "status", "days_to_expiry", "employee_id", "manager_id", "course_id")),
            "AUT-003", new RuleContract("CAPA", "CREATE_CAPA_ESCALATION", "capa", Set.of("capa_id", "due_date", "status", "days_overdue", "escalation_day", "incident_id", "finding_id", "assigned_to", "priority")),
            "AUT-004", new RuleContract("RISK", "FLAG_RISK_FOR_REVIEW", "risks", Set.of("risk_id", "inherent_score", "status", "department_id", "zone_id", "owner_id", "risk_level", "residual_score", "last_reviewed_at", "next_review_date", "days_since_review")));

    private final JwtService jwtService;
    private final PlatformService platformService;
    private final NamedParameterJdbcTemplate jdbc;
    private final ObjectMapper objectMapper;
    private final String configuredClientId;
    private final String configuredClientSecret;
    private final long tokenTtlSeconds;

    public InternalAutomationController(JwtService jwtService, PlatformService platformService,
            @org.springframework.beans.factory.annotation.Autowired(required = false) NamedParameterJdbcTemplate jdbc,
            @org.springframework.beans.factory.annotation.Autowired(required = false) ObjectMapper objectMapper,
            @Value("${app.automation.client-id}") String configuredClientId,
            @Value("${app.automation.client-secret}") String configuredClientSecret,
            @Value("${app.automation.token-ttl-seconds:900}") long tokenTtlSeconds) {
        this.jwtService = jwtService;
        this.platformService = platformService;
        this.jdbc = jdbc;
        this.objectMapper = objectMapper != null ? objectMapper : new ObjectMapper();
        this.configuredClientId = configuredClientId;
        this.configuredClientSecret = configuredClientSecret;
        this.tokenTtlSeconds = tokenTtlSeconds;
    }

    @RequestMapping(path = "/api/v1/internal/auth/service-token", method = RequestMethod.POST)
    public ResponseEntity<Map<String, Object>> token(@RequestBody Map<String, String> request) {
        if (!safeEquals(configuredClientId, request.get("client_id")) || !safeEquals(configuredClientSecret, request.get("client_secret"))) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(Map.of("code", "INVALID_SERVICE_CREDENTIALS", "message", "Service authentication failed"));
        }
        return ResponseEntity.ok().header("Cache-Control", "no-store").body(Map.of(
                "access_token", jwtService.serviceToken(configuredClientId, "automation:write", tokenTtlSeconds),
                "token_type", "Bearer", "expires_in", tokenTtlSeconds, "scope", "automation:write"));
    }

    @Transactional
    @RequestMapping(path = "/api/v1/internal/automation/actions", method = RequestMethod.POST)
    public ResponseEntity<Map<String, Object>> action(
            @RequestHeader("Idempotency-Key") String idempotencyHeader,
            @RequestHeader("X-Correlation-ID") String correlationHeader,
            @RequestHeader("X-Event-Schema-Version") String versionHeader,
            @RequestBody Map<String, Object> event) {
        validateEnvelope(event, idempotencyHeader, correlationHeader, versionHeader);
        String eventId = text(event, "event_id");
        String key = text(event, "idempotency_key");
        List<Map<String, Object>> previous = jdbc.queryForList("SELECT * FROM automation_actions WHERE idempotency_key = :key", Map.of("key", key));
        if (!previous.isEmpty()) return ResponseEntity.ok(result("DUPLICATE", previous.get(0)));

        String ruleId = text(event, "rule_id");
        RuleContract contract = RULES.get(ruleId);
        String entityId = text(event, "entity_id");
        Map<String, Object> authoritative;
        try {
            authoritative = platformService.get(contract.module(), entityId);
        } catch (ResourceNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("code", "ENTITY_NOT_FOUND", "message", "Automation target was not found"));
        }
        if (!stillApplicable(ruleId, authoritative, event)) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("status", "NOT_APPLICABLE", "event_id", eventId, "error_code", "ENTITY_STATE_CHANGED"));
        }

        String actionId = identifier("ACT");
        NotificationContent notification = notificationFor(ruleId, authoritative, entityId);
        Map<String, Object> details = Map.of("event_id", eventId, "rule_id", ruleId, "outcome", "APPLIED");
        String auditId = platformService.audit("AUTOMATION_ACTION", text(event, "entity_type"), entityId, details, correlationHeader);
        
        jdbc.update("INSERT INTO notifications (notification_id, recipient_employee_id, type, title, message, entity_type, entity_id, status) "
                        + "VALUES (:notif_id, :recipient_employee_id, :type, :title, :message, :entity_type, :entity_id, 'UNREAD')",
                new MapSqlParameterSource()
                        .addValue("notif_id", identifier("NTF"))
                        .addValue("recipient_employee_id", notification.recipientEmployeeId())
                        .addValue("type", notification.type())
                        .addValue("title", notification.title())
                        .addValue("message", notification.message())
                        .addValue("entity_type", text(event, "entity_type"))
                        .addValue("entity_id", entityId));

        Instant processed = Instant.now();
        String payloadJson = "{}";
        try {
            payloadJson = objectMapper.writeValueAsString(event.get("payload"));
        } catch (Exception ignored) {}

        jdbc.update("INSERT INTO automation_actions (action_record_id, event_id, idempotency_key, rule_id, entity_type, entity_id, action, alert_code, status, payload_json, processed_at_utc, audit_id) "
                        + "VALUES (:action_id, :event_id, :key, :rule_id, :entity_type, :entity_id, :action, :alert_code, 'APPLIED', :payload, :processed_at, :audit_id)",
                new MapSqlParameterSource()
                        .addValue("action_id", actionId)
                        .addValue("event_id", eventId)
                        .addValue("key", key)
                        .addValue("rule_id", ruleId)
                        .addValue("entity_type", text(event, "entity_type"))
                        .addValue("entity_id", entityId)
                        .addValue("action", text(event, "action"))
                        .addValue("alert_code", text(event, "alert_code"))
                        .addValue("payload", payloadJson)
                        .addValue("processed_at", java.sql.Timestamp.from(processed))
                        .addValue("audit_id", auditId));

        if ("AUT-002".equals(ruleId) && "CERTIFICATE_EXPIRED".equals(text(event, "alert_code"))) {
            try {
                jdbc.update("UPDATE certificates SET status = 'EXPIRED' WHERE certificate_id = :id", Map.of("id", entityId));
            } catch (Exception ignored) {}
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", "APPLIED");
        response.put("event_id", eventId);
        response.put("action_record_id", actionId);
        response.put("audit_id", auditId);
        response.put("processed_at_utc", processed.toString());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    private void validateEnvelope(Map<String, Object> event, String keyHeader, String correlationHeader, String versionHeader) {
        if (!event.keySet().equals(BODY_FIELDS)) throw new IllegalArgumentException("Automation event fields are invalid");
        String version = text(event, "schema_version");
        String eventId = text(event, "event_id");
        String key = text(event, "idempotency_key");
        if (!"1.0".equals(version) || !version.equals(versionHeader)) throw new IllegalArgumentException("Automation schema version is invalid");
        if (!EVENT_ID.matcher(eventId).matches() || !eventId.equals(correlationHeader)) throw new IllegalArgumentException("Automation event ID is invalid");
        if (!IDEMPOTENCY_KEY.matcher(key).matches() || !key.equals(keyHeader)) throw new IllegalArgumentException("Automation idempotency key is invalid");
        RuleContract contract = RULES.get(text(event, "rule_id"));
        if (contract == null || !contract.entityType().equals(text(event, "entity_type")) || !contract.action().equals(text(event, "action"))) {
            throw new IllegalArgumentException("Automation rule contract is invalid");
        }
        if (!(event.get("payload") instanceof Map<?, ?> payload) || !contract.payloadFields().containsAll(payload.keySet().stream().map(String::valueOf).toList())) {
            throw new IllegalArgumentException("Automation payload contains unsupported fields");
        }
        try {
            OffsetDateTime.parse(text(event, "evaluated_at_utc"));
            LocalDate.parse(text(event, "business_date"));
        } catch (DateTimeParseException ex) {
            throw new IllegalArgumentException("Automation timestamps are invalid");
        }
    }

    private boolean stillApplicable(String ruleId, Map<String, Object> entity, Map<String, Object> event) {
        String status = String.valueOf(entity.getOrDefault("status", ""));
        LocalDate businessDate = LocalDate.parse(text(event, "business_date"));
        return switch (ruleId) {
            case "AUT-001" -> Set.of("ACTIVE", "APPROVED").contains(status.toUpperCase(Locale.ROOT));
            case "AUT-002" -> !Set.of("REVOKED", "CANCELLED").contains(status.toUpperCase(Locale.ROOT)) && date(entity.get("expiry_date")).isBefore(businessDate.plusDays(365));
            case "AUT-003" -> Set.of("OPEN", "IN_PROGRESS").contains(status.toUpperCase(Locale.ROOT)) && date(entity.get("due_date")).isBefore(businessDate.plusDays(1));
            case "AUT-004" -> Set.of("OPEN", "ACTIVE").contains(status.toUpperCase(Locale.ROOT)) && number(entity.get("inherent_score")) >= 15;
            default -> false;
        };
    }

    private Map<String, Object> result(String status, Map<String, Object> row) {
        Object processed = row.get("processed_at_utc");
        String timestamp = processed instanceof java.sql.Timestamp value ? value.toInstant().toString() : (processed != null ? String.valueOf(processed) : Instant.now().toString());
        String eventId = row.get("event_id") != null ? String.valueOf(row.get("event_id")) : "";
        String actionRecordId = row.get("action_record_id") != null ? String.valueOf(row.get("action_record_id")) : identifier("ACT");
        String auditId = row.get("audit_id") != null ? String.valueOf(row.get("audit_id")) : "1";
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("status", status);
        map.put("event_id", eventId);
        map.put("action_record_id", actionRecordId);
        map.put("audit_id", auditId);
        map.put("processed_at_utc", timestamp);
        return map;
    }

    private NotificationContent notificationFor(String ruleId, Map<String, Object> entity, String entityId) {
        return switch (ruleId) {
            case "AUT-001" -> new NotificationContent(
                    "AUTOMATION_PERMIT_OVERDUE",
                    "تصريح عمل متأخر",
                    "التصريح " + entityId + " تجاوز موعد انتهائه ويحتاج إلى مراجعة.",
                    firstText(entity.get("issuer_id"), entity.get("requester_id")));
            case "AUT-002" -> new NotificationContent(
                    "AUTOMATION_CERTIFICATE_EXPIRY",
                    "تنبيه اعتماد تدريبي",
                    "الاعتماد " + entityId + " منتهي أو يقترب من الانتهاء.",
                    firstText(entity.get("employee_id")));
            case "AUT-003" -> new NotificationContent(
                    "AUTOMATION_CAPA_OVERDUE",
                    "إجراء تصحيحي متأخر",
                    "الإجراء التصحيحي " + entityId + " متأخر ويحتاج إلى تصعيد.",
                    firstText(entity.get("assigned_to")));
            default -> new NotificationContent(
                    "AUTOMATION_RISK_REVIEW",
                    "مراجعة خطر مرتفع",
                    "الخطر " + entityId + " مرتفع ويحتاج إلى مراجعة محدثة.",
                    firstText(entity.get("owner_id")));
        };
    }

    private String firstText(Object... values) {
        for (Object value : values) {
            if (value != null && !String.valueOf(value).isBlank()) return String.valueOf(value);
        }
        return null;
    }

    private LocalDate date(Object value) {
        if (value instanceof java.sql.Date sqlDate) return sqlDate.toLocalDate();
        if (value instanceof LocalDate localDate) return localDate;
        return LocalDate.parse(String.valueOf(value));
    }

    private int number(Object value) { return value instanceof Number number ? number.intValue() : Integer.parseInt(String.valueOf(value)); }
    private String text(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (!(value instanceof String string) || string.isBlank() || string.length() > 512) throw new IllegalArgumentException("Automation field is invalid: " + key);
        return string;
    }
    private String identifier(String prefix) { return prefix + "-" + UUID.randomUUID().toString().replace("-", "").substring(0, 20).toUpperCase(Locale.ROOT); }
    private boolean safeEquals(String expected, String supplied) {
        byte[] left = expected.getBytes(StandardCharsets.UTF_8);
        byte[] right = supplied == null ? new byte[0] : supplied.getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(left, right);
    }
    private record NotificationContent(String type, String title, String message, String recipientEmployeeId) {}
    private record RuleContract(String entityType, String action, String module, Set<String> payloadFields) {}
}
