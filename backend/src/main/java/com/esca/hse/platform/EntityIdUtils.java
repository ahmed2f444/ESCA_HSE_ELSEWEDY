package com.esca.hse.platform;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Utility methods for parsing, normalizing, and formatting domain entity identifiers.
 */
public final class EntityIdUtils {

    private static final Pattern NUMERIC_PATTERN = Pattern.compile("\\d+");

    private EntityIdUtils() {
        // Utility class
    }

    /**
     * Extracts the first numeric sequence found in a string ID, or returns the default value.
     * Examples: "FE-0042" -> 42, "PPE-1001" -> 1001, "123" -> 123, "invalid" -> 1.
     *
     * @param id           the raw ID string
     * @param defaultValue the fallback value if no numeric sequence is found
     * @return parsed numeric integer
     */
    public static int parseNumericId(String id, int defaultValue) {
        if (id == null || id.isBlank()) {
            return defaultValue;
        }
        try {
            Matcher m = NUMERIC_PATTERN.matcher(id.trim());
            if (m.find()) {
                return Integer.parseInt(m.group());
            }
            return defaultValue;
        } catch (Exception e) {
            return defaultValue;
        }
    }

    /**
     * Parses numeric ID with default fallback of 1.
     */
    public static int parseNumericId(String id) {
        return parseNumericId(id, 1);
    }

    /**
     * Formats an integer ID with a standardized prefix and zero padding.
     * Example: formatId("FE", 42) -> "FE-0042".
     *
     * @param prefix the prefix without trailing dash (e.g. "FE", "PPE", "INSP", "PPM", "FSA")
     * @param id     the integer ID
     * @return formatted ID string
     */
    public static String formatId(String prefix, int id) {
        return String.format("%s-%04d", prefix, id);
    }

    /**
     * Formats a zone ID into a standard code representation (e.g. 1 -> "ZONE-A", 2 -> "ZONE-B").
     *
     * @param zoneId the integer zone ID
     * @return formatted zone string
     */
    public static String formatZoneCode(int zoneId) {
        if (zoneId >= 1 && zoneId <= 26) {
            char letter = (char) ('A' + (zoneId - 1));
            return "ZONE-" + letter;
        }
        return "ZONE-" + zoneId;
    }
}
