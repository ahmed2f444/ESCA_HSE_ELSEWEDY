package com.esca.hse.repository;

import com.esca.hse.model.FireEquipment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface FireEquipmentRepository extends JpaRepository<FireEquipment, String> {
}
