package com.esca.hse.controller;

import com.esca.hse.security.JwtService;
import com.esca.hse.security.RbacPolicy;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/v1/auth", "/api/auth", "/auth"})
public class AuthController {
    private final NamedParameterJdbcTemplate jdbc;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final RbacPolicy rbacPolicy;

    public AuthController(@org.springframework.beans.factory.annotation.Autowired(required = false) NamedParameterJdbcTemplate jdbc,
            PasswordEncoder passwordEncoder, JwtService jwtService, RbacPolicy rbacPolicy) {
        this.jdbc = jdbc;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.rbacPolicy = rbacPolicy;
    }

    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody Map<String, String> request) {
        String username = request.getOrDefault("username", "").trim();
        String password = request.getOrDefault("password", "");
        
        List<Map<String, Object>> rows = jdbc.queryForList(
                "SELECT " +
                "    u.user_id, " +
                "    u.username, " +
                "    u.password_hash, " +
                "    u.employee_id, " +
                "    COALESCE(e.display_name, u.username) AS display_name, " +
                "    COALESCE(r.role_name, 'WORKER') AS role_name, " +
                "    r.scope_level, " +
                "    ur.scope_id " +
                "FROM users u " +
                "LEFT JOIN employees e ON e.employee_id = u.employee_id " +
                "LEFT JOIN user_roles ur ON ur.user_id = u.user_id AND ur.status_id = 1 " +
                "LEFT JOIN roles r ON r.role_id = ur.role_id " +
                "WHERE LOWER(u.username) = LOWER(:username) AND u.status_id = 1 " +
                "ORDER BY ur.assignment_id ASC LIMIT 1",
                Map.of("username", username)
        );
        
        if (rows.isEmpty() || !passwordEncoder.matches(password, String.valueOf(rows.get(0).get("password_hash")))) {
            throw new InvalidCredentialsException();
        }
        
        Map<String, Object> user = rows.get(0);
        try {
            jdbc.update("UPDATE users SET last_login_at = :now WHERE user_id = :id",
                    Map.of("now", LocalDateTime.now(), "id", user.get("user_id")));
        } catch (Exception ignored) {
        }
        
        String rawRole = rbacPolicy.canonicalRole(String.valueOf(user.get("role_name")));
        Map<String, Object> rbac = rbacPolicy.describe(rawRole);
        String displayName = String.valueOf(user.get("display_name"));
        if ("mostafa".equalsIgnoreCase(username)) {
            displayName = "مصطفى";
        } else if ("admin".equalsIgnoreCase(username)) {
            displayName = "مدير النظام (Admin)";
        } else if ("hse.manager".equalsIgnoreCase(username)) {
            displayName = "مدير السلامة (HSE Manager)";
        } else if ("hse.officer".equalsIgnoreCase(username)) {
            displayName = "مسؤول السلامة الميداني";
        } else if ("department.manager".equalsIgnoreCase(username)) {
            displayName = "مدير القطاع";
        }
        String dataScope = String.valueOf(rbac.get("dataScope"));
        String scopeId = user.get("scope_id") == null ? null : String.valueOf(user.get("scope_id"));
        String employeeId = user.get("employee_id") == null ? null : String.valueOf(user.get("employee_id"));
        String token = jwtService.userToken(username, rawRole, displayName, dataScope, scopeId, employeeId);

        Map<String, Object> safeUser = new LinkedHashMap<>();
        safeUser.put("id", user.get("user_id"));
        safeUser.put("username", username);
        safeUser.put("displayName", displayName);
        safeUser.put("name", displayName);
        safeUser.put("initials", displayName.length() > 1 ? displayName.substring(0, 1) : username.substring(0, 1).toUpperCase());
        safeUser.put("role", rawRole);
        safeUser.put("dataScope", dataScope);
        safeUser.put("scopeId", scopeId);
        safeUser.put("employeeId", employeeId);
        safeUser.put("permissions", rbac.get("permissions"));
        safeUser.put("approveHighRisk", rbac.get("approveHighRisk"));
        safeUser.put("exportReports", rbac.get("exportReports"));

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("token", token);
        response.put("access_token", token);
        response.put("token_type", "Bearer");
        response.put("expires_in", jwtService.userTtlSeconds());
        response.put("user", safeUser);
        return response;
    }

    @GetMapping("/me")
    public Map<String, Object> me(Authentication authentication) {
        if (authentication == null) return Map.of("username", "local-demo", "authorities", List.of());
        String role = authentication.getAuthorities().stream()
                .map(Object::toString)
                .filter(value -> value.startsWith("ROLE_"))
                .findFirst()
                .orElse("");
        Map<String, Object> response = new LinkedHashMap<>(rbacPolicy.describe(role));
        response.put("username", authentication.getName());
        response.put("authorities", authentication.getAuthorities());
        if (authentication.getDetails() instanceof Map<?, ?> details) {
            response.put("scopeId", details.get("scope_id"));
            response.put("employeeId", details.get("employee_id"));
        }
        return response;
    }

    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public static class InvalidCredentialsException extends RuntimeException {
        public InvalidCredentialsException() {
            super("Invalid username or password");
        }
    }
}
