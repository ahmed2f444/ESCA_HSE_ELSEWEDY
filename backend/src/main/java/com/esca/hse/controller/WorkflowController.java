package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import com.esca.hse.security.SecurityUtils;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
public class WorkflowController {
    private final PlatformService service;

    public WorkflowController(PlatformService service) { this.service = service; }

    // Permit lifecycle transitions are handled by WorkPermitController.java


    @PatchMapping("/incidents/{id}/close")
    public Map<String, Object> closeIncident(@PathVariable String id, @RequestBody(required = false) Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        return service.transition("incidents", id, "CLOSED", body);
    }

    @PatchMapping("/jsa/{id}/approve")
    public Map<String, Object> approveJsa(@PathVariable String id, @RequestBody(required = false) Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        return service.transition("jsa", id, "APPROVED", body);
    }

    @PatchMapping("/inspections/{id}/complete")
    public Map<String, Object> completeInspection(@PathVariable String id, @RequestBody(required = false) Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        return service.transition("inspections", id, "COMPLETED", body);
    }

    @PatchMapping("/capa/{id}/complete")
    public Map<String, Object> completeCapa(@PathVariable String id, @RequestBody(required = false) Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "PRODUCTION_SUPERVISOR", "SYSTEM_ADMINISTRATOR");
        }
        return service.transition("capa", id, "COMPLETED", body);
    }

    @PatchMapping("/capa/{id}/verify")
    public Map<String, Object> verifyCapa(@PathVariable String id, @RequestBody(required = false) Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        Map<String, Object> values = new java.util.LinkedHashMap<>(body == null ? Map.of() : body);
        values.put("verification_status", "VERIFIED");
        return service.update("capa", id, values);
    }

    @PatchMapping("/notifications/{id}/read")
    public Map<String, Object> readNotification(@PathVariable String id) {
        return service.update("notifications", id, Map.of("status", "READ", "read_at", java.time.LocalDateTime.now()));
    }
}
