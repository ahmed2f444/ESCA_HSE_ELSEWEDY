package com.esca.hse.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import jakarta.validation.constraints.NotBlank;

import java.time.LocalDate;

@Entity
@Table(name = "fire_equipment")
public class FireEquipment {

    @Id
    @NotBlank(message = "Equipment ID is required")
    private String equipmentId;

    @NotBlank(message = "Asset type is required")
    @Column(name = "asset_type_id")
    private String assetTypeId;

    private String subtype;

    @Column(name = "department_id")
    private String departmentId;

    @Column(name = "zone_id")
    private String zoneId;

    @Column(name = "location_detail")
    private String locationDetail;

    private String capacity;

    @Column(name = "installation_date")
    private LocalDate installationDate;

    @Column(name = "expiry_date")
    private LocalDate expiryDate;

    @NotBlank(message = "Status is required (ACTIVE, EXPIRED, MAINTENANCE, DECOMMISSIONED)")
    private String status;

    private String vendor;

    @Column(name = "qr_code")
    private String qrCode;

    @Column(name = "last_inspection_date")
    private LocalDate lastInspectionDate;

    @Column(name = "next_inspection_date")
    private LocalDate nextInspectionDate;

    public FireEquipment() {
    }

    public String getEquipmentId() { return equipmentId; }
    public void setEquipmentId(String equipmentId) { this.equipmentId = equipmentId; }

    public String getAssetTypeId() { return assetTypeId; }
    public void setAssetTypeId(String assetTypeId) { this.assetTypeId = assetTypeId; }

    public String getSubtype() { return subtype; }
    public void setSubtype(String subtype) { this.subtype = subtype; }

    public String getDepartmentId() { return departmentId; }
    public void setDepartmentId(String departmentId) { this.departmentId = departmentId; }

    public String getZoneId() { return zoneId; }
    public void setZoneId(String zoneId) { this.zoneId = zoneId; }

    public String getLocationDetail() { return locationDetail; }
    public void setLocationDetail(String locationDetail) { this.locationDetail = locationDetail; }

    public String getCapacity() { return capacity; }
    public void setCapacity(String capacity) { this.capacity = capacity; }

    public LocalDate getInstallationDate() { return installationDate; }
    public void setInstallationDate(LocalDate installationDate) { this.installationDate = installationDate; }

    public LocalDate getExpiryDate() { return expiryDate; }
    public void setExpiryDate(LocalDate expiryDate) { this.expiryDate = expiryDate; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getVendor() { return vendor; }
    public void setVendor(String vendor) { this.vendor = vendor; }

    public String getQrCode() { return qrCode; }
    public void setQrCode(String qrCode) { this.qrCode = qrCode; }

    public LocalDate getLastInspectionDate() { return lastInspectionDate; }
    public void setLastInspectionDate(LocalDate lastInspectionDate) { this.lastInspectionDate = lastInspectionDate; }

    public LocalDate getNextInspectionDate() { return nextInspectionDate; }
    public void setNextInspectionDate(LocalDate nextInspectionDate) { this.nextInspectionDate = nextInspectionDate; }
}
