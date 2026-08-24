package com.esca.hse.controller;

import com.esca.hse.platform.PlatformService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/training/{resource:courses|certificates}")
public class TrainingController {
    private final PlatformService service;

    public TrainingController(PlatformService service) { this.service = service; }

    private String module(String resource) { return resource.equals("courses") ? "training-courses" : "certificates"; }

    @GetMapping
    public List<Map<String, Object>> list(@PathVariable String resource,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "200") int limit) {
        return service.list(module(resource), q, status, limit);
    }

    @GetMapping("/{id}")
    public Map<String, Object> get(@PathVariable String resource, @PathVariable String id) {
        return service.get(module(resource), id);
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> create(@PathVariable String resource, @RequestBody Map<String, Object> body) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(module(resource), body));
    }

    @PatchMapping("/{id}")
    public Map<String, Object> update(@PathVariable String resource, @PathVariable String id, @RequestBody Map<String, Object> body) {
        return service.update(module(resource), id, body);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String resource, @PathVariable String id) {
        service.delete(module(resource), id);
        return ResponseEntity.noContent().build();
    }
}
