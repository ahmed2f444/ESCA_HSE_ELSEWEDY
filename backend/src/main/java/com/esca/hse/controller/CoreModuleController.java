package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import com.esca.hse.security.SecurityUtils;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/raw/{module:incidents|permits|jsa|risks|inspections|findings|capa|hazmat|occupational-health|notifications|sensor-events|automation-rules}")

public class CoreModuleController {
    private final PlatformService service;

    public CoreModuleController(PlatformService service) {
        this.service = service;
    }

    @GetMapping
    public List<Map<String, Object>> list(
            @PathVariable String module,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "100") int limit) {
        return service.list(module, q, status, limit);
    }

    @GetMapping("/{id}")
    public Map<String, Object> get(@PathVariable String module, @PathVariable String id) {
        return service.get(module, id);
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> create(@PathVariable String module, @RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            if ("automation-rules".equals(module)) {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
            } else if ("occupational-health".equals(module)) {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
            }
        }
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(module, body));
    }

    @PutMapping("/{id}")
    public Map<String, Object> replace(@PathVariable String module, @PathVariable String id, @RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            if ("automation-rules".equals(module)) {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
            } else if ("occupational-health".equals(module)) {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
            } else {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR", "PRODUCTION_SUPERVISOR");
            }
        }
        return service.update(module, id, body);
    }

    @PatchMapping("/{id}")
    public Map<String, Object> update(@PathVariable String module, @PathVariable String id, @RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            if ("automation-rules".equals(module)) {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
            } else if ("occupational-health".equals(module)) {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR");
            } else {
                SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR", "PRODUCTION_SUPERVISOR");
            }
        }
        return service.update(module, id, body);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String module, @PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        service.delete(module, id);
        return ResponseEntity.noContent().build();
    }
}
