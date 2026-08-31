package com.esca.hse.security;

import com.esca.hse.security.RbacPolicy.Action;
import com.esca.hse.security.RbacPolicy.Module;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpMethod;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Locale;

/** Applies the canonical RBAC matrix to every user-facing API request. */
@Component
public class RbacAuthorizationFilter extends OncePerRequestFilter {
    private final RbacPolicy policy;
    private final boolean securityEnabled;

    public RbacAuthorizationFilter(RbacPolicy policy,
            @Value("${app.security.enabled:false}") boolean securityEnabled) {
        this.policy = policy;
        this.securityEnabled = securityEnabled;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return !securityEnabled || !path.startsWith("/api/") || isPublicOrInternal(path);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            chain.doFilter(request, response);
            return;
        }

        String role = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .filter(authority -> authority.startsWith("ROLE_"))
                .findFirst()
                .orElse("");
        Decision decision = classify(request);
        if (decision == null || !policy.isAllowed(role, decision.module(), decision.action())) {
            deny(response);
            return;
        }
        chain.doFilter(request, response);
    }

    private static Decision classify(HttpServletRequest request) {
        String path = request.getRequestURI().toLowerCase(Locale.ROOT);
        if (path.contains("/users/me")) {
            return new Decision(Module.DASHBOARD,
                    HttpMethod.GET.matches(request.getMethod()) ? Action.READ : Action.UPDATE);
        }
        Action action = actionFor(request.getMethod(), path);

        if (containsAny(path, "/dashboard", "/notifications", "/field/")) {
            return new Decision(Module.DASHBOARD, action);
        }
        if (path.contains("/reports")) return new Decision(Module.REPORTS, path.contains("send-management") ? Action.EXPORT : action);
        if (path.contains("/audit")) return new Decision(Module.AUDIT, action);
        if (containsAny(path, "/master-data", "/departments", "/organization/", "/security/", "/integrations", "/automation-rules")) {
            return new Decision(Module.ADMIN, action);
        }
        if (path.contains("/occupational-health")) {
            if (path.contains("/self")) return new Decision(Module.HEALTH_SELF, action);
            if (path.endsWith("/stats") || path.contains("/summary")) return new Decision(Module.HEALTH_AGGREGATE, action);
            return new Decision(Module.HEALTH, action);
        }
        if (path.contains("/training")) return new Decision(Module.TRAINING, action);
        if (containsAny(path, "/incidents", "/capa")) return new Decision(Module.INCIDENTS, action);
        if (path.contains("/permits")) return new Decision(Module.PERMITS, action);
        if (containsAny(path, "/inspections", "/findings", "/fire", "/ppe", "/fixed-safety", "/safety/fixed-assets", "/sensor-events", "/iot/")) {
            return new Decision(Module.INSPECTIONS, action);
        }
        if (containsAny(path, "/risks", "/risk/", "/jsa", "/hazmat")) return new Decision(Module.RISKS, action);
        if (containsAny(path, "/agent/", "/ai/ask", "/ai/suggestions")) return new Decision(Module.AI_AGENT, action);
        if (containsAny(path, "/ai/", "/iot")) return new Decision(Module.INSPECTIONS, action);
        return null; // Fail closed for future API routes until they are classified.
    }

    private static Action actionFor(String method, String path) {
        if (path.contains("/approve") || path.contains("/verify")) return Action.APPROVE;
        if (HttpMethod.GET.matches(method) || HttpMethod.HEAD.matches(method) || HttpMethod.OPTIONS.matches(method)) return Action.READ;
        if (HttpMethod.POST.matches(method)) return Action.CREATE;
        if (HttpMethod.PUT.matches(method) || HttpMethod.PATCH.matches(method)) return Action.UPDATE;
        if (HttpMethod.DELETE.matches(method)) return Action.DELETE;
        return Action.UPDATE;
    }

    private static boolean containsAny(String value, String... needles) {
        for (String needle : needles) if (value.contains(needle)) return true;
        return false;
    }

    private static boolean isPublicOrInternal(String path) {
        return path.matches("/api(?:/v1)?/(?:auth|health)(?:/.*)?")
                || path.startsWith("/api/v1/internal/");
    }

    private static void deny(HttpServletResponse response) throws IOException {
        response.setStatus(HttpServletResponse.SC_FORBIDDEN);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"error\":\"FORBIDDEN\",\"message\":\"Access denied by RBAC policy\",\"status\":403}");
    }

    private record Decision(Module module, Action action) { }
}
