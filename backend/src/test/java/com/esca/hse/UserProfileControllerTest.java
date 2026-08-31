package com.esca.hse;

import com.esca.hse.profile.dto.ProfileUpdateRequest;
import com.esca.hse.profile.dto.UserProfileDto;
import com.esca.hse.profile.service.UserProfileService;
import com.esca.hse.security.JwtService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:esca-profile-test;MODE=MySQL;DB_CLOSE_DELAY=-1;DATABASE_TO_LOWER=TRUE",
        "app.security.enabled=true",
        "app.security.demo-users-enabled=false",
        "app.demo-data.enabled=false"
})
@AutoConfigureMockMvc
class UserProfileControllerTest {

    @Autowired MockMvc mvc;
    @Autowired JdbcTemplate jdbc;
    @Autowired PasswordEncoder encoder;
    @Autowired JwtService jwtService;
    @Autowired UserProfileService profileService;

    @BeforeEach
    void setupFixtures() {
        jdbc.update("DELETE FROM user_avatars");
        jdbc.update("DELETE FROM mfa_codes");
        jdbc.update("DELETE FROM profile_edit_history");
        jdbc.update("DELETE FROM user_roles");
        jdbc.update("DELETE FROM users");
        jdbc.update("DELETE FROM employees");
        jdbc.update("DELETE FROM roles");

        jdbc.update("INSERT INTO roles (role_id, role_name, description, scope_level) VALUES (1, 'HSE Manager', 'HSE oversight', 'SITE')");
        jdbc.update("INSERT INTO employees (employee_id, employee_code, display_name, email, phone, job_title, department_id) "
                + "VALUES ('EMP-001', 'EMP-001', 'Mostafa Mohamed', 'mostafa@elsewedy.com', '01000000001', 'HSE Manager', 'DEP-01')");
        jdbc.update("INSERT INTO users (user_id, employee_id, username, password_hash, status_id) VALUES (1, 'EMP-001', 'mostafa', ?, 1)",
                encoder.encode("HseDemo@2026"));
        jdbc.update("INSERT INTO user_roles (user_id, role_id, status_id) VALUES (1, 1, 1)");
    }

    @Test
    void testGetProfileSuccess() throws Exception {
        String token = jwtService.userToken("mostafa", "HSE_MANAGER", "Mostafa Mohamed");

        mvc.perform(get("/api/users/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("mostafa"))
                .andExpect(jsonPath("$.fullName").value("Mostafa Mohamed"))
                .andExpect(jsonPath("$.email").value("mostafa@elsewedy.com"))
                .andExpect(jsonPath("$.jobTitle").value("HSE Manager"));
    }

    @Test
    void testUpdateProfileUsernameAndFullName() throws Exception {
        String token = jwtService.userToken("mostafa", "HSE_MANAGER", "Mostafa Mohamed");

        mvc.perform(patch("/api/users/me")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"fullName\":\"Mostafa ElSayed\",\"username\":\"mostafa.new\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.fullName").value("Mostafa ElSayed"))
                .andExpect(jsonPath("$.username").value("mostafa.new"));

        UserProfileDto updated = profileService.getProfile("mostafa.new");
        assertThat(updated.getFullName()).isEqualTo("Mostafa ElSayed");
        assertThat(updated.getUsername()).isEqualTo("mostafa.new");
    }

    @Test
    void testUpdateProfileAllFields() throws Exception {
        String token = jwtService.userToken("mostafa", "HSE_MANAGER", "Mostafa Mohamed");

        mvc.perform(patch("/api/users/me")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"fullName\":\"Mostafa Mahmoud\",\"username\":\"mostafa.lead\",\"phone\":\"01099887766\",\"jobTitle\":\"HSE Director\",\"zoneName\":\"CCV Extrusion\",\"departmentName\":\"Plant Safety\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.fullName").value("Mostafa Mahmoud"))
                .andExpect(jsonPath("$.username").value("mostafa.lead"))
                .andExpect(jsonPath("$.phone").value("01099887766"))
                .andExpect(jsonPath("$.jobTitle").value("HSE Director"));

        UserProfileDto updated = profileService.getProfile("mostafa.lead");
        assertThat(updated.getFullName()).isEqualTo("Mostafa Mahmoud");
        assertThat(updated.getPhone()).isEqualTo("01099887766");
        assertThat(updated.getJobTitle()).isEqualTo("HSE Director");
    }

    @Test
    void testUpdateProfileValidationFailure() throws Exception {
        String token = jwtService.userToken("mostafa", "HSE_MANAGER", "Mostafa Mohamed");

        // Invalid full name (single word)
        mvc.perform(patch("/api/users/me")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"fullName\":\"SingleName\"}"))
                .andExpect(status().isBadRequest());

        // Invalid username (invalid characters)
        mvc.perform(patch("/api/users/me")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"username\":\"user name with spaces!\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testMfaRequestAndVerifyEmail() throws Exception {
        var resp = profileService.requestEmailChangeCode("mostafa");
        assertThat(resp.isCodeSent()).isTrue();
        assertThat(resp.getDevelopmentCode()).isNotNull();

        UserProfileDto updated = profileService.verifyEmailChangeCode("mostafa", resp.getDevelopmentCode(), "mostafa.new@elsewedy.com");
        assertThat(updated.getEmail()).isEqualTo("mostafa.new@elsewedy.com");
    }
}
