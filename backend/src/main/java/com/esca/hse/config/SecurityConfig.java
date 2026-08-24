package com.esca.hse.config;

import com.esca.hse.security.JwtAuthenticationFilter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
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
                        .requestMatchers(HttpMethod.DELETE, "/api/**", "/api/v1/**").hasAnyRole("HSE_MANAGER", "HSE_OFFICER", "SYSTEM_ADMINISTRATOR")
                        .requestMatchers(
                                "/api/v1/occupational-health/**", "/api/occupational-health/**", "/api/v1/raw/occupational-health/**"
                        ).hasAnyRole("HSE_MANAGER", "OCCUPATIONAL_DOCTOR", "SYSTEM_ADMINISTRATOR")
                        .requestMatchers(
                                "/api/v1/master-data/**", "/api/master-data/**",
                                "/api/v1/departments/**", "/api/departments/**",
                                "/api/v1/organization/**",
                                "/api/v1/automation-rules/**", "/api/v1/raw/automation-rules/**",
                                "/api/v1/security/**", "/api/security/**",
                                "/api/v1/integrations/**", "/api/integrations/**"
                        ).hasAnyRole("HSE_MANAGER", "SYSTEM_ADMINISTRATOR", "AUDITOR")
                        .requestMatchers(
                                "/api/v1/audit/**", "/api/audit/**",
                                "/api/v1/audit-log/**", "/api/audit-log/**"
                        ).hasAnyRole("HSE_MANAGER", "AUDITOR", "SYSTEM_ADMINISTRATOR")
                        .anyRequest().authenticated();
                    }
                })
                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}

