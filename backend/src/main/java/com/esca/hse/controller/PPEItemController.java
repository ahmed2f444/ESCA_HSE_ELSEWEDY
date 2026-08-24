package com.esca.hse.controller;

import com.esca.hse.model.PPEItem;
import com.esca.hse.security.SecurityUtils;
import com.esca.hse.service.PPEItemService;
import jakarta.validation.Valid;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/ppe-items", "/api/ppe/inventory", "/api/ppe/items", "/api/ppe/stock", "/api/v1/ppe-items", "/api/v1/ppe/inventory", "/api/v1/ppe/items", "/api/v1/ppe/stock", "/api/v1/jpa/ppe/items"})
public class PPEItemController {

    private final PPEItemService service;

    public PPEItemController(PPEItemService service) {
        this.service = service;
    }

    @GetMapping
    public List<PPEItem> getAllItems() {
        return service.getAllItems();
    }

    @GetMapping("/below-threshold")
    public List<PPEItem> getItemsBelowThreshold() {
        return service.getItemsBelowThreshold();
    }

    @GetMapping("/{id}")
    public ResponseEntity<PPEItem> getItemById(@PathVariable String id) {
        PPEItem item = service.getItemById(id);
        if (item == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(item);
    }

    @GetMapping("/{id}/days-until-stockout")
    public ResponseEntity<Map<String, Object>> getDaysUntilStockout(@PathVariable String id) {
        PPEItem item = service.getItemById(id);
        if (item == null) {
            return ResponseEntity.notFound().build();
        }

        int days = service.getDaysUntilStockout(item);
        return ResponseEntity.ok(Map.of(
                "ppeItemId", item.getPpeItemId() != null ? item.getPpeItemId() : id,
                "daysUntilStockout", days,
                "estimateAvailable", days >= 0
        ));
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        return service.getSummary();
    }

    @PostMapping
    public ResponseEntity<?> createItem(@Valid @RequestBody PPEItem item, BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "WAREHOUSE_SUPERVISOR", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }

        try {
            PPEItem createdItem = service.createItem(item);
            return ResponseEntity.status(HttpStatus.CREATED).body(createdItem);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to create item"));
        }
    }

    @PutMapping("/{id}")
    public ResponseEntity<?> updateItem(@PathVariable String id, @Valid @RequestBody PPEItem item, BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "WAREHOUSE_SUPERVISOR", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }

        try {
            PPEItem updatedItem = service.updateItem(id, item);
            if (updatedItem == null) {
                return ResponseEntity.notFound().build();
            }
            return ResponseEntity.ok(updatedItem);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to update item"));
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteItem(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            service.deleteItem(id);
            return ResponseEntity.noContent().build();
        } catch (DataIntegrityViolationException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(Map.of("error", "Cannot delete PPE Item because it has associated transaction records."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to delete PPE Item"));
        }
    }
}
