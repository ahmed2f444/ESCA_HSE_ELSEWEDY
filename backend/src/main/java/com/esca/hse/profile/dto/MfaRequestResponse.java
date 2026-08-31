package com.esca.hse.profile.dto;

public class MfaRequestResponse {
    private final boolean codeSent;
    private final int expiresInSeconds;

    public MfaRequestResponse(boolean codeSent, int expiresInSeconds) {
        this.codeSent = codeSent;
        this.expiresInSeconds = expiresInSeconds;
    }

    public boolean isCodeSent() {
        return codeSent;
    }

    public int getExpiresInSeconds() {
        return expiresInSeconds;
    }

}
