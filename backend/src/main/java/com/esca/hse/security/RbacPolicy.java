package com.esca.hse.security;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/**
 * Canonical, fail-closed RBAC policy for the HSE platform.
 *
 * <p>The access grades and scopes mirror the approved RBAC matrix shipped with
 * the project. Controllers and the web application consume this policy instead
 * of maintaining independent role lists.</p>
 */
@Component
public class RbacPolicy {

    public enum Module {
        DASHBOARD,
        INCIDENTS,
        PERMITS,
        INSPECTIONS,
        RISKS,
        TRAINING,
        HEALTH,
        HEALTH_AGGREGATE,
        HEALTH_SELF,
        ADMIN,
        AUDIT,
        REPORTS,
        AI_AGENT
    }

    public enum Action { CREATE, READ, UPDATE, DELETE, APPROVE, EXPORT }

    private record RoleAccess(
            String scope,
            String incidents,
            String permits,
            String inspections,
            String risks,
            String training,
            String health,
            String admin,
            boolean approveHighRisk,
            boolean exportReports) {
    }

    private static final Set<String> HUMAN_ROLES = Set.of(
            "SYSTEM_ADMINISTRATOR",
            "HSE_MANAGER",
            "HSE_OFFICER",
            "OCCUPATIONAL_DOCTOR",
            "DEPARTMENT_MANAGER",
            "SHIFT_SUPERVISOR",
            "MAINTENANCE_TECHNICIAN",
            "WORKER",
            "CONTRACTOR",
            "AUDITOR"
    );

    private static final Map<String, String> ROLE_ALIASES = Map.ofEntries(
            Map.entry("ADMIN", "SYSTEM_ADMINISTRATOR"),
            Map.entry("SECTOR_MANAGER", "DEPARTMENT_MANAGER"),
            Map.entry("PRODUCTION_SUPERVISOR", "SHIFT_SUPERVISOR"),
            Map.entry("WAREHOUSE_SUPERVISOR", "SHIFT_SUPERVISOR"),
            Map.entry("MAINTENANCE_ENGINEER", "MAINTENANCE_TECHNICIAN")
    );

    private final Map<String, RoleAccess> roles;

    public RbacPolicy() {
        Map<String, RoleAccess> configured = new LinkedHashMap<>();
        configured.put("SYSTEM_ADMINISTRATOR", role("SITE", "CRUD", "CRUD", "CRUD", "CRUD", "CRUD", "CRUD", "RW", true, true));
        configured.put("HSE_MANAGER", role("SITE", "CRUD", "CRUD", "CRUD", "CRUD", "CRUD", "AGGREGATE_ONLY", "RW", true, true));
        configured.put("HSE_OFFICER", role("ASSIGNED_ZONES", "CRU", "CRU", "CRUD", "CRU", "CRUD", "SELF_FITNESS_ONLY", "NONE", false, true));
        configured.put("OCCUPATIONAL_DOCTOR", role("CLINIC", "C", "NONE", "CR", "NONE", "SELF", "CRUD", "NONE", false, false));
        configured.put("DEPARTMENT_MANAGER", role("DEPARTMENT", "CR", "R", "R", "R", "R", "SELF_FITNESS_ONLY", "NONE", false, true));
        configured.put("SHIFT_SUPERVISOR", role("SHIFT", "CR", "CR", "CR", "NONE", "SELF", "SELF_FITNESS_ONLY", "NONE", false, false));
        configured.put("MAINTENANCE_TECHNICIAN", role("ASSIGNED_WORK", "C", "CR", "CR", "NONE", "SELF", "SELF_FITNESS_ONLY", "NONE", false, false));
        configured.put("WORKER", role("SELF", "C", "CR", "CR", "NONE", "SELF", "SELF_FITNESS_ONLY", "NONE", false, false));
        configured.put("CONTRACTOR", role("ACTIVE_PERMIT", "C", "CR", "CR", "NONE", "SELF", "SELF_FITNESS_ONLY", "NONE", false, false));
        configured.put("AUDITOR", role("SITE_READ_ONLY", "R", "R", "R", "R", "R", "NONE", "R", false, true));
        configured.put("AUTOMATION_SERVICE", role("SERVICE", "R", "R", "R", "R", "R", "NONE", "SERVICE_API", false, false));
        roles = Map.copyOf(configured);
    }

    public boolean isAllowed(String rawRole, Module module, Action action) {
        String role = canonicalRole(rawRole);
        RoleAccess access = roles.get(role);
        if (access == null) return false;

        if (module == Module.DASHBOARD) {
            // PATCH is limited to the notification read-state endpoint by the route classifier.
            return (action == Action.READ || action == Action.UPDATE) && HUMAN_ROLES.contains(role);
        }
        if (module == Module.AI_AGENT) {
            // Reading suggestions and posting a question are user-facing operations.
            return (action == Action.READ || action == Action.CREATE) && HUMAN_ROLES.contains(role);
        }
        if (module == Module.AUDIT) return action == Action.READ && ("SYSTEM_ADMINISTRATOR".equals(role)
                || "HSE_MANAGER".equals(role) || "AUDITOR".equals(role));
        if (module == Module.REPORTS) {
            if (action == Action.EXPORT) return access.exportReports();
            return action == Action.READ && gradeAllows(access.incidents(), Action.READ);
        }
        if (action == Action.APPROVE) return access.approveHighRisk();

        String grade = switch (module) {
            case INCIDENTS -> access.incidents();
            case PERMITS -> access.permits();
            case INSPECTIONS -> access.inspections();
            case RISKS -> access.risks();
            case TRAINING -> access.training();
            case HEALTH -> access.health();
            case ADMIN -> access.admin();
            case HEALTH_AGGREGATE, HEALTH_SELF -> access.health();
            default -> "NONE";
        };

        if (module == Module.HEALTH_AGGREGATE) {
            return action == Action.READ && ("CRUD".equals(grade) || "AGGREGATE_ONLY".equals(grade));
        }
        if (module == Module.HEALTH_SELF) {
            return action == Action.READ && ("CRUD".equals(grade)
                    || "SELF".equals(grade)
                    || "SELF_FITNESS_ONLY".equals(grade));
        }
        if (module == Module.HEALTH && !"CRUD".equals(grade)) {
            // Aggregate/self-only grades must never open the unscoped medical endpoints.
            return false;
        }
        return gradeAllows(grade, action);
    }

    public String canonicalRole(String rawRole) {
        if (rawRole == null) return "";
        String normalized = rawRole.trim().toUpperCase(Locale.ROOT)
                .replace('-', '_')
                .replace(' ', '_');
        if (normalized.startsWith("ROLE_")) normalized = normalized.substring(5);
        return ROLE_ALIASES.getOrDefault(normalized, normalized);
    }

    public Map<String, Object> describe(String rawRole) {
        String role = canonicalRole(rawRole);
        RoleAccess access = roles.get(role);
        if (access == null) {
            return Map.of(
                    "role", role,
                    "dataScope", "NONE",
                    "permissions", List.of(),
                    "approveHighRisk", false,
                    "exportReports", false
            );
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("role", role);
        result.put("dataScope", access.scope());
        result.put("permissions", effectivePermissions(role));
        result.put("approveHighRisk", access.approveHighRisk());
        result.put("exportReports", access.exportReports());
        return result;
    }

    public List<String> effectivePermissions(String rawRole) {
        String role = canonicalRole(rawRole);
        Set<String> permissions = new TreeSet<>();
        for (Module module : Module.values()) {
            for (Action action : Action.values()) {
                if (isAllowed(role, module, action)) {
                    permissions.add(module.name() + ":" + action.name());
                }
            }
        }
        return new ArrayList<>(permissions);
    }

    private static RoleAccess role(
            String scope,
            String incidents,
            String permits,
            String inspections,
            String risks,
            String training,
            String health,
            String admin,
            boolean approveHighRisk,
            boolean exportReports) {
        return new RoleAccess(scope, incidents, permits, inspections, risks, training, health, admin,
                approveHighRisk, exportReports);
    }

    private static boolean gradeAllows(String grade, Action action) {
        if (grade == null || grade.isBlank() || "NONE".equals(grade) || "SERVICE_API".equals(grade)) return false;
        if ("SELF".equals(grade)) return action == Action.READ || action == Action.CREATE;
        if ("RW".equals(grade)) return action == Action.READ || action == Action.CREATE || action == Action.UPDATE;
        if ("AGGREGATE_ONLY".equals(grade) || "SELF_FITNESS_ONLY".equals(grade)) return action == Action.READ;
        return switch (action) {
            case CREATE -> grade.contains("C");
            case READ -> grade.contains("R");
            case UPDATE -> grade.contains("U");
            case DELETE -> grade.contains("D");
            case APPROVE, EXPORT -> false;
        };
    }
}
