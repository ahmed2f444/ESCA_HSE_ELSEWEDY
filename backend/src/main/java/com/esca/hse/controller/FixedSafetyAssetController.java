package com.esca.hse.controller;

import com.esca.hse.model.FixedSafetyAsset;
import com.esca.hse.security.SecurityUtils;
import com.esca.hse.service.FixedSafetyAssetService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/safety/fixed-assets", "/api/fixed-safety-assets", "/api/ppe/fixed-assets", "/api/ppe/fixedAssets", "/api/v1/safety/fixed-assets", "/api/v1/fixed-safety-assets", "/api/v1/ppe/fixed-assets", "/api/v1/ppe/fixedAssets", "/api/v1/jpa/safety/fixed-assets"})
public class FixedSafetyAssetController {

    private final FixedSafetyAssetService service;

    public FixedSafetyAssetController(FixedSafetyAssetService service) {
        this.service = service;
    }

    // ─────────────────────────────── GET ─────────────────────────────────

    @GetMapping
    public List<FixedSafetyAsset> getAllAssets(@RequestParam(required = false) String zoneId,
                                              @RequestParam(required = false) String assetType) {
        if (zoneId != null && !zoneId.isBlank()) {
            return service.getAssetsByZone(zoneId);
        }
        if (assetType != null && !assetType.isBlank()) {
            return service.getAssetsByType(assetType);
        }
        return service.getAllAssets();
    }

    @GetMapping("/{id}")
    public ResponseEntity<FixedSafetyAsset> getAssetById(@PathVariable String id) {
        FixedSafetyAsset asset = service.getAssetById(id);
        if (asset == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(asset);
    }

    @GetMapping("/zone/{zoneId}")
    public List<FixedSafetyAsset> getByZone(@PathVariable String zoneId) {
        return service.getAssetsByZone(zoneId);
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        return service.getAssetSummary();
    }

    // ─────────────────────────────── POST ────────────────────────────────

    @PostMapping
    public ResponseEntity<?> createAsset(@Valid @RequestBody FixedSafetyAsset asset, BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            FixedSafetyAsset created = service.createAsset(asset);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to record fixed safety asset"));
        }
    }

    // ─────────────────────────────── PUT ─────────────────────────────────

    @PutMapping("/{id}")
    public ResponseEntity<?> updateAsset(@PathVariable String id,
                                         @Valid @RequestBody FixedSafetyAsset asset,
                                         BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            FixedSafetyAsset updated = service.updateAsset(id, asset);
            if (updated == null) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to update fixed safety asset"));
        }
    }

    // ─────────────────────────────── DELETE ──────────────────────────────

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteAsset(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            boolean deleted = service.deleteAsset(id);
            if (!deleted) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.noContent().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to delete fixed safety asset"));
        }
    }
}
