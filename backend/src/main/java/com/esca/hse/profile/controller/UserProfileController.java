package com.esca.hse.profile.controller;

import com.esca.hse.profile.dto.EmailVerifyRequest;
import com.esca.hse.profile.dto.MfaRequestResponse;
import com.esca.hse.profile.dto.MfaVerifyRequest;
import com.esca.hse.profile.dto.ProfileUpdateRequest;
import com.esca.hse.profile.dto.UserProfileDto;
import com.esca.hse.profile.service.UserProfileService;
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

    public UserProfileController(UserProfileService profileService) {
        this.profileService = profileService;
    }

    @GetMapping
    public UserProfileDto getProfile(Authentication authentication) {
        return profileService.getProfile(requireUsername(authentication));
    }

    @PatchMapping
    public UserProfileDto updateProfile(Authentication authentication, @RequestBody ProfileUpdateRequest request) {
        return profileService.updateProfile(requireUsername(authentication), request);
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
        if (!contentType.equals("image/png") && !contentType.equals("image/jpeg")) {
            throw new ResponseStatusException(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "Only PNG and JPEG avatars are supported");
        }
        if (profileService.isSameAvatar(username, file.getBytes())) {
            throw new IllegalArgumentException("The selected image is already your current avatar");
        }
        Path uploadDirectory = Paths.get("uploads").toAbsolutePath().normalize();
        Files.createDirectories(uploadDirectory);
        String extension = contentType.equals("image/png") ? ".png" : ".jpg";
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
        if (authentication == null || !authentication.isAuthenticated()
                || "anonymousUser".equals(authentication.getPrincipal())) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Authentication required");
        }
        return authentication.getName();
    }
}
