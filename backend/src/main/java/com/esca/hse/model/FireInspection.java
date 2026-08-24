package com.esca.hse.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

public class FireInspection {

    private String id;

    @NotBlank(message = "Equipment ID is required")
    private String equipmentId;

    @NotNull(message = "Inspection date is required")
    private LocalDate inspectionDate;

    @NotBlank(message = "Inspector name is required")
    private String inspectorName;

    @NotBlank(message = "Status is required (e.g. PASSED, FAILED, MAINTENANCE_REQUIRED)")
    private String status;

    private String notes;

    public FireInspection() {
    }

    public FireInspection(String id, String equipmentId, LocalDate inspectionDate, String inspectorName, String status, String notes) {
        this.id = id;
        this.equipmentId = equipmentId;
        this.inspectionDate = inspectionDate;
        this.inspectorName = inspectorName;
        this.status = status;
        this.notes = notes;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getEquipmentId() { return equipmentId; }
    public void setEquipmentId(String equipmentId) { this.equipmentId = equipmentId; }

    public LocalDate getInspectionDate() { return inspectionDate; }
    public void setInspectionDate(LocalDate inspectionDate) { this.inspectionDate = inspectionDate; }

    public String getInspectorName() { return inspectorName; }
    public void setInspectorName(String inspectorName) { this.inspectorName = inspectorName; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
}
