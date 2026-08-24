package com.esca.hse.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    private final JwtService jwtService;

    public JwtAuthenticationFilter(JwtService jwtService) { this.jwtService = jwtService; }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String authorization = request.getHeader("Authorization");
        if (authorization != null && authorization.startsWith("Bearer ")
                && SecurityContextHolder.getContext().getAuthentication() == null) {
            try {
                Map<String, Object> claims = jwtService.parse(authorization.substring(7));
                String subject = String.valueOf(claims.get("sub"));
                List<SimpleGrantedAuthority> authorities = new ArrayList<>();
                if ("service".equals(claims.get("type"))) {
                    String scope = String.valueOf(claims.getOrDefault("scope", ""));
                    for (String item : scope.split(" ")) if (!item.isBlank()) authorities.add(new SimpleGrantedAuthority("SCOPE_" + item));
                    subject = "service:" + subject;
                } else {
                    authorities.add(new SimpleGrantedAuthority("ROLE_" + String.valueOf(claims.get("role"))));
                }
                SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(subject, null, authorities));
            } catch (IllegalArgumentException ignored) {
                SecurityContextHolder.clearContext();
            }
        }
        chain.doFilter(request, response);
    }
}
