package com.esca.hse.profile.controller;

import com.esca.hse.profile.dto.EmailVerifyRequest;
import com.esca.hse.profile.dto.MfaRequestResponse;
import com.esca.hse.profile.dto.MfaVerifyRequest;
import com.esca.hse.profile.dto.ProfileUpdateRequest;
import com.esca.hse.profile.dto.UserProfileDto;
import com.esca.hse.profile.service.UserProfileService;
import com.esca.hse.security.JwtService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@RestController
@RequestMapping({"/api/v1/users/me", "/api/users/me"})
public class UserProfileController {
    private final UserProfileService profileService;
    private final JwtService jwtService;
    private final boolean securityEnabled;

    public UserProfileController(
            UserProfileService profileService,
            @Autowired(required = false) JwtService jwtService,
            @Value("${app.security.enabled:false}") boolean securityEnabled) {
        this.profileService = profileService;
        this.jwtService = jwtService;
        this.securityEnabled = securityEnabled;
    }

    @GetMapping
    public UserProfileDto getProfile(Authentication authentication) {
        return profileService.getProfile(requireUsername(authentication));
    }

    @PatchMapping
    public UserProfileDto updateProfile(Authentication authentication, @RequestBody ProfileUpdateRequest request) {
        String username = requireUsername(authentication);
        UserProfileDto updated = profileService.updateProfile(username, request);
        if (jwtService != null && updated.getUsername() != null) {
            try {
                String role = "WORKER";
                if (authentication != null && authentication.getAuthorities() != null) {
                    role = authentication.getAuthorities().stream()
                            .map(Object::toString)
                            .filter(val -> val.startsWith("ROLE_"))
                            .map(val -> val.substring(5))
                            .findFirst()
                            .orElse(authentication.getAuthorities().isEmpty() ? "WORKER" : authentication.getAuthorities().iterator().next().getAuthority());
                }
                String newToken = jwtService.userToken(updated.getUsername(), role, updated.getFullName());
                updated.setToken(newToken);
            } catch (Exception ignored) {}
        }
        return updated;
    }

    @PostMapping("/password/mfa/request")
    public MfaRequestResponse requestPasswordCode(Authentication authentication) {
        return profileService.requestPasswordChangeCode(requireUsername(authentication));
    }

    @PostMapping("/password/mfa/verify")
    public ResponseEntity<Void> verifyPasswordCode(Authentication authentication, @RequestBody MfaVerifyRequest request) {
        profileService.verifyPasswordChangeCode(requireUsername(authentication), request.getCode(), request.getNewPassword());
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/email/mfa/request")
    public MfaRequestResponse requestEmailCode(Authentication authentication) {
        return profileService.requestEmailChangeCode(requireUsername(authentication));
    }

    @PostMapping("/email/mfa/verify")
    public UserProfileDto verifyEmailCode(Authentication authentication, @RequestBody EmailVerifyRequest request) {
        return profileService.verifyEmailChangeCode(requireUsername(authentication), request.getCode(), request.getNewEmail());
    }

    @PostMapping("/avatar")
    public UserProfileDto uploadAvatar(
            Authentication authentication,
            @RequestParam("avatar") MultipartFile file) throws IOException {
        String username = requireUsername(authentication);
        if (file.isEmpty()) throw new IllegalArgumentException("Avatar file is required");
        if (file.getSize() > 20 * 1024 * 1024) throw new IllegalArgumentException("Avatar file exceeds 20 MB");
        String contentType = file.getContentType() == null ? "" : file.getContentType().toLowerCase();
        if (!contentType.equals("image/png") && !contentType.equals("image/jpeg") && !contentType.equals("image/webp")) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Only PNG, JPEG, and WEBP avatars are supported");
        }
        Path uploadDirectory = Paths.get("uploads").toAbsolutePath().normalize();
        Files.createDirectories(uploadDirectory);
        String extension = contentType.equals("image/png") ? ".png" : (contentType.equals("image/webp") ? ".webp" : ".jpg");
        String fileName = "avatar-" + java.util.UUID.randomUUID() + extension;
        Path destination = uploadDirectory.resolve(fileName).normalize();
        if (!destination.getParent().equals(uploadDirectory)) throw new IllegalArgumentException("Invalid avatar path");
        file.transferTo(destination);
        return profileService.updateAvatar(username, "/uploads/" + fileName);
    }

    @DeleteMapping("/avatar")
    public UserProfileDto deleteAvatar(Authentication authentication) {
        return profileService.deleteAvatar(requireUsername(authentication));
    }

    private String requireUsername(Authentication authentication) {
        if (authentication != null && authentication.isAuthenticated()
                && !"anonymousUser".equals(authentication.getPrincipal())) {
            return authentication.getName();
        }
        if (!securityEnabled) {
            String active = profileService.resolvePrimaryUsername();
            if (active != null) return active;
            return "mostafa";
        }
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Authentication required");
    }
}
