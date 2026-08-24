package com.esca.hse.controller;

import com.esca.hse.security.JwtService;
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
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping({"/api/v1/auth", "/api/auth", "/auth"})
public class AuthController {
    private final NamedParameterJdbcTemplate jdbc;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthController(@org.springframework.beans.factory.annotation.Autowired(required = false) NamedParameterJdbcTemplate jdbc, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.jdbc = jdbc;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
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
                "    COALESCE(e.display_name, u.username) AS display_name, " +
                "    COALESCE(r.role_name, 'HSE Manager') AS role_name " +
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
        
        String rawRole = String.valueOf(user.get("role_name")).toUpperCase().replace(" ", "_");
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
        String token = jwtService.userToken(username, rawRole, displayName);
        
        return Map.of(
                "token", token,
                "access_token", token,
                "token_type", "Bearer",
                "expires_in", jwtService.userTtlSeconds(),
                "user", Map.of(
                        "id", user.get("user_id"),
                        "username", username,
                        "displayName", displayName,
                        "name", displayName,
                        "initials", displayName.length() > 1 ? displayName.substring(0, 1) : username.substring(0, 1).toUpperCase(),
                        "role", rawRole
                )
        );
    }

    @GetMapping("/me")
    public Map<String, Object> me(Authentication authentication) {
        return Map.of(
                "username", authentication == null ? "local-demo" : authentication.getName(),
                "authorities", authentication == null ? List.of() : authentication.getAuthorities()
        );
    }

    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public static class InvalidCredentialsException extends RuntimeException {
        public InvalidCredentialsException() {
            super("Invalid username or password");
        }
    }
}
