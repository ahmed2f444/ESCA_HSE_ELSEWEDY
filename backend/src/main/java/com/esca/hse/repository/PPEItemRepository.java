package com.esca.hse.repository;

import com.esca.hse.model.PPEItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PPEItemRepository extends JpaRepository<PPEItem, String> {
    Optional<PPEItem> findByPpeItemIdIgnoreCase(String ppeItemId);
}