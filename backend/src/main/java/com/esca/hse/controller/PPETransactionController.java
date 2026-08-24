package com.esca.hse.controller;

import com.esca.hse.model.PPETransaction;
import com.esca.hse.security.SecurityUtils;
import com.esca.hse.service.PPETransactionService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

@RestController
@RequestMapping({"/api/ppe-transactions", "/api/ppe/transactions", "/api/v1/ppe-transactions", "/api/v1/ppe/transactions", "/api/v1/jpa/ppe/transactions"})
public class PPETransactionController {

    private final PPETransactionService service;

    public PPETransactionController(PPETransactionService service) {
        this.service = service;
    }

    // ─────────────────────────────── GET ─────────────────────────────────

    @GetMapping
    public List<PPETransaction> getAllTransactions() {
        return service.getAllTransactions();
    }

    @GetMapping("/{id}")
    public ResponseEntity<PPETransaction> getTransactionById(@PathVariable String id) {
        PPETransaction tx = service.getTransactionById(id);
        if (tx == null) return ResponseEntity.notFound().build();
        return ResponseEntity.ok(tx);
    }

    @GetMapping("/item/{ppeItemId}")
    public List<PPETransaction> getTransactionsForItem(@PathVariable String ppeItemId) {
        return service.getTransactionsForItem(ppeItemId);
    }

    @GetMapping("/summary")
    public Map<String, Object> getSummary() {
        return service.getSummary();
    }

    // ─────────────────────────────── POST ────────────────────────────────

    @PostMapping
    public ResponseEntity<?> createTransaction(@Valid @RequestBody PPETransaction transaction,
                                               BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "WAREHOUSE_SUPERVISOR", "SYSTEM_ADMINISTRATOR", "PRODUCTION_SUPERVISOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            PPETransaction created = service.createTransaction(transaction);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (IllegalStateException e) {
            // Insufficient stock → 409 Conflict
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("error", e.getMessage()));
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to create transaction"));
        }
    }

    // ─────────────────────────────── PUT ─────────────────────────────────

    @PutMapping("/{id}")
    public ResponseEntity<?> updateTransaction(@PathVariable String id,
                                               @Valid @RequestBody PPETransaction transaction,
                                               BindingResult bindingResult) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "WAREHOUSE_SUPERVISOR", "SYSTEM_ADMINISTRATOR");
        }
        if (bindingResult.hasErrors()) {
            return ControllerUtils.buildValidationError(bindingResult);
        }
        try {
            PPETransaction updated = service.updateTransaction(id, transaction);
            return ResponseEntity.ok(updated);
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (IllegalStateException e) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to update transaction"));
        }
    }

    // ─────────────────────────────── DELETE ──────────────────────────────

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteTransaction(@PathVariable String id) {
        if (SecurityUtils.isAuthenticated()) {
            SecurityUtils.requireAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
        }
        try {
            service.deleteTransaction(id);
            return ResponseEntity.noContent().build();
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage() != null ? e.getMessage() : "Failed to delete transaction"));
        }
    }
}
