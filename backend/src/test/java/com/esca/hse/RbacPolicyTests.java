package com.esca.hse;

import com.esca.hse.security.RbacPolicy;
import com.esca.hse.security.RbacPolicy.Action;
import com.esca.hse.security.RbacPolicy.Module;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class RbacPolicyTests {
    private final RbacPolicy policy = new RbacPolicy();

    @Test
    void hseManagerHasSiteOperationsButOnlyAggregateMedicalAccess() {
        assertThat(policy.isAllowed("HSE_MANAGER", Module.INCIDENTS, Action.DELETE)).isTrue();
        assertThat(policy.isAllowed("HSE_MANAGER", Module.PERMITS, Action.APPROVE)).isTrue();
        assertThat(policy.isAllowed("HSE_MANAGER", Module.HEALTH_AGGREGATE, Action.READ)).isTrue();
        assertThat(policy.isAllowed("HSE_MANAGER", Module.HEALTH_SELF, Action.READ)).isFalse();
        assertThat(policy.isAllowed("HSE_MANAGER", Module.HEALTH, Action.READ)).isFalse();
    }

    @Test
    void auditorIsStrictlyReadOnlyAndCannotSeeMedicalRecords() {
        assertThat(policy.isAllowed("AUDITOR", Module.AUDIT, Action.READ)).isTrue();
        assertThat(policy.isAllowed("AUDITOR", Module.ADMIN, Action.READ)).isTrue();
        assertThat(policy.isAllowed("AUDITOR", Module.ADMIN, Action.UPDATE)).isFalse();
        assertThat(policy.isAllowed("AUDITOR", Module.INCIDENTS, Action.CREATE)).isFalse();
        assertThat(policy.isAllowed("AUDITOR", Module.HEALTH_AGGREGATE, Action.READ)).isFalse();
    }

    @Test
    void workerCanReportAndUseAssignedOperationalFlowsOnly() {
        assertThat(policy.isAllowed("WORKER", Module.INCIDENTS, Action.CREATE)).isTrue();
        assertThat(policy.isAllowed("WORKER", Module.INCIDENTS, Action.READ)).isFalse();
        assertThat(policy.isAllowed("WORKER", Module.PERMITS, Action.READ)).isTrue();
        assertThat(policy.isAllowed("WORKER", Module.PERMITS, Action.APPROVE)).isFalse();
        assertThat(policy.isAllowed("WORKER", Module.ADMIN, Action.READ)).isFalse();
        assertThat(policy.isAllowed("WORKER", Module.HEALTH_SELF, Action.READ)).isTrue();
        assertThat(policy.isAllowed("WORKER", Module.HEALTH_AGGREGATE, Action.READ)).isFalse();
        assertThat(policy.isAllowed("WORKER", Module.DASHBOARD, Action.UPDATE)).isTrue();
        assertThat(policy.isAllowed("WORKER", Module.AI_AGENT, Action.CREATE)).isTrue();
    }

    @Test
    void occupationalDoctorOwnsFullMedicalRecordsButNotPermitAdministration() {
        assertThat(policy.isAllowed("OCCUPATIONAL_DOCTOR", Module.HEALTH, Action.CREATE)).isTrue();
        assertThat(policy.isAllowed("OCCUPATIONAL_DOCTOR", Module.HEALTH, Action.DELETE)).isTrue();
        assertThat(policy.isAllowed("OCCUPATIONAL_DOCTOR", Module.PERMITS, Action.READ)).isFalse();
    }

    @Test
    void legacyRoleNamesResolveToCanonicalRoles() {
        assertThat(policy.canonicalRole("ROLE_PRODUCTION_SUPERVISOR")).isEqualTo("SHIFT_SUPERVISOR");
        assertThat(policy.canonicalRole("maintenance engineer")).isEqualTo("MAINTENANCE_TECHNICIAN");
        assertThat(policy.canonicalRole("ADMIN")).isEqualTo("SYSTEM_ADMINISTRATOR");
    }

    @Test
    void unknownRolesAndUnknownPrivilegesFailClosed() {
        assertThat(policy.isAllowed("UNKNOWN", Module.DASHBOARD, Action.READ)).isFalse();
        assertThat(policy.describe("UNKNOWN").get("permissions")).isEqualTo(List.of());
    }

    @Test
    void effectivePermissionsAreDeterministicAndExposeDataScope() {
        List<String> permissions = policy.effectivePermissions("DEPARTMENT_MANAGER");
        assertThat(permissions).isSorted();
        assertThat(permissions).contains("INCIDENTS:CREATE", "INCIDENTS:READ", "REPORTS:EXPORT");
        assertThat(policy.describe("DEPARTMENT_MANAGER").get("dataScope")).isEqualTo("DEPARTMENT");
    }
}
