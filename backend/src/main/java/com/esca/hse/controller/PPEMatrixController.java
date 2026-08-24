package com.esca.hse.controller;

import com.esca.hse.model.PPEMatrix;
import com.esca.hse.security.SecurityUtils;
import com.esca.hse.service.PPEMatrixService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/ppe/matrix", "/api/ppe-matrix", "/api/v1/ppe/matrix", "/api/v1/ppe-matrix", "/api/v1/jpa/ppe/matrix"})
public class PPEMatrixController {

    private final PPEMatrixService service;

    public PPEMatrixController(PPEMatrixService service) {
        this.service = service;
    }

    // ─────────────────────────────── GET ─────────────────────────────────

    @GetMapping
    public List<PPEMatrix> getAllMatrixEntries(@RequestParam(required = false) String zoneId) {
        if (zoneId != null && !zoneId.isBlank()) {
            return service.getMatrixByZone(zoneId);
        }
        return service.getAllMatrixEntries();
    }

    @GetMapping("/{id}")
    public ResponseEntity<PPEMatrix> getMatrixEntryById(@PathVariable String id) {
        PPEMatrix entry = service.getMatrixEntryById(id);
        if (entry == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(entry);
    }

    @GetMapping("/zone/{zoneId}")
    public List<PPEMatrix> getMatrixByZone(@PathVariable String zoneId) {
        return service.getMatrixByZone(zoneId);
    }

    @GetMapping("/item/{ppeItemId}")
    public List<PPEMatrix> getMatrixByItem(@PathVariable String ppeItemId) {
        return service.getMatrixByItem(ppeItemId);
    }

    @GetMapping("/summary")
    public Map<String, Object> getMatrixSummary() {
        return service.getSummary();
    }

    // ─────────────────────────────── POST ────────────────────────────────

    @PostMapping
    public ResponseEntity<?> createMatrixEntry(@Valid @RequestBody PPEMatrix matrix,
                                               BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            PPEMatrix created = service.createMatrixEntry(matrix);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to create matrix rule"));
        }
    }

    // ─────────────────────────────── PUT ─────────────────────────────────

    @PutMapping("/{id}")
    public ResponseEntity<?> updateMatrixEntry(@PathVariable String id,
                                               @Valid @RequestBody PPEMatrix matrix,
                                               BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            PPEMatrix updated = service.updateMatrixEntry(id, matrix);
            if (updated == null) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to update matrix rule"));
        }
    }

    // ─────────────────────────────── DELETE ──────────────────────────────

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteMatrixEntry(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            boolean deleted = service.deleteMatrixEntry(id);
            if (!deleted) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to delete matrix rule"));
        }
    }
}
