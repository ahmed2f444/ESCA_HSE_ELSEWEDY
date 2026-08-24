package com.esca.hse;

import com.esca.hse.model.PPEItem;
import com.esca.hse.model.PPETransaction;
import com.esca.hse.repository.PPEItemRepository;
import com.esca.hse.repository.PPETransactionRepository;
import com.esca.hse.service.PPETransactionService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for PPETransactionService.
 * All JPA repositories are mocked — no database required.
 */
@ExtendWith(MockitoExtension.class)
class PPETransactionServiceTest {

    @Mock
    private PPETransactionRepository transactionRepository;

    @Mock
    private PPEItemRepository ppeItemRepository;

    @InjectMocks
    private PPETransactionService service;

    private PPEItem sampleItem;
    private PPETransaction issueTransaction;
    private PPETransaction returnTransaction;

    @BeforeEach
    void setUp() {
        sampleItem = new PPEItem();
        sampleItem.setPpeItemId("PPE-001");
        sampleItem.setItemCode("HELM-01");
        sampleItem.setNameAr("Safety Helmet");
        sampleItem.setCategoryId("HEAD_PROTECTION");
        sampleItem.setUnit("pcs");
        sampleItem.setBalanceQty(50);
        sampleItem.setReorderThreshold(10);
        sampleItem.setMonthlyConsumption(5);

        PPEItem ref = new PPEItem();
        ref.setPpeItemId("PPE-001");

        issueTransaction = new PPETransaction();
        issueTransaction.setTransactionId("TXN-001");
        issueTransaction.setPpeItem(ref);
        issueTransaction.setTransactionType("ISSUE");
        issueTransaction.setQuantity(10);
        issueTransaction.setEmployeeId("EMP-100");

        returnTransaction = new PPETransaction();
        returnTransaction.setTransactionId("TXN-002");
        returnTransaction.setPpeItem(ref);
        returnTransaction.setTransactionType("RETURN");
        returnTransaction.setQuantity(5);
        returnTransaction.setEmployeeId("EMP-100");
    }

    // ──────────────────────────── Happy paths ────────────────────────────

    @Test
    @DisplayName("ISSUE transaction deducts quantity from PPE item stock")
    void issueTransaction_deductsStock() {
        when(ppeItemRepository.findByPpeItemIdIgnoreCase("PPE-001")).thenReturn(Optional.of(sampleItem));
        when(ppeItemRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(transactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        service.createTransaction(issueTransaction);

        // balanceQty should go from 50 → 40
        assertThat(sampleItem.getBalanceQty()).isEqualTo(40);
        verify(ppeItemRepository).save(sampleItem);
        verify(transactionRepository).save(issueTransaction);
    }

    @Test
    @DisplayName("RETURN transaction adds quantity back to PPE item stock")
    void returnTransaction_addsStock() {
        when(ppeItemRepository.findByPpeItemIdIgnoreCase("PPE-001")).thenReturn(Optional.of(sampleItem));
        when(ppeItemRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));
        when(transactionRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        service.createTransaction(returnTransaction);

        // balanceQty should go from 50 → 55
        assertThat(sampleItem.getBalanceQty()).isEqualTo(55);
        verify(ppeItemRepository).save(sampleItem);
    }

    @Test
    @DisplayName("DELETE transaction reverses the ISSUE inventory effect")
    void deleteIssueTransaction_reversesStock() {
        when(transactionRepository.findById("TXN-001")).thenReturn(Optional.of(issueTransaction));
        when(ppeItemRepository.findByPpeItemIdIgnoreCase("PPE-001")).thenReturn(Optional.of(sampleItem));
        when(ppeItemRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        service.deleteTransaction("TXN-001");

        // Reversing ISSUE of 10 → balanceQty goes from 50 → 60
        assertThat(sampleItem.getBalanceQty()).isEqualTo(60);
        verify(transactionRepository).delete(issueTransaction);
    }

    // ──────────────────────────── Failure paths ──────────────────────────

    @Test
    @DisplayName("ISSUE with quantity exceeding stock throws IllegalStateException")
    void issueTransaction_insufficientStock_throwsException() {
        sampleItem.setBalanceQty(5);   // only 5 in stock
        issueTransaction.setQuantity(10);  // trying to issue 10

        when(ppeItemRepository.findByPpeItemIdIgnoreCase("PPE-001")).thenReturn(Optional.of(sampleItem));

        assertThatThrownBy(() -> service.createTransaction(issueTransaction))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("Insufficient stock");

        // Item should NOT be saved
        verify(ppeItemRepository, never()).save(any());
        verify(transactionRepository, never()).save(any());
    }

    @Test
    @DisplayName("Invalid transactionType throws IllegalArgumentException")
    void invalidTransactionType_throwsException() {
        issueTransaction.setTransactionType("BORROW");

        assertThatThrownBy(() -> service.createTransaction(issueTransaction))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("transactionType must be exactly");
    }

    @Test
    @DisplayName("Transaction with null type throws IllegalArgumentException")
    void nullTransactionType_throwsException() {
        issueTransaction.setTransactionType(null);

        assertThatThrownBy(() -> service.createTransaction(issueTransaction))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
