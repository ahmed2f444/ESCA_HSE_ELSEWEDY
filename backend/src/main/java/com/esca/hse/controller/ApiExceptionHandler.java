package com.esca.hse.controller;

import com.esca.hse.platform.ResourceNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(AuthController.InvalidCredentialsException.class)
    public ResponseEntity<Map<String, Object>> unauthorized(AuthController.InvalidCredentialsException ex, HttpServletRequest request) {
        return error(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS", ex.getMessage(), Map.of(), request);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, Object>> notFound(ResourceNotFoundException ex, HttpServletRequest request) {
        return error(HttpStatus.NOT_FOUND, "NOT_FOUND", ex.getMessage(), Map.of(), request);
    }

    @ExceptionHandler({IllegalArgumentException.class, MethodArgumentNotValidException.class})
    public ResponseEntity<Map<String, Object>> badRequest(Exception ex, HttpServletRequest request) {
        Map<String, String> fields = new LinkedHashMap<>();
        if (ex instanceof MethodArgumentNotValidException validation) {
            validation.getBindingResult().getFieldErrors().forEach(error -> fields.put(error.getField(), error.getDefaultMessage()));
        }
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", ex.getMessage(), fields, request);
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> conflict(DataIntegrityViolationException ex, HttpServletRequest request) {
        return error(HttpStatus.CONFLICT, "DATA_CONFLICT", "The operation conflicts with related HSE records", Map.of(), request);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> unexpected(Exception ex, HttpServletRequest request) {
        ex.printStackTrace();
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "The request could not be completed: " + ex.getMessage(), Map.of(), request);
    }

    private ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message,
            Map<String, String> fieldErrors, HttpServletRequest request) {
        String traceId = (request != null) ? request.getHeader("X-Correlation-ID") : null;
        if (traceId == null || traceId.isBlank()) {
            traceId = UUID.randomUUID().toString();
        }
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("code", code != null ? code : "INTERNAL_ERROR");
        body.put("message", message != null ? message : status.getReasonPhrase());
        body.put("fieldErrors", fieldErrors != null ? fieldErrors : Map.of());
        body.put("traceId", traceId);
        return ResponseEntity.status(status).body(body);
    }
}
