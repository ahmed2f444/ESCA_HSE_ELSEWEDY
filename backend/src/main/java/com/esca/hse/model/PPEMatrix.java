package com.esca.hse.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * Entity representing Zone-to-PPE requirements matrix.
 * Maps specific industrial plant zones to mandatory PPE items.
 */
@Entity
@Table(name = "ppe_matrix")
public class PPEMatrix {

    @Id
    @NotBlank(message = "Matrix ID is required (e.g. PPM-001)")
    @Column(name = "matrix_id")
    private String matrixId;

    @NotBlank(message = "Zone ID is required (e.g. ZN-A1)")
    @Column(name = "zone_id")
    private String zoneId;

    @NotBlank(message = "PPE Item ID is required (e.g. PPE-1001)")
    @Column(name = "ppe_item_id")
    private String ppeItemId;

    @NotNull(message = "Required flag must be specified (1 for mandatory, 0 for optional)")
    @Column(name = "required_flag")
    private Integer requiredFlag = 1;

    @Column(name = "notes")
    private String notes;

    public PPEMatrix() {
    }

    public PPEMatrix(String matrixId, String zoneId, String ppeItemId, Integer requiredFlag, String notes) {
        this.matrixId = matrixId;
        this.zoneId = zoneId;
        this.ppeItemId = ppeItemId;
        this.requiredFlag = requiredFlag;
        this.notes = notes;
    }

    // ────────────────────────── Getters & Setters ──────────────────────────

    public String getMatrixId() {
        return matrixId;
    }

    public void setMatrixId(String matrixId) {
        this.matrixId = matrixId;
    }

    public String getZoneId() {
        return zoneId;
    }

    public void setZoneId(String zoneId) {
        this.zoneId = zoneId;
    }

    public String getPpeItemId() {
        return ppeItemId;
    }

    public void setPpeItemId(String ppeItemId) {
        this.ppeItemId = ppeItemId;
    }

    public Integer getRequiredFlag() {
        return requiredFlag;
    }

    public void setRequiredFlag(Integer requiredFlag) {
        this.requiredFlag = requiredFlag;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}
