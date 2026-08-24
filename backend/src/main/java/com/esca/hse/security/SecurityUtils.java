package com.esca.hse.security;

import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Collection;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Enterprise Security utility for evaluating authenticated user identity,
 * Role-Based Access Control (RBAC), and server-side ownership.
 */
public final class SecurityUtils {

    private SecurityUtils() {}

    /**
     * Returns current authentication object or null.
     */
    public static Authentication getAuthentication() {
        return SecurityContextHolder.getContext().getAuthentication();
    }

    /**
     * Returns true if request has an authenticated principal (not anonymous).
     */
    public static boolean isAuthenticated() {
        Authentication auth = getAuthentication();
        return auth != null && auth.isAuthenticated() && !"anonymousUser".equals(auth.getPrincipal());
    }

    /**
     * Returns current username or "local-demo" when unauthenticated in development mode.
     */
    public static String getCurrentUsername() {
        Authentication auth = getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return "local-demo";
        }
        return auth.getName();
    }

    /**
     * Returns set of granted authority strings (e.g. "ROLE_HSE_MANAGER", "SCOPE_automation:write").
     */
    public static Set<String> getAuthorities() {
        Authentication auth = getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return Set.of();
        }
        Collection<? extends GrantedAuthority> authorities = auth.getAuthorities();
        if (authorities == null) {
            return Set.of();
        }
        return authorities.stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toSet());
    }

    /**
     * Checks if current user has any of the specified roles (e.g., "HSE_MANAGER", "SYSTEM_ADMINISTRATOR").
     * Prefix "ROLE_" is checked automatically.
     */
    public static boolean hasAnyRole(String... roles) {
        Set<String> authorities = getAuthorities();
        for (String role : roles) {
            String roleUpper = role.toUpperCase().trim();
            if (authorities.contains("ROLE_" + roleUpper) || authorities.contains(roleUpper)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Returns true if user has administrative or HSE manager privileges.
     */
    public static boolean isManagerOrAdmin() {
        return hasAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR");
    }

    /**
     * Returns true if user has HSE Officer, Manager, or Admin privileges.
     */
    public static boolean isOfficerOrManager() {
        return hasAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR");
    }

    /**
     * Enforces that current user must have at least one of the allowed roles, otherwise throws 403 Forbidden AccessDeniedException.
     */
    public static void requireAnyRole(String... allowedRoles) {
        if (!isAuthenticated()) {
            // When security is enabled but no auth is present
            throw new AccessDeniedException("Authentication required");
        }
        if (!hasAnyRole(allowedRoles)) {
            throw new AccessDeniedException("Access denied: requires one of roles " + String.join(", ", allowedRoles));
        }
    }

    /**
     * Enforces ownership or administrative bypass.
     */
    public static void requireOwnershipOrRole(String resourceOwnerUsername, String... allowedRoles) {
        if (!isAuthenticated()) {
            throw new AccessDeniedException("Authentication required");
        }
        if (hasAnyRole(allowedRoles) || isManagerOrAdmin()) {
            return;
        }
        String current = getCurrentUsername();
        if (resourceOwnerUsername != null && resourceOwnerUsername.equalsIgnoreCase(current)) {
            return;
        }
        throw new AccessDeniedException("Access denied: You are not authorized to modify this resource");
    }
}
