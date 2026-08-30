package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import com.esca.hse.security.SecurityUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Dedicated CRUD controller for the Occupational Health module.
 *
 * Mirrors the pattern used by TrainingController (certificates module):
 * all persistence is delegated to PlatformService, which resolves the
 * occupational-health module definition from ModuleCatalog.
 *
 * Routes:
 *   GET    /api/v1/occupational-health/records        - list with optional q/status/limit
 *   GET    /api/v1/occupational-health/records/{id}   - single record
 *   POST   /api/v1/occupational-health/records        - create
 *   PATCH  /api/v1/occupational-health/records/{id}   - partial update
 *   PUT    /api/v1/occupational-health/records/{id}   - full replace
 *   DELETE /api/v1/occupational-health/records/{id}   - delete
 */
@RestController
@RequestMapping("/api/v1/occupational-health/records")
public class OccupationalHealthController {

    private static final String MODULE = "occupational-health";

    private final PlatformService service;

    public OccupationalHealthController(PlatformService service) {
        this.service = service;
    }

    @GetMapping
    public List<Map<String, Object>> list(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "200") int limit) {
        return service.list(MODULE, q, status, limit);
    }

    @GetMapping("/{id}")
    public Map<String, Object> getById(@PathVariable String id) {
        return service.get(MODULE, id);
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> create(@RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole(
                    "HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
        }
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(service.create(MODULE, body));
    }

    @PatchMapping("/{id}")
    public Map<String, Object> patch(
            @PathVariable String id,
            @RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole(
                    "HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
        }
        return service.update(MODULE, id, body);
    }

    @PutMapping("/{id}")
    public Map<String, Object> put(
            @PathVariable String id,
            @RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole(
                    "HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
        }
        return service.update(MODULE, id, body);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole(
                    "HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
        }
        service.delete(MODULE, id);
        return ResponseEntity.noContent().build();
    }
}