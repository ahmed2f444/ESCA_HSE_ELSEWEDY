package com.esca.hse.controller;

import com.esca.hse.model.FireEquipment;
import com.esca.hse.security.SecurityUtils;
import com.esca.hse.service.FireEquipmentService;
import jakarta.validation.Valid;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/fire-equipment", "/api/fire/equipment", "/api/v1/fire-equipment", "/api/v1/fire/equipment", "/api/v1/jpa/fire/equipment"})
public class FireEquipmentController {

    private final FireEquipmentService service;

    public FireEquipmentController(FireEquipmentService service) {
        this.service = service;
    }

    // ─────────────────────────────── GET ─────────────────────────────────

    @GetMapping
    public List<FireEquipment> getAllEquipment() {
        return service.getAllEquipment();
    }

    @GetMapping("/stats")
    public Map<String, Object> getStatsSummary() {
        return service.getStatsSummary();
    }

    @GetMapping("/attention")
    public List<Map<String, Object>> getAttentionList() {
        return service.getAttentionList();
    }

    @GetMapping("/coverage")
    public List<Map<String, Object>> getCoverageList() {
        return service.getCoverageList();
    }

    @GetMapping("/{id}")
    public ResponseEntity<FireEquipment> getEquipmentById(@PathVariable String id) {
        FireEquipment fe = service.getEquipmentById(id);
        if (fe == null) return ResponseEntity.notFound().build();
        return ResponseEntity.ok(fe);
    }

    // ─────────────────────────────── POST ────────────────────────────────

    @PostMapping
    public ResponseEntity<?> createEquipment(@Valid @RequestBody FireEquipment equipment,
                                             BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            FireEquipment created = service.createEquipment(equipment);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Unexpected error"));
        }
    }

    // ─────────────────────────────── PUT ─────────────────────────────────

    @PutMapping("/{id}")
    public ResponseEntity<?> updateEquipment(@PathVariable String id,
                                             @Valid @RequestBody FireEquipment equipment,
                                             BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            FireEquipment updated = service.updateEquipment(id, equipment);
            if (updated == null) return ResponseEntity.notFound().build();
            return ResponseEntity.ok(updated);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Unexpected error"));
        }
    }

    // ─────────────────────────────── SERVICE & WORK ORDER ────────────────
    @PostMapping("/{id}/service")
    public ResponseEntity<?> serviceEquipment(@PathVariable String id, @RequestBody(required = false) Map<String, Object> body) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "MAINTENANCE_ENGINEER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            Map<String, Object> payload = body != null ? body : Map.of();
            Map<String, Object> result = service.serviceEquipment(id, payload);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to service equipment"));
        }
    }

    // ─────────────────────────────── DELETE ──────────────────────────────

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteEquipment(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (service.getEquipmentById(id) == null) {
            return ResponseEntity.notFound().build();
        }
        try {
            service.deleteEquipment(id);
            return ResponseEntity.noContent().build();
        } catch (DataIntegrityViolationException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "Cannot delete fire equipment because it has associated records."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to delete equipment"));
        }
    }
}
