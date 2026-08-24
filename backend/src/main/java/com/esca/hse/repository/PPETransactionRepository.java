package com.esca.hse.repository;

import com.esca.hse.model.PPETransaction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PPETransactionRepository extends JpaRepository<PPETransaction, String> {
    List<PPETransaction> findByPpeItem_PpeItemId(String ppeItemId);
}
