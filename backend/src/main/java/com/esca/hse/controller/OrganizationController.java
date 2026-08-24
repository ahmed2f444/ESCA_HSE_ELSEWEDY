package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/organization/{module:departments|zones|employees}")
public class OrganizationController {
    private final PlatformService service;

    public OrganizationController(PlatformService service) { this.service = service; }

    @GetMapping
    public List<Map<String, Object>> list(@PathVariable String module,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "200") int limit) {
        return service.list(module, q, status, limit);
    }

    @GetMapping("/{id}")
    public Map<String, Object> get(@PathVariable String module, @PathVariable String id) { return service.get(module, id); }

    @PostMapping
    public ResponseEntity<Map<String, Object>> create(@PathVariable String module, @RequestBody Map<String, Object> body) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(module, body));
    }

    @PatchMapping("/{id}")
    public Map<String, Object> update(@PathVariable String module, @PathVariable String id, @RequestBody Map<String, Object> body) {
        return service.update(module, id, body);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String module, @PathVariable String id) {
        service.delete(module, id);
        return ResponseEntity.noContent().build();
    }
}
