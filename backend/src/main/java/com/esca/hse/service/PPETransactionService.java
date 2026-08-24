package com.esca.hse.service;

import com.esca.hse.model.PPEItem;
import com.esca.hse.model.PPETransaction;
import com.esca.hse.platform.EntityIdUtils;
import com.esca.hse.repository.PPEItemRepository;
import com.esca.hse.repository.PPETransactionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.*;

@Service
public class PPETransactionService {

    private static final Set<String> VALID_TYPES = Set.of("ISSUE", "RETURN", "ADJUSTMENT", "DISPOSAL");

    private static final RowMapper<PPETransaction> ROW_MAPPER = (rs, rowNum) -> {
        PPETransaction tx = new PPETransaction();
        int id = rs.getInt("transaction_id");
        int ppeId = rs.getInt("ppe_item_id");
        int empId = rs.getInt("employee_id");

        tx.setTransactionId(EntityIdUtils.formatId("TXN", id));

        PPEItem item = new PPEItem();
        item.setPpeItemId(EntityIdUtils.formatId("PPE", ppeId));
        item.setItemCode(rs.getString("item_code"));
        item.setNameAr(rs.getString("item_name"));
        tx.setPpeItem(item);

        String empName = rs.getString("employee_name");
        tx.setEmployeeId(empName != null ? empName : EntityIdUtils.formatId("EMP", empId));

        tx.setTransactionType(rs.getString("type_name"));
        tx.setQuantity(rs.getInt("quantity"));

        Timestamp ts = rs.getTimestamp("transacted_at");
        if (ts != null) {
            tx.setTransactedAt(ts.toLocalDateTime());
        }

        tx.setProcessedBy(String.valueOf(rs.getInt("processed_by")));
        tx.setReason(rs.getString("reason"));
        tx.setPermitId(rs.getString("permit_id"));
        tx.setNotes(rs.getString("notes"));
        return tx;
    };

    private final PPETransactionRepository repository;
    private final PPEItemRepository ppeItemRepository;
    private final NamedParameterJdbcTemplate jdbc;

    public PPETransactionService(
            @Autowired(required = false) PPETransactionRepository repository,
            @Autowired(required = false) PPEItemRepository ppeItemRepository,
            @Autowired(required = false) NamedParameterJdbcTemplate jdbc) {
        this.repository = repository;
        this.ppeItemRepository = ppeItemRepository;
        this.jdbc = jdbc;
    }

    // ─────────────────────────────── Reads ───────────────────────────────

    public List<PPETransaction> getAllTransactions() {
        if (jdbc != null) {
            try {
                String sql = "SELECT pt.transaction_id, pt.ppe_item_id, pt.employee_id, pt.transaction_type_id, " +
                        "pt.quantity, pt.transacted_at, pt.processed_by, pt.reason, pt.permit_id, pt.notes, " +
                        "COALESCE(ptt.name, 'ISSUE') as type_name, " +
                        "p.name_ar as item_name, p.item_code, " +
                        "e.display_name as employee_name " +
                        "FROM ppe_transactions pt " +
                        "LEFT JOIN ppe_transaction_types ptt ON pt.transaction_type_id = ptt.ppe_transaction_type_id " +
                        "LEFT JOIN ppe_inventory p ON pt.ppe_item_id = p.ppe_item_id " +
                        "LEFT JOIN employees e ON pt.employee_id = e.employee_id " +
                        "ORDER BY pt.transaction_id DESC";

                return jdbc.query(sql, ROW_MAPPER);
            } catch (Exception ignored) {
            }
        }
        if (repository != null) {
            return repository.findAll();
        }
        return Collections.emptyList();
    }

    public PPETransaction getTransactionById(String id) {
        if (repository != null) {
            return repository.findById(id).orElse(null);
        }
        return null;
    }

    public List<PPETransaction> getTransactionsForItem(String ppeItemId) {
        if (repository != null) {
            return repository.findByPpeItem_PpeItemId(ppeItemId);
        }
        return Collections.emptyList();
    }

    public Map<String, Object> getSummary() {
        List<PPETransaction> list = getAllTransactions();
        Map<String, Object> summary = new LinkedHashMap<>();

        long totalCount = list.size();
        long issueCount = list.stream().filter(t -> "ISSUE".equalsIgnoreCase(t.getTransactionType())).count();
        long returnCount = list.stream().filter(t -> "RETURN".equalsIgnoreCase(t.getTransactionType())).count();
        int totalIssuedQty = list.stream()
                .filter(t -> "ISSUE".equalsIgnoreCase(t.getTransactionType()) && t.getQuantity() != null)
                .mapToInt(PPETransaction::getQuantity)
                .sum();
        int totalReturnedQty = list.stream()
                .filter(t -> "RETURN".equalsIgnoreCase(t.getTransactionType()) && t.getQuantity() != null)
                .mapToInt(PPETransaction::getQuantity)
                .sum();

        summary.put("totalTransactions", totalCount);
        summary.put("issueCount", issueCount);
        summary.put("returnCount", returnCount);
        summary.put("totalIssuedQuantity", totalIssuedQty);
        summary.put("totalReturnedQuantity", totalReturnedQty);
        return summary;
    }

    // ─────────────────────────────── Writes ──────────────────────────────

    @Transactional
    public PPETransaction createTransaction(PPETransaction transaction) {
        validateTransactionType(transaction.getTransactionType());

        if (jdbc != null) {
            try {
                String rawItemId = transaction.getPpeItem() != null ? transaction.getPpeItem().getPpeItemId() : "1";
                int ppeItemId = EntityIdUtils.parseNumericId(rawItemId);
                
                // Validate/resolve ppeItemId
                try {
                    Integer validPpeId = jdbc.queryForObject(
                            "SELECT ppe_item_id FROM ppe_inventory WHERE ppe_item_id = :id LIMIT 1",
                            Map.of("id", ppeItemId), Integer.class);
                    if (validPpeId != null) ppeItemId = validPpeId;
                } catch (Exception e) {
                    try {
                        Integer validPpeId = jdbc.queryForObject(
                                "SELECT ppe_item_id FROM ppe_inventory WHERE item_code = :code LIMIT 1",
                                Map.of("code", rawItemId), Integer.class);
                        if (validPpeId != null) ppeItemId = validPpeId;
                    } catch (Exception ignored) {}
                }

                // Validate/resolve employeeId
                int empId = EntityIdUtils.parseNumericId(transaction.getEmployeeId());
                try {
                    Integer validEmpId = jdbc.queryForObject(
                            "SELECT employee_id FROM employees WHERE employee_id = :id LIMIT 1",
                            Map.of("id", empId), Integer.class);
                    if (validEmpId != null) empId = validEmpId;
                    else empId = 1;
                } catch (Exception e) {
                    empId = 1;
                }

                int typeId = "RETURN".equalsIgnoreCase(transaction.getTransactionType()) ? 2 : 1;
                int qty = transaction.getQuantity() != null ? transaction.getQuantity() : 1;
                LocalDateTime ts = transaction.getTransactedAt() != null ? transaction.getTransactedAt() : LocalDateTime.now();
                String reason = transaction.getReason() != null ? transaction.getReason() : "صرف دوري";
                String notes = transaction.getNotes() != null ? transaction.getNotes() : "";

                // Check stock balance if issuing
                if (typeId == 1) {
                    Integer currentBal = jdbc.queryForObject(
                            "SELECT balance_qty FROM ppe_inventory WHERE ppe_item_id = :id",
                            Map.of("id", ppeItemId), Integer.class);
                    if (currentBal != null && currentBal < qty) {
                        throw new IllegalArgumentException("Insufficient stock for item PPE-" + ppeItemId +
                                ". Available: " + currentBal + ", requested: " + qty);
                    }
                    jdbc.update("UPDATE ppe_inventory SET balance_qty = balance_qty - :qty WHERE ppe_item_id = :id",
                            Map.of("qty", qty, "id", ppeItemId));
                } else if (typeId == 2) {
                    jdbc.update("UPDATE ppe_inventory SET balance_qty = balance_qty + :qty WHERE ppe_item_id = :id",
                            Map.of("qty", qty, "id", ppeItemId));
                }

                String sql = "INSERT INTO ppe_transactions (ppe_item_id, employee_id, transaction_type_id, " +
                        "quantity, transacted_at, processed_by, reason, permit_id, notes) " +
                        "VALUES (:ppe_item_id, :employee_id, :type_id, :quantity, :transacted_at, 1, :reason, NULL, :notes)";

                MapSqlParameterSource params = new MapSqlParameterSource()
                        .addValue("ppe_item_id", ppeItemId)
                        .addValue("employee_id", empId)
                        .addValue("type_id", typeId)
                        .addValue("quantity", qty)
                        .addValue("transacted_at", Timestamp.valueOf(ts))
                        .addValue("reason", reason)
                        .addValue("notes", notes);

                KeyHolder keyHolder = new GeneratedKeyHolder();
                jdbc.update(sql, params, keyHolder, new String[]{"transaction_id"});
                Number newKey = keyHolder.getKey();
                int newId = newKey != null ? newKey.intValue() : 100;
                transaction.setTransactionId(EntityIdUtils.formatId("TXN", newId));
                return transaction;
            } catch (IllegalArgumentException e) {
                throw e;
            } catch (Exception ignored) {
            }
        }

        if (repository != null && ppeItemRepository != null) {
            PPEItem managedItem = resolveAndAdjustStock(transaction);
            transaction.setPpeItem(managedItem);
            ppeItemRepository.save(managedItem);
            return repository.save(transaction);
        }

        return transaction;
    }

    @Transactional
    public PPETransaction updateTransaction(String id, PPETransaction updated) {
        if (repository != null && ppeItemRepository != null) {
            PPETransaction existing = repository.findById(id)
                    .orElseThrow(() -> new NoSuchElementException("Transaction not found: " + id));

            validateTransactionType(updated.getTransactionType());

            PPEItem oldItem = safeFetchItem(existing);
            if (oldItem != null) {
                reverseEffect(existing, oldItem);
                ppeItemRepository.save(oldItem);
            }

            PPEItem newItem = resolveAndAdjustStock(updated);
            updated.setPpeItem(newItem);
            ppeItemRepository.save(newItem);

            updated.setTransactionId(id);
            return repository.save(updated);
        }
        return updated;
    }

    @Transactional
    public void deleteTransaction(String id) {
        if (repository != null) {
            PPETransaction tx = repository.findById(id).orElse(null);
            if (tx != null) {
                PPEItem item = safeFetchItem(tx);
                if (item != null) {
                    reverseEffect(tx, item);
                    if (ppeItemRepository != null) ppeItemRepository.save(item);
                }
                repository.delete(tx);
            }
        }
    }

    // ─────────────────────────────── Helpers ─────────────────────────────

    private PPEItem safeFetchItem(PPETransaction tx) {
        if (tx == null || tx.getPpeItem() == null || tx.getPpeItem().getPpeItemId() == null) {
            return null;
        }
        if (ppeItemRepository == null) return null;
        return ppeItemRepository.findByPpeItemIdIgnoreCase(tx.getPpeItem().getPpeItemId())
                .or(() -> ppeItemRepository.findById(tx.getPpeItem().getPpeItemId()))
                .orElse(null);
    }

    private PPEItem resolveAndAdjustStock(PPETransaction tx) {
        String itemId = tx.getPpeItem() != null ? tx.getPpeItem().getPpeItemId() : null;
        if (itemId == null) {
            throw new IllegalArgumentException("Transaction must reference a valid PPE item");
        }

        PPEItem item = null;
        if (ppeItemRepository != null) {
            item = ppeItemRepository.findByPpeItemIdIgnoreCase(itemId)
                    .or(() -> ppeItemRepository.findById(itemId))
                    .orElse(null);
        }

        if (item == null) {
            throw new NoSuchElementException("PPE Item not found: " + itemId);
        }

        int currentBalance = item.getBalanceQty() != null ? item.getBalanceQty() : 0;
        int qty = tx.getQuantity() != null ? tx.getQuantity() : 0;

        if ("ISSUE".equalsIgnoreCase(tx.getTransactionType())) {
            if (currentBalance < qty) {
                throw new IllegalStateException(
                        "Insufficient stock for item " + itemId +
                                ". Available: " + currentBalance + ", requested: " + qty);
            }
            item.setBalanceQty(currentBalance - qty);
        } else if ("RETURN".equalsIgnoreCase(tx.getTransactionType())) {
            item.setBalanceQty(currentBalance + qty);
        }

        return item;
    }

    private void reverseEffect(PPETransaction tx, PPEItem item) {
        int currentBalance = item.getBalanceQty() != null ? item.getBalanceQty() : 0;
        int qty = tx.getQuantity() != null ? tx.getQuantity() : 0;

        if ("ISSUE".equalsIgnoreCase(tx.getTransactionType())) {
            item.setBalanceQty(currentBalance + qty);
        } else if ("RETURN".equalsIgnoreCase(tx.getTransactionType())) {
            item.setBalanceQty(Math.max(0, currentBalance - qty));
        }
    }

    private void validateTransactionType(String type) {
        if (type == null || !VALID_TYPES.contains(type.toUpperCase())) {
            throw new IllegalArgumentException(
                    "transactionType must be exactly 'ISSUE' or 'RETURN', got: " + type);
        }
    }
}
