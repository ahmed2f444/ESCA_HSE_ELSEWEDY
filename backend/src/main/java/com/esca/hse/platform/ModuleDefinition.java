package com.esca.hse.platform;

import java.util.LinkedHashSet;
import java.util.Set;

public record ModuleDefinition(
        String key,
        String table,
        String idColumn,
        String idPrefix,
        String titleColumn,
        Set<String> writableColumns
) {
    public ModuleDefinition {
        writableColumns = Set.copyOf(new LinkedHashSet<>(writableColumns));
    }
}
