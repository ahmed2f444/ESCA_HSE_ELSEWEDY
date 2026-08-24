INSERT INTO ppe_transactions (transaction_id, ppe_item_id, employee_id, transaction_type, quantity, transaction_at, processed_by, reason, permit_id, notes) VALUES
('TXN-2025-001', 'PPE-1001', 'EMP-5401', 'ISSUE', 5, '2026-08-17 09:30:00', 'Safety Officer Ahmed', 'Routine issue', 'PERMIT-2025-001', 'Regular site issue'),
('TXN-2025-002', 'PPE-1002', 'EMP-5402', 'ISSUE', 3, '2026-08-16 14:15:00', 'Safety Officer Ahmed', 'Replacement', 'PERMIT-2025-002', 'Damaged item replacement'),
('TXN-2025-003', 'PPE-1003', 'EMP-5403', 'RETURN', 2, '2026-08-15 10:45:00', 'Warehouse Supervisor', 'Damaged item return', NULL, 'Returned due to wear and tear'),
('TXN-2025-004', 'PPE-1004', 'EMP-5401', 'ISSUE', 4, '2026-08-14 11:20:00', 'Safety Officer Ahmed', 'Routine issue', 'PERMIT-2025-003', 'Daily work issue'),
('TXN-2025-005', 'PPE-1005', 'EMP-5404', 'ISSUE', 6, '2026-08-13 08:00:00', 'Site Manager', 'Project startup', 'PERMIT-2025-004', 'New project personnel onboarding'),
('TXN-2025-006', 'PPE-1006', 'EMP-5402', 'RETURN', 1, '2026-08-12 15:30:00', 'Warehouse Supervisor', 'Inventory audit', NULL, 'Excess stock return'),
('TXN-2025-007', 'PPE-1007', 'EMP-5405', 'ISSUE', 2, '2026-08-11 13:45:00', 'Safety Officer Ahmed', 'Routine issue', 'PERMIT-2025-005', 'New hire issue'),
('TXN-2025-008', 'PPE-1008', 'EMP-5401', 'ISSUE', 8, '2026-08-10 09:00:00', 'Site Manager', 'Special operation', 'PERMIT-2025-006', 'Emergency response team setup'),
('TXN-2025-009', 'PPE-1009', 'EMP-5403', 'RETURN', 3, '2026-08-09 16:20:00', 'Warehouse Supervisor', 'End of contract', NULL, 'Employee contract termination'),
('TXN-2025-010', 'PPE-1010', 'EMP-5406', 'ISSUE', 10, '2026-08-08 10:15:00', 'Safety Officer Ahmed', 'Bulk issue', 'PERMIT-2025-007', 'Site expansion - new workers');
