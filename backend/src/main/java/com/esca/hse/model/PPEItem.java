package com.esca.hse.model;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Transient;
import jakarta.persistence.Column;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@Entity
@Table(name = "ppe_inventory")
public class PPEItem {

    @Id
    @NotBlank(message = "PPE Item ID is required")
    private String ppeItemId;

    @NotBlank(message = "Item Code is required")
    private String itemCode;

    @NotBlank(message = "Name is required")
    private String nameAr;

    @NotBlank(message = "Category is required")
    @Column(name = "category")
    @JsonProperty("categoryId")   // Explicit name — works with both Jackson 2 and 3
    @JsonAlias({"category", "category_id"}) // Accept alternative keys from incoming JSON
    private String categoryId;

    @NotBlank(message = "Unit is required")
    private String unit;

    @NotNull(message = "Balance Qty is required")
    @Min(value = 0, message = "Balance Qty must be 0 or greater")
    private Integer balanceQty;

    @NotNull(message = "Reorder Threshold is required")
    @Min(value = 0, message = "Reorder Threshold must be 0 or greater")
    private Integer reorderThreshold;

    @NotNull(message = "Monthly Consumption is required")
    @Min(value = 0, message = "Monthly Consumption must be 0 or greater")
    private Integer monthlyConsumption;
    private String supplier;
    private String storageZoneId;
    public PPEItem() {
    }

    public String getPpeItemId() { return ppeItemId; }
    public void setPpeItemId(String ppeItemId) { this.ppeItemId = ppeItemId; }

    public String getItemCode() { return itemCode; }
    public void setItemCode(String itemCode) { this.itemCode = itemCode; }

    public String getNameAr() { return nameAr; }
    public void setNameAr(String nameAr) { this.nameAr = nameAr; }

    public String getCategoryId() { return categoryId; }
    public void setCategoryId(String categoryId) { this.categoryId = categoryId; }

    @JsonProperty("category")
    public String getCategory() { return categoryId; }
    @JsonProperty("category")
    public void setCategory(String category) { this.categoryId = category; }

    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }

    public Integer getBalanceQty() { return balanceQty; }
    public void setBalanceQty(Integer balanceQty) { this.balanceQty = balanceQty; }

    public Integer getReorderThreshold() { return reorderThreshold; }
    public void setReorderThreshold(Integer reorderThreshold) { this.reorderThreshold = reorderThreshold; }

    public Integer getMonthlyConsumption() { return monthlyConsumption; }
    public void setMonthlyConsumption(Integer monthlyConsumption) { this.monthlyConsumption = monthlyConsumption; }

    public String getSupplier() { return supplier; }
    public void setSupplier(String supplier) { this.supplier = supplier; }

    public String getStorageZoneId() { return storageZoneId; }
    public void setStorageZoneId(String storageZoneId) { this.storageZoneId = storageZoneId; }

    @Transient
    public String getStockStatus() {
        int currentBalance = balanceQty == null ? 0 : balanceQty;
        int threshold = reorderThreshold == null ? 0 : reorderThreshold;

        if (currentBalance < threshold) {
            return "BELOW_THRESHOLD";
        } else if (currentBalance <= threshold + 5) {
            return "LOW_STOCK";
        }
        return "AVAILABLE";
    }
}