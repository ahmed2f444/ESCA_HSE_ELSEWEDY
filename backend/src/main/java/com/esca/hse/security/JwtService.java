package com.esca.hse.security;

import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class JwtService {
    private final ObjectMapper objectMapper;
    private final byte[] secret;
    private final long userTtlSeconds;

    public JwtService(ObjectMapper objectMapper,
            @Value("${app.security.jwt-secret}") String secret,
            @Value("${app.security.token-ttl-seconds:28800}") long userTtlSeconds) {
        this.objectMapper = objectMapper;
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
        this.userTtlSeconds = userTtlSeconds;
    }

    public String userToken(String subject, String role, String displayName) {
        return issue(subject, userTtlSeconds, Map.of("type", "user", "role", role, "name", displayName));
    }

    public String serviceToken(String subject, String scope, long ttlSeconds) {
        return issue(subject, ttlSeconds, Map.of("type", "service", "scope", scope));
    }

    public Map<String, Object> parse(String token) {
        try {
            String[] parts = token.split("\\.");
            if (parts.length != 3) throw new IllegalArgumentException("Invalid token");
            String signed = parts[0] + "." + parts[1];
            byte[] expected = hmac(signed);
            byte[] supplied = Base64.getUrlDecoder().decode(parts[2]);
            if (!java.security.MessageDigest.isEqual(expected, supplied)) throw new IllegalArgumentException("Invalid token");
            Map<String, Object> claims = objectMapper.readValue(Base64.getUrlDecoder().decode(parts[1]), new TypeReference<>() {});
            Number expiry = (Number) claims.get("exp");
            if (expiry == null || Instant.now().getEpochSecond() >= expiry.longValue()) throw new IllegalArgumentException("Expired token");
            return claims;
        } catch (Exception ex) {
            throw new IllegalArgumentException("Invalid token");
        }
    }

    public long userTtlSeconds() { return userTtlSeconds; }

    private String issue(String subject, long ttlSeconds, Map<String, Object> additionalClaims) {
        try {
            long now = Instant.now().getEpochSecond();
            String header = encode(objectMapper.writeValueAsBytes(Map.of("alg", "HS256", "typ", "JWT")));
            Map<String, Object> claims = new LinkedHashMap<>();
            claims.put("sub", subject);
            claims.put("iat", now);
            claims.put("exp", now + ttlSeconds);
            claims.putAll(additionalClaims);
            String payload = encode(objectMapper.writeValueAsBytes(claims));
            String signed = header + "." + payload;
            return signed + "." + encode(hmac(signed));
        } catch (Exception ex) {
            throw new IllegalStateException("Could not issue token", ex);
        }
    }

    private byte[] hmac(String value) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret, "HmacSHA256"));
        return mac.doFinal(value.getBytes(StandardCharsets.UTF_8));
    }

    private String encode(byte[] value) { return Base64.getUrlEncoder().withoutPadding().encodeToString(value); }
}
