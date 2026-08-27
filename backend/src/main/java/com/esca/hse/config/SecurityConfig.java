package com.esca.hse.config;

import com.esca.hse.security.JwtAuthenticationFilter;
import com.esca.hse.security.RbacAuthorizationFilter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfigurationSource;

@Configuration
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    @Bean
    PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }

    @Bean
    SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            JwtAuthenticationFilter jwtFilter,
            RbacAuthorizationFilter rbacFilter,
            CorsConfigurationSource corsConfigurationSource,
            @Value("${app.security.enabled:false}") boolean securityEnabled) throws Exception {
        
        http.csrf(csrf -> csrf.disable())
                .cors(cors -> cors.configurationSource(corsConfigurationSource))
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .exceptionHandling(exceptions -> exceptions
                        .authenticationEntryPoint((request, response, authException) -> {
                            response.setStatus(jakarta.servlet.http.HttpServletResponse.SC_UNAUTHORIZED);
                            response.setContentType("application/json;charset=UTF-8");
                            response.getWriter().write("{\"error\":\"UNAUTHORIZED\",\"message\":\"Authentication required\",\"status\":401}");
                        })
                        .accessDeniedHandler((request, response, accessDeniedException) -> {
                            response.setStatus(jakarta.servlet.http.HttpServletResponse.SC_FORBIDDEN);
                            response.setContentType("application/json;charset=UTF-8");
                            response.getWriter().write("{\"error\":\"FORBIDDEN\",\"message\":\"Access denied: Insufficient permissions\",\"status\":403}");
                        })
                )
                .authorizeHttpRequests(authorize -> {
                    if (!securityEnabled) {
                        authorize.anyRequest().permitAll();
                    } else {
                        authorize.requestMatchers(
                                "/api/v1/auth/**", "/api/auth/**", "/auth/**",
                                "/api/v1/health/**", "/api/health/**", "/health/**",
                                "/api/v1/internal/auth/service-token",
                                "/swagger-ui/**", "/v3/api-docs/**"
                        ).permitAll()
                        .requestMatchers("/api/v1/internal/automation/**").hasAuthority("SCOPE_automation:write")
                        // RbacAuthorizationFilter applies the action-level policy
                        // (read/create/update/delete/approve/export) to user APIs.
                        .requestMatchers("/api/**").authenticated()
                        .anyRequest().authenticated();
                    }
                })
                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
                .addFilterAfter(rbacFilter, JwtAuthenticationFilter.class);

        return http.build();
    }
}

