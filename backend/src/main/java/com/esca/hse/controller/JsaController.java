package com.esca.hse.controller;

import com.esca.hse.security.SecurityUtils;
import com.esca.hse.service.JsaService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * Dedicated REST Controller for Job Safety Analysis (JSA) operations.
 * Connects directly to the database layer via JsaService.
 */
@RestController
@RequestMapping({"/api/v1/jsa", "/api/jsa", "/jsa"})
public class JsaController {

    private final JsaService jsaService;

    public JsaController(JsaService jsaService) {
        this.jsaService = jsaService;
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStats() {
        return ResponseEntity.ok(jsaService.getJsaStats());
    }

    @GetMapping("/available-permits")
    public ResponseEntity<List<Map<String, Object>>> getAvailablePermits() {
        return ResponseEntity.ok(jsaService.getAvailablePermitsForLinking());
    }

    @GetMapping
    public ResponseEntity<List<Map<String, Object>>> list(
            @RequestParam(required = false) Integer zoneId,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String permitType,
            @RequestParam(required = false) String q,
            @RequestParam(defaultValue = "100") int limit,
            @RequestParam(defaultValue = "0") int offset) {
        return ResponseEntity.ok(jsaService.getJsaList(zoneId, status, permitType, q, limit, offset));
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getById(@PathVariable String id) {
        Map<String, Object> jsa = jsaService.getJsaById(id);
        if (jsa == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "تحليل السلامة المطلوب غير موجود"));
        }
        return ResponseEntity.ok(jsa);
    }

    @PostMapping
    public ResponseEntity<?> create(@RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "PRODUCTION_SUPERVISOR", "SYSTEM_ADMINISTRATOR", "DEPARTMENT_MANAGER");
        }
        try {
            Map<String, Object> created = jsaService.createJsa(body);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل إنشاء تحليل السلامة: " + e.getMessage()));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> update(@PathVariable String id, @RequestBody Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "PRODUCTION_SUPERVISOR", "SYSTEM_ADMINISTRATOR", "DEPARTMENT_MANAGER");
        }
        try {
            Map<String, Object> updated = jsaService.updateJsa(id, body);
            if (updated == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "JSA غير موجود"));
            }
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل تحديث تحليل السلامة: " + e.getMessage()));
        }
    }

    @PatchMapping("/{id}")
    public ResponseEntity<?> patch(@PathVariable String id, @RequestBody Map<String, Object> body) {
        return update(id, body);
    }

    @PatchMapping("/{id}/approve")
    public ResponseEntity<?> approve(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            Map<String, Object> updated = jsaService.updateJsa(id, Map.of("statusId", 3));
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل اعتماد تحليل السلامة: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> delete(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            jsaService.deleteJsa(id);
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل حذف تحليل السلامة: " + e.getMessage()));
        }
    }

    @PostMapping("/{id}/steps")
    public ResponseEntity<?> addStep(@PathVariable String id, @RequestBody Map<String, Object> stepData) {
        try {
            Map<String, Object> updated = jsaService.addStep(id, stepData);
            return ResponseEntity.status(HttpStatus.CREATED).body(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل إضافة الخطوة: " + e.getMessage()));
        }
    }

    @DeleteMapping("/{id}/steps/{stepId}")
    public ResponseEntity<?> deleteStep(@PathVariable String id, @PathVariable int stepId) {
        try {
            Map<String, Object> updated = jsaService.deleteStep(id, stepId);
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل حذف الخطوة: " + e.getMessage()));
        }
    }

    @PostMapping("/{id}/link-permit")
    public ResponseEntity<?> linkPermit(@PathVariable String id, @RequestBody Map<String, Object> body) {
        try {
            Object permitId = body.get("permitId") != null ? body.get("permitId") : body.get("id");
            Map<String, Object> res = jsaService.linkPermit(id, permitId);
            return ResponseEntity.ok(res);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل ربط تصريح العمل: " + e.getMessage()));
        }
    }

    @PostMapping("/{id}/unlink-permit")
    public ResponseEntity<?> unlinkPermit(@PathVariable String id, @RequestBody Map<String, Object> body) {
        try {
            Object permitId = body.get("permitId") != null ? body.get("permitId") : body.get("id");
            Map<String, Object> res = jsaService.unlinkPermit(id, permitId);
            return ResponseEntity.ok(res);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "فشل إلغاء ربط تصريح العمل: " + e.getMessage()));
        }
    }
}
