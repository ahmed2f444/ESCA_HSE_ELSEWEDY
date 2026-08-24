-- Member 6: Fire Inspections Log sample data

INSERT INTO fire_inspections (id, equipment_id, inspection_date, inspector_name, status, notes) VALUES
('INSP-001', 'FE-1001', '2026-08-01', 'Inspector Mohamed', 'PASSED', 'Pressure gauge green, safety seal intact'),
('INSP-002', 'FE-1002', '2026-08-01', 'Inspector Mohamed', 'PASSED', 'Hose and nozzle clean, pin in place'),
('INSP-003', 'FE-1003', '2026-08-02', 'Inspector Ahmed', 'PASSED', 'Weight checked, discharge horn clear'),
('INSP-004', 'FE-1004', '2026-07-28', 'Inspector Ahmed', 'MAINTENANCE_REQUIRED', 'Pressure dropped to yellow band, scheduled for recharge'),
('INSP-005', 'FE-1005', '2026-08-03', 'Inspector Mohamed', 'PASSED', 'Cabinet clean, glass undamaged')
ON DUPLICATE KEY UPDATE
    equipment_id = VALUES(equipment_id),
    inspection_date = VALUES(inspection_date),
    inspector_name = VALUES(inspector_name),
    status = VALUES(status),
    notes = VALUES(notes);
