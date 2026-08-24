package com.esca.hse.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Common utility methods and response helpers for REST controllers.
 */
public final class ControllerUtils {

    private ControllerUtils() {
        // Utility class
    }

    /**
     * Builds a structured 400 Bad Request response entity containing validation error messages.
     *
     * @param bindingResult Spring MVC binding result containing field errors
     * @return ResponseEntity with validation errors payload
     */
    public static ResponseEntity<Map<String, Object>> buildValidationError(BindingResult bindingResult) {
        Map<String, String> fieldErrors = new LinkedHashMap<>();
        if (bindingResult != null) {
            bindingResult.getFieldErrors().forEach(error ->
                    fieldErrors.put(error.getField(), error.getDefaultMessage() != null ? error.getDefaultMessage() : "Invalid value")
            );
        }

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("error", "Validation failed");
        body.put("fields", fieldErrors);
        body.put("validation_errors", fieldErrors);
        return ResponseEntity.badRequest().body(body);
    }

    /**
     * Safely constructs a mutable LinkedHashMap from key-value pairs without risk of NullPointerExceptions.
     */
    public static Map<String, Object> safeMap(Object... entries) {
        Map<String, Object> map = new LinkedHashMap<>();
        if (entries == null) {
            return map;
        }
        for (int i = 0; i < entries.length; i += 2) {
            String key = entries[i] != null ? String.valueOf(entries[i]) : "unknown";
            Object value = (i + 1 < entries.length) ? entries[i + 1] : null;
            map.put(key, value);
        }
        return map;
    }
}
