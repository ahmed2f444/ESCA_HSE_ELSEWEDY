package com.esca.hse.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import jakarta.validation.constraints.NotBlank;

@Entity
@Table(name = "fixed_safety_assets")
public class FixedSafetyAsset {

    @Id
    @Column(name = "id")
    private String id;

    @NotBlank(message = "Asset name is required")
    @Column(name = "asset_name")
    private String assetName;

    @NotBlank(message = "Asset type is required (e.g. EYEWASH_STATION, EMERGENCY_SHOWER, LOTO_STATION, AED, EMERGENCY_EXIT)")
    @Column(name = "asset_type")
    private String assetType;

    @NotBlank(message = "Zone ID is required")
    @Column(name = "zone_id")
    private String zoneId;

    @Column(name = "location_detail")
    private String locationDetail;

    @NotBlank(message = "Status is required (e.g. OPERATIONAL, DEFECTIVE, UNDER_MAINTENANCE)")
    @Column(name = "status")
    private String status;

    public FixedSafetyAsset() {
    }

    public FixedSafetyAsset(String id, String assetName, String assetType, String zoneId, String locationDetail, String status) {
        this.id = id;
        this.assetName = assetName;
        this.assetType = assetType;
        this.zoneId = zoneId;
        this.locationDetail = locationDetail;
        this.status = status;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getAssetName() { return assetName; }
    public void setAssetName(String assetName) { this.assetName = assetName; }

    public String getAssetType() { return assetType; }
    public void setAssetType(String assetType) { this.assetType = assetType; }

    public String getZoneId() { return zoneId; }
    public void setZoneId(String zoneId) { this.zoneId = zoneId; }

    public String getLocationDetail() { return locationDetail; }
    public void setLocationDetail(String locationDetail) { this.locationDetail = locationDetail; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
