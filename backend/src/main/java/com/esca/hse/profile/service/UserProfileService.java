package com.esca.hse.profile.service;

import com.esca.hse.profile.dto.MfaRequestResponse;
import com.esca.hse.profile.dto.ProfileUpdateRequest;
import com.esca.hse.profile.dto.UserProfileDto;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.sql.DataSource;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class UserProfileService {
    private static final Logger log = LoggerFactory.getLogger(UserProfileService.class);
    private static final int MFA_EXPIRY_SECONDS = 120;
    private static final SecureRandom MFA_RANDOM = new SecureRandom();

    private final JdbcTemplate jdbc;
    private final DataSource dataSource;
    private final PasswordEncoder passwordEncoder;

    // In-memory fallback for verification codes
    private final Map<String, PendingOtp> memoryCodes = new ConcurrentHashMap<>();

    private record PendingOtp(Object userId, String codeHash, Instant expiresAt, int attemptCount) {}

    public UserProfileService(
            JdbcTemplate jdbc,
            DataSource dataSource,
            PasswordEncoder passwordEncoder) {
        this.jdbc = jdbc;
        this.dataSource = dataSource;
        this.passwordEncoder = passwordEncoder;
    }

    @PostConstruct
    public void initSchema() {
        if (jdbc == null) return;
        try {
            jdbc.execute("CREATE TABLE IF NOT EXISTS user_avatars ("
                    + "user_id INT PRIMARY KEY, "
                    + "file_name VARCHAR(255) NOT NULL, "
                    + "file_path VARCHAR(500) NOT NULL, "
                    + "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                    + "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");
        } catch (Exception e) {
            log.debug("user_avatars table init note: {}", e.getMessage());
        }

        try {
            jdbc.execute("CREATE TABLE IF NOT EXISTS mfa_codes ("
                    + "mfa_code_id INT PRIMARY KEY AUTO_INCREMENT, "
                    + "user_id INT NOT NULL, "
                    + "code_hash VARCHAR(64) NOT NULL, "
                    + "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
                    + "expires_at TIMESTAMP NOT NULL, "
                    + "used_flag BOOLEAN DEFAULT FALSE, "
                    + "attempt_count INT DEFAULT 0)");
        } catch (Exception e) {
            log.debug("mfa_codes table init note: {}", e.getMessage());
        }

        try {
            jdbc.execute("CREATE TABLE IF NOT EXISTS profile_edit_history ("
                    + "history_id INT PRIMARY KEY AUTO_INCREMENT, "
                    + "user_id INT NOT NULL, "
                    + "field_name VARCHAR(80) NOT NULL, "
                    + "old_value VARCHAR(1000), "
                    + "new_value VARCHAR(1000), "
                    + "modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");
        } catch (Exception e) {
            log.debug("profile_edit_history table init note: {}", e.getMessage());
        }
    }

    public String resolvePrimaryUsername() {
        if (jdbc == null) return "mostafa";
        try {
            List<String> list = jdbc.queryForList("SELECT username FROM users WHERE status_id = 1 ORDER BY user_id ASC LIMIT 1", String.class);
            if (!list.isEmpty() && list.get(0) != null && !list.get(0).isBlank()) {
                return list.get(0);
            }
        } catch (Exception ignored) {}
        return "mostafa";
    }

    public UserProfileDto getProfile(String username) {
        String effectiveUsername = (username == null || username.isBlank()) ? resolvePrimaryUsername() : username.trim();

        UserProfileDto dto = new UserProfileDto();
        dto.setUsername(effectiveUsername);
        dto.setUserId(1);
        dto.setEmployeeId("EMP-001");
        dto.setFullName("مصطفى محمد");
        dto.setEmail(effectiveUsername.toLowerCase() + "@elsewedy.com");
        dto.setPhone("01000000001");
        dto.setJobTitle("مدير السلامة والصحة المهنية (HSE Manager)");
        dto.setZoneName("خطوط العزل CCV");
        dto.setDepartmentName("قطاع الإنتاج والتصنيع (ESCA)");
        dto.setStatus("ACTIVE");
        dto.setMfaEnabled(false);
        dto.setAvatarPath(null);

        if (jdbc == null) return dto;

        try {
            // 1. Fetch user account from users table
            List<Map<String, Object>> userRows = jdbc.queryForList(
                    "SELECT * FROM users WHERE LOWER(username) = LOWER(?) LIMIT 1",
                    effectiveUsername);

            if (userRows.isEmpty()) {
                userRows = jdbc.queryForList("SELECT * FROM users WHERE status_id = 1 ORDER BY user_id ASC LIMIT 1");
            }
            if (userRows.isEmpty()) {
                userRows = jdbc.queryForList("SELECT * FROM users ORDER BY user_id ASC LIMIT 1");
            }

            if (!userRows.isEmpty()) {
                Map<String, Object> u = userRows.get(0);
                if (u.get("user_id") != null) dto.setUserId(u.get("user_id"));
                if (u.get("employee_id") != null) dto.setEmployeeId(String.valueOf(u.get("employee_id")));
                if (u.get("username") != null) dto.setUsername(String.valueOf(u.get("username")));
                if (u.get("mfa_enabled") != null) {
                    Object mfa = u.get("mfa_enabled");
                    dto.setMfaEnabled(Boolean.TRUE.equals(mfa) || "1".equals(String.valueOf(mfa)));
                }
                if (u.get("status_id") != null) {
                    dto.setStatus(Integer.valueOf(1).equals(u.get("status_id")) ? "ACTIVE" : "INACTIVE");
                }
            }

            // 2. Fetch employee details
            String empId = dto.getEmployeeId();
            List<Map<String, Object>> empRows = List.of();
            if (empId != null && !empId.isBlank()) {
                try {
                    empRows = jdbc.queryForList("SELECT * FROM employees WHERE employee_id = ? LIMIT 1", empId);
                } catch (Exception ignored) {}
            }

            if (empRows.isEmpty()) {
                try {
                    empRows = jdbc.queryForList("SELECT * FROM employees ORDER BY created_at ASC LIMIT 1");
                } catch (Exception ignored) {}
            }

            if (!empRows.isEmpty()) {
                Map<String, Object> e = empRows.get(0);
                // Name
                String name = getFirstString(e, "display_name", "full_name", "name_ar", "name_en");
                if (name != null && !name.isBlank()) dto.setFullName(name);

                // Email
                String email = getFirstString(e, "email_alias", "email", "work_email");
                if (email != null && !email.isBlank()) dto.setEmail(email);

                // Phone
                String phone = getFirstString(e, "phone_ext", "phone", "mobile", "contact_number");
                if (phone != null && !phone.isBlank()) dto.setPhone(phone);

                // Job Title
                String job = getFirstString(e, "job_title", "role_title", "position");
                if (job != null && !job.isBlank()) dto.setJobTitle(job);

                // Zone & Department
                Object zoneIdObj = e.get("zone_id");
                if (zoneIdObj != null) {
                    try {
                        List<Map<String, Object>> zoneRows = jdbc.queryForList(
                                "SELECT * FROM zones WHERE zone_id = ? LIMIT 1", zoneIdObj);
                        if (!zoneRows.isEmpty()) {
                            Map<String, Object> z = zoneRows.get(0);
                            String zName = getFirstString(z, "name_ar", "name_en", "zone_name");
                            if (zName != null && !zName.isBlank()) dto.setZoneName(zName);

                            Object deptIdObj = z.get("department_id");
                            if (deptIdObj != null) {
                                List<Map<String, Object>> deptRows = jdbc.queryForList(
                                        "SELECT * FROM departments WHERE department_id = ? LIMIT 1", deptIdObj);
                                if (!deptRows.isEmpty()) {
                                    String dName = getFirstString(deptRows.get(0), "name_ar", "name_en", "department_name");
                                    if (dName != null && !dName.isBlank()) dto.setDepartmentName(dName);
                                }
                            }
                        }
                    } catch (Exception ignored) {}
                }

                Object deptIdObj = e.get("department_id");
                if (deptIdObj != null) {
                    try {
                        List<Map<String, Object>> deptRows = jdbc.queryForList(
                                "SELECT * FROM departments WHERE department_id = ? LIMIT 1", deptIdObj);
                        if (!deptRows.isEmpty()) {
                            String dName = getFirstString(deptRows.get(0), "department_name", "name_ar", "name_en");
                            if (dName != null && !dName.isBlank()) dto.setDepartmentName(dName);
                        }
                    } catch (Exception ignored) {}
                }
            }

            // 3. Fetch avatar if exists
            try {
                List<Map<String, Object>> avRows = jdbc.queryForList(
                        "SELECT file_path FROM user_avatars WHERE user_id = ? LIMIT 1", dto.getUserId());
                if (!avRows.isEmpty()) {
                    dto.setAvatarPath(String.valueOf(avRows.get(0).get("file_path")));
                }
            } catch (Exception ignored) {}

        } catch (Exception ex) {
            log.warn("getProfile encountered exception for user {}: {}", username, ex.getMessage());
        }

        return dto;
    }

    @Transactional
    public UserProfileDto updateProfile(String currentUsername, ProfileUpdateRequest request) {
        UserProfileDto current = getProfile(currentUsername);
        String targetUsername = currentUsername;

        // 1. Full Name Validation & DB Update
        if (request.getFullName() != null) {
            String newFullName = request.getFullName().trim();
            validateFullName(newFullName);
            if (!newFullName.equals(current.getFullName())) {
                updateEmployeeName(current.getEmployeeId(), newFullName);
                recordProfileChange(current.getUserId(), "full_name", current.getFullName(), newFullName);
            }
        }

        // 2. Username Validation & DB Update
        if (request.getUsername() != null) {
            String newUsername = request.getUsername().trim();
            validateUsername(newUsername);
            if (!newUsername.equalsIgnoreCase(current.getUsername())) {
                Integer duplicate = 0;
                try {
                    duplicate = jdbc.queryForObject(
                            "SELECT COUNT(*) FROM users WHERE LOWER(username) = LOWER(?) AND user_id <> ?",
                            Integer.class, newUsername, current.getUserId());
                } catch (Exception ignored) {}

                if (duplicate != null && duplicate > 0) {
                    throw new IllegalArgumentException("اسم المستخدم مستخدم بالفعل من قبل حساب آخر");
                }
                try {
                    jdbc.update("UPDATE users SET username = ? WHERE user_id = ?", newUsername, current.getUserId());
                } catch (Exception ignored) {}
                recordProfileChange(current.getUserId(), "username", current.getUsername(), newUsername);
                targetUsername = newUsername;
            }
        }

        // 3. Organizational & Employment Fields (HR & Operational Authority Restricted)
        // These fields are managed strictly by HR and HSE administration and directly bound to the DB.
        // Direct employee modifications through self-service profile updates are ignored.
        if (request.getPhone() != null && !request.getPhone().trim().equals(current.getPhone())) {
            log.info("Ignoring direct update attempt to protected corporate phone extension for user: {}", current.getUsername());
        }
        if (request.getJobTitle() != null && !request.getJobTitle().trim().equals(current.getJobTitle())) {
            log.info("Ignoring direct update attempt to protected job title for user: {}", current.getUsername());
        }
        if (request.getZoneName() != null && !request.getZoneName().trim().equals(current.getZoneName())) {
            log.info("Ignoring direct update attempt to protected work zone for user: {}", current.getUsername());
        }
        if (request.getDepartmentName() != null && !request.getDepartmentName().trim().equals(current.getDepartmentName())) {
            log.info("Ignoring direct update attempt to protected department for user: {}", current.getUsername());
        }

        // 7. Email Validation & DB Update
        if (request.getEmail() != null) {
            String newEmail = request.getEmail().trim().toLowerCase();
            validateEmail(current, newEmail);
            if (!newEmail.equalsIgnoreCase(current.getEmail())) {
                updateEmployeeEmail(current.getEmployeeId(), newEmail);
                recordProfileChange(current.getUserId(), "email", current.getEmail(), newEmail);
            }
        }

        return getProfile(targetUsername);
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
        Instant now = Instant.now();
        Instant expiresAt = now.plusSeconds(MFA_EXPIRY_SECONDS);

        // Store in memory for instant reliability
        memoryCodes.put(String.valueOf(profile.getUserId()), new PendingOtp(profile.getUserId(), codeHash, expiresAt, 0));

        // Also persist in DB if table is accessible
        try {
            jdbc.update("INSERT INTO mfa_codes (user_id, code_hash, created_at, expires_at, used_flag, attempt_count) "
                            + "VALUES (?, ?, ?, ?, FALSE, 0)",
                    profile.getUserId(), codeHash, Timestamp.from(now), Timestamp.from(expiresAt));
        } catch (Exception ex) {
            log.debug("Persisting MFA code to DB note: {}", ex.getMessage());
        }
        return new MfaRequestResponse(true, MFA_EXPIRY_SECONDS, code);
    }

    @Transactional
    public void verifyPasswordChangeCode(String username, String code, String newPassword) {
        UserProfileDto profile = getProfile(username);
        if (code == null || code.isBlank() || newPassword == null || newPassword.isBlank()) {
            throw new IllegalArgumentException("رمز التحقق وكلمة المرور الجديدة مطلوبان");
        }
        verifyAndConsumeCode(profile.getUserId(), code);

        if (newPassword.length() < 5) {
            throw new IllegalArgumentException("كلمة المرور يجب ألا تقل عن 5 خانات");
        }
        if (containsNamePart(newPassword, profile.getFullName())) {
            throw new IllegalArgumentException("كلمة المرور لا يجب أن تحتوي على اسمك الشخصي");
        }

        String newHash = passwordEncoder.encode(newPassword);
        try {
            jdbc.update("UPDATE users SET password_hash = ? WHERE user_id = ?", newHash, profile.getUserId());
        } catch (Exception ex) {
            log.warn("Could not update password hash in users table: {}", ex.getMessage());
        }
        recordProfileChange(profile.getUserId(), "password", "[old]", "[changed]");
    }

    @Transactional
    public UserProfileDto verifyEmailChangeCode(String username, String code, String newEmail) {
        UserProfileDto profile = getProfile(username);
        validateEmail(profile, newEmail);
        verifyAndConsumeCode(profile.getUserId(), code);

        String email = newEmail.trim().toLowerCase();
        try {
            int updated = jdbc.update("UPDATE employees SET email_alias = ? WHERE employee_id = ?",
                    email, profile.getEmployeeId());
            if (updated == 0) {
                jdbc.update("UPDATE employees SET email = ? WHERE employee_id = ?",
                        email, profile.getEmployeeId());
            }
        } catch (Exception ex) {
            try {
                jdbc.update("UPDATE employees SET email = ? WHERE employee_id = ?",
                        email, profile.getEmployeeId());
            } catch (Exception ignored) {}
        }
        recordProfileChange(profile.getUserId(), "email", profile.getEmail(), email);
        return getProfile(username);
    }

    @Transactional
    public UserProfileDto updateAvatar(String username, String avatarPath) {
        UserProfileDto profile = getProfile(username);
        Object userId = profile.getUserId();
        try {
            int updated = jdbc.update("UPDATE user_avatars SET file_path = ?, updated_at = ? WHERE user_id = ?",
                    avatarPath, Timestamp.from(Instant.now()), userId);
            if (updated == 0) {
                jdbc.update("INSERT INTO user_avatars (user_id, file_name, file_path, created_at, updated_at) "
                                + "VALUES (?, ?, ?, ?, ?)",
                        userId, "profile-picture", avatarPath, Timestamp.from(Instant.now()), Timestamp.from(Instant.now()));
            }
        } catch (Exception ex) {
            try {
                initSchema();
                jdbc.update("INSERT INTO user_avatars (user_id, file_name, file_path, created_at, updated_at) "
                                + "VALUES (?, ?, ?, ?, ?)",
                        userId, "profile-picture", avatarPath, Timestamp.from(Instant.now()), Timestamp.from(Instant.now()));
            } catch (Exception ignored) {}
        }
        recordProfileChange(userId, "avatar", profile.getAvatarPath(), avatarPath);
        return getProfile(username);
    }

    @Transactional
    public UserProfileDto deleteAvatar(String username) {
        UserProfileDto profile = getProfile(username);
        try {
            jdbc.update("DELETE FROM user_avatars WHERE user_id = ?", profile.getUserId());
        } catch (Exception ignored) {}
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

    private void verifyAndConsumeCode(Object userId, String code) {
        String uidStr = String.valueOf(userId);
        String codeHash = sha256Hex(code.trim());

        // Check memory OTP first
        PendingOtp pending = memoryCodes.get(uidStr);
        if (pending != null) {
            if (pending.expiresAt().isBefore(Instant.now())) {
                memoryCodes.remove(uidStr);
                throw new IllegalArgumentException("رمز التحقق منتهي الصلاحية (Expired verification code)");
            }
            if (pending.codeHash().equalsIgnoreCase(codeHash)) {
                memoryCodes.remove(uidStr);
                return;
            }
        }

        // Check DB OTP if available
        try {
            Map<String, Object> dbPending = jdbc.queryForMap(
                    "SELECT mfa_code_id, code_hash, expires_at FROM mfa_codes "
                            + "WHERE user_id = ? AND used_flag = FALSE ORDER BY created_at DESC LIMIT 1", userId);

            Object expiresAt = dbPending.get("expires_at");
            if (expiresAt instanceof Timestamp ts && ts.before(Timestamp.from(Instant.now()))) {
                throw new IllegalArgumentException("رمز التحقق منتهي الصلاحية (Expired verification code)");
            }
            if (!codeHash.equalsIgnoreCase(String.valueOf(dbPending.get("code_hash")))) {
                throw new IllegalArgumentException("رمز التحقق غير صحيح (Invalid verification code)");
            }
            jdbc.update("UPDATE mfa_codes SET used_flag = TRUE WHERE mfa_code_id = ?", dbPending.get("mfa_code_id"));
            memoryCodes.remove(uidStr);
            return;
        } catch (DataAccessException ex) {
            if (pending == null) {
                throw new IllegalArgumentException("لا يوجد رمز تحقق نشط أو تم استخدامه مسبقاً");
            }
        }
        throw new IllegalArgumentException("رمز التحقق غير صحيح (Invalid verification code)");
    }

    private void updateEmployeeName(String employeeId, String newName) {
        if (jdbc == null || employeeId == null || employeeId.isBlank()) return;
        try {
            int updated = jdbc.update("UPDATE employees SET display_name = ? WHERE employee_id = ?", newName, employeeId);
            if (updated == 0) {
                jdbc.update("UPDATE employees SET full_name = ? WHERE employee_id = ?", newName, employeeId);
            }
        } catch (Exception e1) {
            try {
                jdbc.update("UPDATE employees SET full_name = ? WHERE employee_id = ?", newName, employeeId);
            } catch (Exception ignored) {}
        }
    }

    private void updateEmployeePhone(String employeeId, String newPhone) {
        if (jdbc == null || employeeId == null || employeeId.isBlank()) return;
        try {
            int updated = jdbc.update("UPDATE employees SET phone_ext = ? WHERE employee_id = ?", newPhone, employeeId);
            if (updated == 0) {
                jdbc.update("UPDATE employees SET phone = ? WHERE employee_id = ?", newPhone, employeeId);
            }
        } catch (Exception e1) {
            try {
                jdbc.update("UPDATE employees SET phone = ? WHERE employee_id = ?", newPhone, employeeId);
            } catch (Exception ignored) {}
        }
    }

    private void updateEmployeeJobTitle(String employeeId, String newJob) {
        if (jdbc == null || employeeId == null || employeeId.isBlank()) return;
        try {
            jdbc.update("UPDATE employees SET job_title = ? WHERE employee_id = ?", newJob, employeeId);
        } catch (Exception ignored) {}
    }

    private void updateEmployeeEmail(String employeeId, String newEmail) {
        if (jdbc == null || employeeId == null || employeeId.isBlank()) return;
        try {
            int updated = jdbc.update("UPDATE employees SET email_alias = ? WHERE employee_id = ?", newEmail, employeeId);
            if (updated == 0) {
                jdbc.update("UPDATE employees SET email = ? WHERE employee_id = ?", newEmail, employeeId);
            }
        } catch (Exception e1) {
            try {
                jdbc.update("UPDATE employees SET email = ? WHERE employee_id = ?", newEmail, employeeId);
            } catch (Exception ignored) {}
        }
    }

    private void updateZoneName(String employeeId, String newZone) {
        if (jdbc == null || employeeId == null || employeeId.isBlank()) return;
        try {
            jdbc.update("UPDATE zones z JOIN employees e ON e.zone_id = z.zone_id SET z.name_ar = ? WHERE e.employee_id = ?", newZone, employeeId);
        } catch (Exception ignored) {}
    }

    private void updateDepartmentName(String employeeId, String newDept) {
        if (jdbc == null || employeeId == null || employeeId.isBlank()) return;
        try {
            jdbc.update("UPDATE departments d JOIN employees e ON e.department_id = d.department_id SET d.department_name = ? WHERE e.employee_id = ?", newDept, employeeId);
        } catch (Exception ignored) {}
    }

    private void validateUsername(String username) {
        if (username == null || username.trim().length() < 3) {
            throw new IllegalArgumentException("اسم المستخدم يجب أن يحتوي على 3 أحرف على الأقل");
        }
        if (!username.trim().matches("^[a-zA-Z0-9._-]+$")) {
            throw new IllegalArgumentException("اسم المستخدم يجب أن يحتوي على أحرف إنجليزية وأرقام ونقاط فقط");
        }
    }

    private void validatePhone(String phone) {
        if (phone == null || phone.trim().length() < 3) {
            throw new IllegalArgumentException("رقم الهاتف يجب أن يحتوي على 3 أرقام على الأقل");
        }
        if (!phone.trim().matches("^[+0-9\\s-]{3,20}$")) {
            throw new IllegalArgumentException("رقم الهاتف يجب أن يحتوي على أرقام صحيحة");
        }
    }

    private void validateJobTitle(String jobTitle) {
        if (jobTitle == null || jobTitle.trim().length() < 2) {
            throw new IllegalArgumentException("المسمى الوظيفي يجب أن يحتوي على حرفين على الأقل");
        }
    }

    private void validateEmail(UserProfileDto profile, String newEmail) {
        if (newEmail == null || !newEmail.trim().matches("^[A-Za-z0-9._%+-]+@(esca\\.local|elsewedy\\.com)$")) {
            throw new IllegalArgumentException("يجب أن ينتهي البريد الإلكتروني بنطاق الشركة (@esca.local أو @elsewedy.com)");
        }
        String email = newEmail.trim().toLowerCase();
        if (email.equalsIgnoreCase(profile.getEmail())) {
            throw new IllegalArgumentException("البريد الإلكتروني الجديد مطابق للبريد الحالي");
        }
    }

    private void validateFullName(String fullName) {
        if (fullName == null || fullName.trim().length() < 3) {
            throw new IllegalArgumentException("الاسم الكامل يجب أن يحتوي على 3 أحرف على الأقل");
        }
        String trimmed = fullName.trim();
        if (!trimmed.contains(" ") && !trimmed.contains(".")) {
            throw new IllegalArgumentException("يرجى كتابة الاسم الأول واسم العائلة مفصولين بمسافة");
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
        if (jdbc == null) return;
        try {
            jdbc.update("INSERT INTO profile_edit_history (user_id, field_name, old_value, new_value, modified_at) "
                            + "VALUES (?, ?, ?, ?, ?)", userId, field, oldValue, newValue, Timestamp.from(Instant.now()));
        } catch (Exception ignored) {}
    }

    private String getFirstString(Map<String, Object> map, String... keys) {
        for (String key : keys) {
            Object val = map.get(key);
            if (val != null) {
                String str = String.valueOf(val).trim();
                if (!str.isBlank() && !"null".equalsIgnoreCase(str)) return str;
            }
            // Case-insensitive check
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                if (entry.getKey().equalsIgnoreCase(key) && entry.getValue() != null) {
                    String str = String.valueOf(entry.getValue()).trim();
                    if (!str.isBlank() && !"null".equalsIgnoreCase(str)) return str;
                }
            }
        }
        return null;
    }

    private byte[] sha256(byte[] value) {
        try {
            return MessageDigest.getInstance("SHA-256").digest(value);
        } catch (Exception ex) {
            throw new IllegalStateException("Unable to hash data", ex);
        }
    }

    private String sha256Hex(String value) {
        StringBuilder result = new StringBuilder();
        for (byte item : sha256(value.getBytes(StandardCharsets.UTF_8))) {
            result.append(String.format("%02x", item));
        }
        return result.toString();
    }
}

