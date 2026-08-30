package com.esca.hse.platform;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

public final class ModuleCatalog {
    private static final Map<String, ModuleDefinition> MODULES = new LinkedHashMap<>();

    static {
        add("departments", "departments", "department_id", "DEP", "department_name",
                "department_code", "department_name", "manager_employee_id", "hse_contact_id", "location", "active");
        add("zones", "zones", "zone_id", "ZON", "zone_name",
                "zone_code", "zone_name", "department_id", "risk_level", "restricted_access", "active");
        add("employees", "employees", "employee_id", "EMP", "full_name",
                "employee_code", "full_name", "email", "phone", "job_title", "department_id", "manager_id", "employment_type", "status", "hire_date");
        add("incidents", "incidents", "incident_id", "INC", "title",
                "incident_type", "title", "description", "department_id", "zone_id", "reported_by", "occurred_at", "severity", "status", "immediate_action", "root_cause", "lost_time_days", "closed_at");
        add("jsa", "jsa", "jsa_id", "JSA", "title",
                "title", "activity", "department_id", "zone_id", "prepared_by", "hazards", "controls", "required_ppe", "risk_level", "status", "approved_by", "approved_at", "review_date");
        add("permits", "permits", "permit_id", "PTW", "work_description",
                "permit_type", "department_id", "zone_id", "work_description", "requester_id", "issuer_id", "executor_type", "executor_name", "start_at", "expiry_at", "risk_level", "jsa_id", "status", "suspended_reason", "actual_close_at");
        add("risks", "risk_register", "risk_id", "RSK", "hazard",
                "department_id", "zone_id", "hazard", "activity", "likelihood", "severity", "inherent_score", "risk_level", "controls", "residual_likelihood", "residual_severity", "residual_score", "owner_id", "status", "last_reviewed_at", "next_review_date");
        add("inspections", "inspections", "inspection_id", "INS", "title",
                "inspection_type", "title", "department_id", "zone_id", "inspector_id", "scheduled_at", "completed_at", "score", "status", "notes");
        add("findings", "findings", "finding_id", "FND", "description",
                "inspection_id", "category", "description", "severity", "status", "photo_url");
        add("capa", "capa", "capa_id", "CAPA", "title",
                "incident_id", "finding_id", "title", "action_type", "priority", "assigned_to", "due_date", "status", "completion_date", "verification_status", "verified_by", "last_reminder_at");
        add("hazmat", "chemicals", "chemical_id", "CHM", "chemical_name",
                "chemical_name", "cas_number", "department_id", "zone_id", "quantity", "unit", "hazard_class", "storage_requirements", "sds_url", "expiry_date", "status");
        add("occupational-health", "health_exams", "exam_id", "HEX", "protocol_id",
                "employee_id", "protocol_id", "scheduled_date", "completed_date",
                "fitness_result_id", "restriction_summary", "next_due_date",
                "status_id", "clinician_alias", "confidentiality_level_id", "days_overdue");
        add("training-courses", "training_courses", "course_id", "CRS", "course_name",
                "course_code", "course_name", "validity_months", "provider", "mandatory", "active");
        add("certificates", "certificates", "certificate_id", "CERT", "certificate_number",
                "employee_id", "course_id", "issue_date", "expiry_date", "certificate_number", "provider", "status", "last_reminder_at");
        add("notifications", "notifications", "notification_id", "NTF", "title",
                "recipient_user_id", "recipient_employee_id", "type", "title", "message", "entity_type", "entity_id", "status", "read_at");
        add("sensor-events", "sensor_events", "sensor_event_id", "SNS", "sensor_type",
                "sensor_type", "zone_id", "reading_value", "reading_unit", "threshold_value", "alert_level", "source", "recorded_at");
        add("automation-rules", "automation_rules", "rule_id", "AUT", "rule_name",
                "rule_name", "entity_type", "trigger_type", "schedule_cron", "conditions_json", "action_type", "action_endpoint", "active");
    }

    private ModuleCatalog() {}

    private static void add(String key, String table, String id, String prefix, String title, String... columns) {
        MODULES.put(key, new ModuleDefinition(key, table, id, prefix, title, Set.of(columns)));
    }

    public static ModuleDefinition get(String key) {
        ModuleDefinition definition = MODULES.get(key);
        if (definition == null) {
            throw new IllegalArgumentException("Unknown HSE module: " + key);
        }
        return definition;
    }

    public static Map<String, ModuleDefinition> all() {
        return Map.copyOf(MODULES);
    }
}
