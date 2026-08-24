package com.esca.hse.controller;

import com.esca.hse.model.FireInspection;
import com.esca.hse.service.FireInspectionService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/fire/inspections", "/api/fire-inspections", "/api/v1/fire/inspections", "/api/v1/fire-inspections", "/api/v1/jpa/fire/inspections"})
public class FireInspectionController {

    private final FireInspectionService service;

    public FireInspectionController(FireInspectionService service) {
        this.service = service;
    }

    // ─────────────────────────────── GET ─────────────────────────────────

    @GetMapping
    public List<FireInspection> getAllInspections(@RequestParam(required = false) String equipmentId) {
        if (equipmentId != null && !equipmentId.isBlank()) {
            return service.getInspectionsByEquipment(equipmentId);
        }
        return service.getAllInspections();
    }

    @GetMapping("/{id}")
    public ResponseEntity<FireInspection> getInspectionById(@PathVariable String id) {
        FireInspection insp = service.getInspectionById(id);
        if (insp == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(insp);
    }

    @GetMapping("/equipment/{equipmentId}")
    public List<FireInspection> getByEquipment(@PathVariable String equipmentId) {
        return service.getInspectionsByEquipment(equipmentId);
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        return service.getInspectionSummary();
    }

    // ─────────────────────────────── POST ────────────────────────────────

    @PostMapping
    public ResponseEntity<?> createInspection(@Valid @RequestBody FireInspection inspection, BindingResult bindingResult) {
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            FireInspection created = service.createInspection(inspection);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to record inspection"));
        }
    }

    // ─────────────────────────────── PUT ─────────────────────────────────

    @PutMapping("/{id}")
    public ResponseEntity<?> updateInspection(@PathVariable String id,
                                             @Valid @RequestBody FireInspection inspection,
                                             BindingResult bindingResult) {
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            FireInspection updated = service.updateInspection(id, inspection);
            if (updated == null) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to update inspection"));
        }
    }

    // ─────────────────────────────── DELETE ──────────────────────────────

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteInspection(@PathVariable String id) {
        try {
            boolean deleted = service.deleteInspection(id);
            if (!deleted) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to delete inspection"));
        }
    }
}
