package com.esca.hse.service;

import com.esca.hse.model.PPEItem;
import com.esca.hse.platform.EntityIdUtils;
import com.esca.hse.repository.PPEItemRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class PPEItemService {

    private static final RowMapper<PPEItem> ROW_MAPPER = (rs, rowNum) -> {
        PPEItem item = new PPEItem();
        int id = rs.getInt("ppe_item_id");
        item.setPpeItemId(EntityIdUtils.formatId("PPE", id));
        item.setItemCode(rs.getString("item_code"));
        item.setNameAr(rs.getString("name_ar"));
        item.setCategoryId(rs.getString("category"));
        item.setUnit(rs.getString("unit"));
        item.setBalanceQty(rs.getInt("balance_qty"));
        item.setReorderThreshold(rs.getInt("reorder_threshold"));
        item.setMonthlyConsumption(rs.getInt("monthly_consumption"));
        item.setSupplier(rs.getString("supplier"));
        item.setStorageZoneId(rs.getString("zone_name"));
        return item;
    };

    private final PPEItemRepository repository;
    private final NamedParameterJdbcTemplate jdbc;

    public PPEItemService(
            @Autowired(required = false) PPEItemRepository repository,
            @Autowired(required = false) NamedParameterJdbcTemplate jdbc) {
        this.repository = repository;
        this.jdbc = jdbc;
    }

    public List<PPEItem> getAllItems() {
        if (jdbc != null) {
            try {
                String sql = "SELECT p.ppe_item_id, p.item_code, p.name_ar, p.category, p.unit, " +
                        "p.balance_qty, p.reorder_threshold, p.monthly_consumption, " +
                        "p.supplier, p.storage_zone_id, p.stock_status, " +
                        "COALESCE(z.name_ar, 'Zone A') as zone_name " +
                        "FROM ppe_inventory p " +
                        "LEFT JOIN zones z ON p.storage_zone_id = z.zone_id " +
                        "ORDER BY p.ppe_item_id ASC";

                return jdbc.query(sql, ROW_MAPPER);
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            return repository.findAll();
        }
        return Collections.emptyList();
    }

    public PPEItem getItemById(String id) {
        if (id == null) return null;
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(id);
                String sql = "SELECT p.ppe_item_id, p.item_code, p.name_ar, p.category, p.unit, " +
                        "p.balance_qty, p.reorder_threshold, p.monthly_consumption, " +
                        "p.supplier, p.storage_zone_id, p.stock_status, " +
                        "COALESCE(z.name_ar, 'Zone A') as zone_name " +
                        "FROM ppe_inventory p " +
                        "LEFT JOIN zones z ON p.storage_zone_id = z.zone_id " +
                        "WHERE p.ppe_item_id = :numId OR p.item_code = :rawId LIMIT 1";

                List<PPEItem> list = jdbc.query(sql, Map.of("numId", numId, "rawId", id), ROW_MAPPER);
                if (!list.isEmpty()) return list.get(0);
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            return repository.findById(id).orElse(null);
        }
        return null;
    }

    public PPEItem createItem(PPEItem item) {
        if (jdbc != null) {
            try {
                String code = item.getItemCode() != null ? item.getItemCode() : ("PPE-" + System.currentTimeMillis() % 10000);
                String name = item.getNameAr() != null ? item.getNameAr() : "معدة وقاية";
                String category = item.getCategoryId() != null ? item.getCategoryId() : "GENERAL";
                String unit = item.getUnit() != null ? item.getUnit() : "pcs";
                int balance = item.getBalanceQty() != null ? item.getBalanceQty() : 0;
                int threshold = item.getReorderThreshold() != null ? item.getReorderThreshold() : 0;
                int rate = item.getMonthlyConsumption() != null ? item.getMonthlyConsumption() : 1;
                String supplier = item.getSupplier() != null ? item.getSupplier() : "Safety Supply";
                int zoneId = 1;
                boolean stockStatus = balance >= threshold;

                String sql = "INSERT INTO ppe_inventory (item_code, name_ar, category, unit, balance_qty, " +
                        "reorder_threshold, monthly_consumption, supplier, storage_zone_id, stock_status) " +
                        "VALUES (:item_code, :name_ar, :category, :unit, :balance_qty, " +
                        ":reorder_threshold, :monthly_consumption, :supplier, :storage_zone_id, :stock_status)";

                MapSqlParameterSource params = new MapSqlParameterSource()
                        .addValue("item_code", code)
                        .addValue("name_ar", name)
                        .addValue("category", category)
                        .addValue("unit", unit)
                        .addValue("balance_qty", balance)
                        .addValue("reorder_threshold", threshold)
                        .addValue("monthly_consumption", rate)
                        .addValue("supplier", supplier)
                        .addValue("storage_zone_id", zoneId)
                        .addValue("stock_status", stockStatus ? 1 : 0);

                KeyHolder keyHolder = new GeneratedKeyHolder();
                jdbc.update(sql, params, keyHolder, new String[]{"ppe_item_id"});
                Number newKey = keyHolder.getKey();
                int newId = newKey != null ? newKey.intValue() : 100;
                item.setPpeItemId(EntityIdUtils.formatId("PPE", newId));
                return item;
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            return repository.save(item);
        }
        return item;
    }

    public PPEItem updateItem(String id, PPEItem updatedItem) {
        updatedItem.setPpeItemId(id);
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(id);
                String sql = "UPDATE ppe_inventory SET item_code = :code, name_ar = :name, category = :cat, " +
                        "unit = :unit, balance_qty = :balance, reorder_threshold = :threshold, " +
                        "monthly_consumption = :consumption, supplier = :supplier " +
                        "WHERE ppe_item_id = :numId";

                MapSqlParameterSource params = new MapSqlParameterSource()
                        .addValue("code", updatedItem.getItemCode())
                        .addValue("name", updatedItem.getNameAr())
                        .addValue("cat", updatedItem.getCategoryId())
                        .addValue("unit", updatedItem.getUnit())
                        .addValue("balance", updatedItem.getBalanceQty())
                        .addValue("threshold", updatedItem.getReorderThreshold())
                        .addValue("consumption", updatedItem.getMonthlyConsumption())
                        .addValue("supplier", updatedItem.getSupplier())
                        .addValue("numId", numId);

                int rows = jdbc.update(sql, params);
                if (rows > 0) return updatedItem;
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            if (!repository.existsById(id)) return null;
            return repository.save(updatedItem);
        }
        return updatedItem;
    }

    public List<PPEItem> getItemsBelowThreshold() {
        return getAllItems().stream()
                .filter(item -> "BELOW_THRESHOLD".equals(item.getStockStatus()))
                .toList();
    }

    public int getDaysUntilStockout(PPEItem item) {
        if (item == null || item.getBalanceQty() == null) {
            return -1;
        }

        Integer monthlyConsumption = item.getMonthlyConsumption();
        if (monthlyConsumption == null || monthlyConsumption <= 0) {
            return -1;
        }

        double dailyConsumption = monthlyConsumption / 30.0;
        if (dailyConsumption <= 0) {
            return -1;
        }

        return (int) Math.floor(item.getBalanceQty() / dailyConsumption);
    }

    public Map<String, Object> getSummary() {
        List<PPEItem> items = getAllItems();
        Map<String, Object> summary = new LinkedHashMap<>();

        int totalItems = items.size();
        int belowThreshold = 0;
        int lowStock = 0;
        int reorderWithin14Days = 0;

        for (PPEItem item : items) {
            if ("BELOW_THRESHOLD".equals(item.getStockStatus())) {
                belowThreshold++;
            }
            if ("LOW_STOCK".equals(item.getStockStatus())) {
                lowStock++;
            }

            int daysUntilStockout = getDaysUntilStockout(item);
            if (daysUntilStockout >= 0 && daysUntilStockout <= 14) {
                reorderWithin14Days++;
            }
        }

        int available = totalItems - belowThreshold - lowStock;
        summary.put("totalItems", totalItems);
        summary.put("belowThreshold", belowThreshold);
        summary.put("lowStock", lowStock);
        summary.put("available", available);
        summary.put("reorderWithin14Days", reorderWithin14Days);
        return summary;
    }

    public void deleteItem(String id) {
        if (jdbc != null) {
            try {
                int numId = EntityIdUtils.parseNumericId(id);
                jdbc.update("DELETE FROM ppe_inventory WHERE ppe_item_id = :numId", Map.of("numId", numId));
                return;
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            repository.deleteById(id);
        }
    }
}