package com.esca.hse.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class DemoUserSeeder implements CommandLineRunner {
    private final boolean enabled;

    public DemoUserSeeder(@Value("${app.security.demo-users-enabled:false}") boolean enabled) {
        this.enabled = enabled;
    }

    @Override
    public void run(String... args) {
        // No DDL or custom table creation. Authentication uses original Railway schema.
    }
}
