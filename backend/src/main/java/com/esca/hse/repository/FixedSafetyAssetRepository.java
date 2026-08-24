package com.esca.hse.repository;

import com.esca.hse.model.FixedSafetyAsset;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface FixedSafetyAssetRepository extends JpaRepository<FixedSafetyAsset, String> {
    List<FixedSafetyAsset> findByZoneId(String zoneId);
    List<FixedSafetyAsset> findByZoneIdIgnoreCase(String zoneId);
    List<FixedSafetyAsset> findByAssetTypeIgnoreCase(String assetType);
    List<FixedSafetyAsset> findByStatusIgnoreCase(String status);
}
