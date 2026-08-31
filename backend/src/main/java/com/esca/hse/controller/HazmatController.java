package com.esca.hse.controller;

import com.esca.hse.service.HazmatService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/v1/hazmat", "/api/hazmat", "/hazmat"})
@CrossOrigin
public class HazmatController {

    private final HazmatService hazmatService;

    public HazmatController(HazmatService hazmatService) {
        this.hazmatService = hazmatService;
    }

    // ─────────────────────────────── KPI STATS ─────────────────────────────────

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getStats() {
        return ResponseEntity.ok(hazmatService.getStats());
    }

    // ─────────────────────────────── CHEMICALS CRUD ────────────────────────────

    @GetMapping({"/chemicals", ""})
    public ResponseEntity<List<Map<String, Object>>> listChemicals(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String query,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) Integer zoneId,
            @RequestParam(required = false) String ghs
    ) {
        String searchQuery = (query != null && !query.isBlank()) ? query : q;
        return ResponseEntity.ok(hazmatService.listChemicals(searchQuery, status, zoneId, ghs));
    }

    @GetMapping({"/chemicals/{id}", "/{id:[0-9]+}"})
    public ResponseEntity<Map<String, Object>> getChemical(@PathVariable int id) {
        Map<String, Object> chemical = hazmatService.getChemicalById(id);
        if (chemical == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Chemical #" + id + " not found"));
        }
        return ResponseEntity.ok(chemical);
    }

    @PostMapping({"/chemicals", ""})
    public ResponseEntity<Map<String, Object>> createChemical(@RequestBody Map<String, Object> body) {
        try {
            Map<String, Object> created = hazmatService.createChemical(body);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    @PutMapping({"/chemicals/{id}", "/{id:[0-9]+}"})
    public ResponseEntity<Map<String, Object>> updateChemical(@PathVariable int id, @RequestBody Map<String, Object> body) {
        try {
            Map<String, Object> updated = hazmatService.updateChemical(id, body);
            if (updated == null) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Chemical #" + id + " not found"));
            }
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping({"/chemicals/{id}", "/{id:[0-9]+}"})
    public ResponseEntity<Map<String, Object>> deleteChemical(@PathVariable int id) {
        boolean deleted = hazmatService.deleteChemical(id);
        if (!deleted) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Chemical #" + id + " not found or could not be deleted"));
        }
        return ResponseEntity.ok(Map.of("success", true, "chemicalId", id, "message", "تم حذف المادة الكيميائية وسجلاتها بنجاح."));
    }

    // ─────────────────────────────── SDS ARCHIVE ───────────────────────────────

    @GetMapping("/sds")
    public ResponseEntity<List<Map<String, Object>>> listSds(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String query,
            @RequestParam(required = false) String status
    ) {
        String searchQuery = (query != null && !query.isBlank()) ? query : q;
        return ResponseEntity.ok(hazmatService.listSdsRecords(searchQuery, status));
    }

    @PostMapping("/sds")
    public ResponseEntity<Map<String, Object>> createSds(@RequestBody Map<String, Object> body) {
        try {
            Map<String, Object> res = hazmatService.createOrUpdateSds(body);
            return ResponseEntity.status(HttpStatus.CREATED).body(res);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    @PutMapping("/sds/{id}")
    public ResponseEntity<Map<String, Object>> updateSds(@PathVariable int id, @RequestBody Map<String, Object> body) {
        try {
            body.put("sdsId", id);
            Map<String, Object> res = hazmatService.createOrUpdateSds(body);
            return ResponseEntity.ok(res);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping("/sds/{id}")
    public ResponseEntity<Map<String, Object>> deleteSds(@PathVariable int id) {
        boolean deleted = hazmatService.deleteSds(id);
        if (!deleted) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "SDS record not found"));
        }
        return ResponseEntity.ok(Map.of("success", true, "sdsId", id, "message", "تم حذف صحيفة بيانات السلامة بنجاح."));
    }

    // ─────────────────────────────── STORAGE COMPATIBILITY ────────────────────

    @GetMapping("/compatibility")
    public ResponseEntity<Map<String, Object>> getCompatibility() {
        return ResponseEntity.ok(hazmatService.getCompatibilityMatrix());
    }
}
