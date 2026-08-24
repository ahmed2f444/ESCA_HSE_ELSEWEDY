package com.esca.hse.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Entity
@Table(name = "ppe_transactions")
public class PPETransaction {

    @Id
    private String transactionId;

    @ManyToOne
    @JoinColumn(name = "ppe_item_id")
    private PPEItem ppeItem;

    @NotBlank(message = "Employee ID is required")
    @Column(name = "employee_id")
    private String employeeId;

    @NotBlank(message = "Transaction type is required (ISSUE or RETURN)")
    private String transactionType;

    @NotNull(message = "Quantity is required")
    @Min(value = 1, message = "Quantity must be at least 1")
    private Integer quantity;

    @Column(name = "transaction_at")
    private LocalDateTime transactedAt;
    private String processedBy;
    private String reason;
    private String permitId;
    private String notes;

    public PPETransaction() {
    }

    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }

    public PPEItem getPpeItem() { return ppeItem; }
    public void setPpeItem(PPEItem ppeItem) { this.ppeItem = ppeItem; }

    public String getEmployeeId() { return employeeId; }
    public void setEmployeeId(String employeeId) { this.employeeId = employeeId; }

    public String getTransactionType() { return transactionType; }
    public void setTransactionType(String transactionType) { this.transactionType = transactionType; }

    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }

    public LocalDateTime getTransactedAt() { return transactedAt; }
    public void setTransactedAt(LocalDateTime transactedAt) { this.transactedAt = transactedAt; }

    public String getProcessedBy() { return processedBy; }
    public void setProcessedBy(String processedBy) { this.processedBy = processedBy; }

    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }

    public String getPermitId() { return permitId; }
    public void setPermitId(String permitId) { this.permitId = permitId; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
}
