package com.esca.hse.profile.dto;

public class MfaRequestResponse {
    private final boolean codeSent;
    private final int expiresInSeconds;
    private final String developmentCode;

    public MfaRequestResponse(boolean codeSent, int expiresInSeconds, String developmentCode) {
        this.codeSent = codeSent;
        this.expiresInSeconds = expiresInSeconds;
        this.developmentCode = developmentCode;
    }

    public boolean isCodeSent() {
        return codeSent;
    }

    public int getExpiresInSeconds() {
        return expiresInSeconds;
    }

    public String getDevelopmentCode() {
        return developmentCode;
    }
}
