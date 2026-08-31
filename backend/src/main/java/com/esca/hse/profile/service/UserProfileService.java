package com.esca.hse.profile.service;

import com.esca.hse.profile.dto.MfaRequestResponse;
import com.esca.hse.profile.dto.ProfileUpdateRequest;
import com.esca.hse.profile.dto.UserProfileDto;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Pattern;

@Service
public class UserProfileService {
    private static final int MFA_EXPIRY_SECONDS = 120;
    private static final SecureRandom MFA_RANDOM = new SecureRandom();
    private static final Pattern FULL_NAME_PATTERN = Pattern.compile("\\p{L}+(?: \\p{L}+)*");

    private final JdbcTemplate jdbc;
    private final DataSource dataSource;
    private final PasswordEncoder passwordEncoder;
    public UserProfileService(
            JdbcTemplate jdbc,
            DataSource dataSource,
            PasswordEncoder passwordEncoder) {
        this.jdbc = jdbc;
        this.dataSource = dataSource;
        this.passwordEncoder = passwordEncoder;
    }

    public UserProfileDto getProfile(String username) {
        if (username == null || username.isBlank()) {
            throw new IllegalArgumentException("Authenticated username is required");
        }
        String employeeName = employeeColumn("display_name", "full_name");
        String employeeEmail = employeeColumn("email_alias", "email");
        String employeePhone = employeeColumn("phone_ext", "phone");
        String zoneJoin = hasTable("zones") && hasColumn("employees", "zone_id")
                ? " LEFT JOIN zones z ON z.zone_id = e.zone_id " : "";
        String zoneName = zoneJoin.isBlank() ? "NULL"
                : "z." + (hasColumn("zones", "zone_name") ? "zone_name" : "name_en");
        String departmentJoin = zoneJoin.isBlank() ? "" : " LEFT JOIN departments d ON d.department_id = z.department_id ";
        String departmentName = departmentJoin.isBlank() ? "NULL"
                : "d." + (hasColumn("departments", "department_name") ? "department_name" : "name_en");
        String avatarJoin = hasTable("user_avatars")
                ? " LEFT JOIN user_avatars a ON a.user_id = u.user_id " : "";
        String avatarPath = avatarJoin.isBlank() ? "NULL" : "a.file_path";
        String mfaEnabled = hasColumn("users", "mfa_enabled") ? "u.mfa_enabled" : "FALSE";
        String sql = "SELECT u.user_id, u.employee_id, u.username, " + mfaEnabled
                + " AS mfa_enabled, e." + employeeName + " AS full_name, e." + employeeEmail
                + " AS email, e.job_title, e." + employeePhone + " AS phone, "
                + zoneName + " AS zone_name, " + departmentName + " AS department_name, "
                + "CASE WHEN u.status_id = 1 THEN 'ACTIVE' ELSE 'INACTIVE' END AS status, "
                + avatarPath + " AS avatar_path FROM users u "
                + "LEFT JOIN employees e ON e.employee_id = u.employee_id "
                + zoneJoin + departmentJoin + avatarJoin
                + "WHERE LOWER(u.username) = LOWER(?)";
        return jdbc.queryForObject(sql, (rs, rowNum) -> {
            UserProfileDto dto = new UserProfileDto();
            dto.setUserId(rs.getObject("user_id"));
            dto.setEmployeeId(rs.getString("employee_id"));
            dto.setUsername(rs.getString("username"));
            dto.setFullName(rs.getString("full_name"));
            dto.setEmail(rs.getString("email"));
            dto.setJobTitle(rs.getString("job_title"));
            dto.setPhone(rs.getString("phone"));
            dto.setZoneName(rs.getString("zone_name"));
            dto.setDepartmentName(rs.getString("department_name"));
            dto.setStatus(rs.getString("status"));
            dto.setMfaEnabled(rs.getBoolean("mfa_enabled"));
            dto.setAvatarPath(rs.getString("avatar_path"));
            return dto;
        }, username);
    }

    @Transactional
    public UserProfileDto updateProfile(String currentUsername, ProfileUpdateRequest request) {
        UserProfileDto current = getProfile(currentUsername);
        if (request.getFullName() != null) {
            validateFullName(request.getFullName());
            if (request.getFullName().trim().equals(current.getFullName())) {
                throw new IllegalArgumentException("Please choose a different full name");
            }
            jdbc.update("UPDATE employees SET " + employeeColumn("display_name", "full_name")
                    + " = ? WHERE employee_id = ?", request.getFullName().trim(), current.getEmployeeId());
        }
        if (request.getUsername() != null) {
            String username = request.getUsername().trim();
            if (username.isBlank()) throw new IllegalArgumentException("Username cannot be blank");
            Integer duplicate = jdbc.queryForObject(
                    "SELECT COUNT(*) FROM users WHERE LOWER(username) = LOWER(?) AND user_id <> ?",
                    Integer.class, username, current.getUserId());
            if (duplicate != null && duplicate > 0) throw new IllegalArgumentException("Username is already in use");
            if (!username.equalsIgnoreCase(current.getUsername())) {
                jdbc.update("UPDATE users SET username = ? WHERE user_id = ?", username, current.getUserId());
            }
        }
        return getProfile(request.getUsername() == null ? currentUsername : request.getUsername().trim());
    }

    public MfaRequestResponse requestPasswordChangeCode(String username) {
        return requestCode(username);
    }

    public MfaRequestResponse requestEmailChangeCode(String username) {
        return requestCode(username);
    }

    private MfaRequestResponse requestCode(String username) {
        UserProfileDto profile = getProfile(username);
        String code = String.format("%06d", MFA_RANDOM.nextInt(1_000_000));
        String codeHash = sha256Hex(code);
        jdbc.update("INSERT INTO mfa_codes (user_id, code_hash, created_at, expires_at, used_flag, attempt_count) "
                        + "VALUES (?, ?, ?, ?, FALSE, 0)",
                profile.getUserId(), codeHash, Timestamp.from(Instant.now()),
                Timestamp.from(Instant.now().plusSeconds(MFA_EXPIRY_SECONDS)));
        return new MfaRequestResponse(true, MFA_EXPIRY_SECONDS, code);
    }

    @Transactional
    public void verifyPasswordChangeCode(String username, String code, String newPassword) {
        UserProfileDto profile = getProfile(username);
        if (code == null || code.isBlank() || newPassword == null || newPassword.isBlank()) {
            throw new IllegalArgumentException("Code and new password are required");
        }
        Map<String, Object> pending = findPendingCode(profile.getUserId());
        checkCode(pending, code);
        if (newPassword.length() < 5) throw new IllegalArgumentException("Password must contain at least 5 characters");
        if (containsNamePart(newPassword, profile.getFullName())) {
            throw new IllegalArgumentException("Password must not contain your name");
        }
        String oldHash = jdbc.queryForObject("SELECT password_hash FROM users WHERE user_id = ?",
                String.class, profile.getUserId());
        String newHash = passwordEncoder.encode(newPassword);
        if (passwordEncoder.matches(newPassword, oldHash)) {
            throw new IllegalArgumentException("Please choose a different password");
        }
        jdbc.update("UPDATE users SET password_hash = ? WHERE user_id = ?", newHash, profile.getUserId());
        markCodeUsed(pending);
        recordProfileChange(profile.getUserId(), "password", oldHash, "[changed]");
    }

    @Transactional
    public UserProfileDto verifyEmailChangeCode(String username, String code, String newEmail) {
        UserProfileDto profile = getProfile(username);
        validateEmail(profile, newEmail);
        Map<String, Object> pending = findPendingCode(profile.getUserId());
        checkCode(pending, code);
        String emailColumn = employeeColumn("email_alias", "email");
        jdbc.update("UPDATE employees SET " + emailColumn + " = ? WHERE employee_id = ?",
                newEmail.trim().toLowerCase(), profile.getEmployeeId());
        markCodeUsed(pending);
        recordProfileChange(profile.getUserId(), "email", profile.getEmail(), newEmail.trim().toLowerCase());
        return getProfile(username);
    }

    @Transactional
    public UserProfileDto updateAvatar(String username, String avatarPath) {
        UserProfileDto profile = getProfile(username);
        if (!hasTable("user_avatars")) throw new IllegalStateException("Avatar storage is not configured");
        jdbc.update("INSERT INTO user_avatars (user_id, file_name, file_path, created_at, updated_at) "
                        + "VALUES (?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE file_name = VALUES(file_name), "
                        + "file_path = VALUES(file_path), updated_at = VALUES(updated_at)",
                profile.getUserId(), "profile-picture", avatarPath, Timestamp.from(Instant.now()), Timestamp.from(Instant.now()));
        recordProfileChange(profile.getUserId(), "avatar", profile.getAvatarPath(), avatarPath);
        return getProfile(username);
    }

    @Transactional
    public UserProfileDto deleteAvatar(String username) {
        UserProfileDto profile = getProfile(username);
        if (profile.getAvatarPath() == null || profile.getAvatarPath().isBlank()) {
            throw new IllegalArgumentException("No profile image to remove");
        }
        jdbc.update("DELETE FROM user_avatars WHERE user_id = ?", profile.getUserId());
        recordProfileChange(profile.getUserId(), "avatar", profile.getAvatarPath(), null);
        return getProfile(username);
    }

    public boolean isSameAvatar(String username, byte[] content) throws IOException {
        String avatarPath = getProfile(username).getAvatarPath();
        if (avatarPath == null || !avatarPath.startsWith("/uploads/")) return false;
        Path current = Paths.get(avatarPath.substring(1)).normalize();
        return Files.isRegularFile(current)
                && MessageDigest.isEqual(sha256(Files.readAllBytes(current)), sha256(content));
    }

    private Map<String, Object> findPendingCode(Object userId) {
        try {
            Map<String, Object> pending = jdbc.queryForMap(
                    "SELECT mfa_code_id, code_hash, expires_at FROM mfa_codes "
                            + "WHERE user_id = ? AND used_flag = FALSE ORDER BY created_at DESC LIMIT 1", userId);
            jdbc.update("UPDATE mfa_codes SET attempt_count = attempt_count + 1 WHERE mfa_code_id = ?",
                    pending.get("mfa_code_id"));
            return pending;
        } catch (DataAccessException ex) {
            throw new IllegalArgumentException("No active verification code");
        }
    }

    private void checkCode(Map<String, Object> pending, String code) {
        Object expiresAt = pending.get("expires_at");
        if (expiresAt instanceof Timestamp timestamp && timestamp.before(Timestamp.from(Instant.now()))) {
            throw new IllegalArgumentException("Verification code has expired");
        }
        if (!sha256Hex(code).equalsIgnoreCase(String.valueOf(pending.get("code_hash")))) {
            throw new IllegalArgumentException("Invalid verification code");
        }
    }

    private void markCodeUsed(Map<String, Object> pending) {
        jdbc.update("UPDATE mfa_codes SET used_flag = TRUE WHERE mfa_code_id = ?", pending.get("mfa_code_id"));
    }

    private void validateEmail(UserProfileDto profile, String newEmail) {
        if (newEmail == null || !newEmail.trim().matches("^[^\\s@]+@esca\\.local$")) {
            throw new IllegalArgumentException("Email must end with @esca.local");
        }
        String email = newEmail.trim().toLowerCase();
        if (email.equalsIgnoreCase(profile.getEmail())) throw new IllegalArgumentException("Email is already in use");
        String emailColumn = employeeColumn("email_alias", "email");
        Integer duplicate = jdbc.queryForObject("SELECT COUNT(*) FROM employees WHERE LOWER(" + emailColumn
                + ") = LOWER(?) AND employee_id <> ?", Integer.class, email, profile.getEmployeeId());
        if (duplicate != null && duplicate > 0) throw new IllegalArgumentException("Email is already in use");
    }

    private void validateFullName(String fullName) {
        String value = fullName == null ? "" : fullName.trim();
        if (value.length() < 8 || !FULL_NAME_PATTERN.matcher(value).matches()) {
            throw new IllegalArgumentException("Enter a first and last name separated by a space");
        }
    }

    private boolean containsNamePart(String value, String fullName) {
        if (fullName == null) return false;
        String normalizedValue = value.toLowerCase().replaceAll("[^\\p{L}\\p{N}]", "");
        for (String part : fullName.toLowerCase().split("\\s+")) {
            String normalizedPart = part.replaceAll("[^\\p{L}\\p{N}]", "");
            if (!normalizedPart.isBlank() && normalizedValue.contains(normalizedPart)) return true;
        }
        return false;
    }

    private void recordProfileChange(Object userId, String field, String oldValue, String newValue) {
        if (!hasTable("profile_edit_history")) return;
        jdbc.update("INSERT INTO profile_edit_history (user_id, field_name, old_value, new_value, modified_at) "
                        + "VALUES (?, ?, ?, ?, ?)", userId, field, oldValue, newValue, Timestamp.from(Instant.now()));
    }

    private String employeeColumn(String preferred, String fallback) {
        return hasColumn("employees", preferred) ? preferred : fallback;
    }

    private boolean hasTable(String table) {
        try (var connection = dataSource.getConnection()) {
            var metadata = connection.getMetaData();
            try (var tables = metadata.getTables(null, null, table, new String[]{"TABLE"})) {
                return tables.next();
            }
        } catch (Exception ex) {
            return false;
        }
    }

    private boolean hasColumn(String table, String column) {
        try (var connection = dataSource.getConnection()) {
            var metadata = connection.getMetaData();
            try (var columns = metadata.getColumns(null, null, table, column)) {
                if (columns.next()) return true;
            }
            try (var columns = metadata.getColumns(null, null, table.toUpperCase(), column.toUpperCase())) {
                return columns.next();
            }
        } catch (Exception ex) {
            return false;
        }
    }

    private byte[] sha256(byte[] value) {
        try {
            return MessageDigest.getInstance("SHA-256").digest(value);
        } catch (Exception ex) {
            throw new IllegalStateException("Unable to hash verification code", ex);
        }
    }

    private String sha256Hex(String value) {
        StringBuilder result = new StringBuilder();
        for (byte item : sha256(value.getBytes(java.nio.charset.StandardCharsets.UTF_8))) {
            result.append(String.format("%02x", item));
        }
        return result.toString();
    }
}
