package com.esca.hse.repository;

import com.esca.hse.model.PPEMatrix;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PPEMatrixRepository extends JpaRepository<PPEMatrix, String> {
    List<PPEMatrix> findByZoneId(String zoneId);
    List<PPEMatrix> findByZoneIdIgnoreCase(String zoneId);
    List<PPEMatrix> findByPpeItemId(String ppeItemId);
    List<PPEMatrix> findByPpeItemIdIgnoreCase(String ppeItemId);
    Optional<PPEMatrix> findByMatrixIdIgnoreCase(String matrixId);
}
