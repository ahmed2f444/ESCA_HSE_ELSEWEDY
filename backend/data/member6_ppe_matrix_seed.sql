-- Member 6: PPE Matrix Registry sample data
-- Defines mandatory safety gear requirements per industrial plant zone

INSERT INTO ppe_matrix (matrix_id, zone_id, ppe_item_id, required_flag, notes) VALUES
('PPM-001', 'ZN-A1', 'PPE-1001', 1, 'Minimum entry requirement for Zone A1'),
('PPM-002', 'ZN-A1', 'PPE-1002', 1, 'Minimum entry requirement for Zone A1'),
('PPM-003', 'ZN-A1', 'PPE-1004', 1, 'Minimum entry requirement for Zone A1'),
('PPM-004', 'ZN-A1', 'PPE-1006', 1, 'Hearing protection mandatory near heavy machinery'),
('PPM-005', 'ZN-A1', 'PPE-1008', 1, 'Protective coverall required on shopfloor'),
('PPM-006', 'ZN-A2', 'PPE-1001', 1, 'Hard hat required inside staging bay'),
('PPM-007', 'ZN-A2', 'PPE-1003', 1, 'Safety goggles for cutting and grinding'),
('PPM-008', 'ZN-A2', 'PPE-1010', 1, 'Cut resistant gloves required for handling sheet metal'),
('PPM-009', 'ZN-B1', 'PPE-1001', 1, 'Overhead crane hazard - helmet mandatory'),
('PPM-010', 'ZN-B1', 'PPE-1002', 1, 'Material handling gloves required'),
('PPM-011', 'ZN-B1', 'PPE-1004', 1, 'Steel-toe boots for warehouse transit'),
('PPM-012', 'ZN-M01', 'PPE-1001', 1, 'Maintenance area standard PPE'),
('PPM-013', 'ZN-M01', 'PPE-1002', 1, 'Oil-resistant work gloves'),
('PPM-014', 'ZN-M01', 'PPE-1005', 1, 'Face shield required for lathe and welding tasks'),
('PPM-015', 'ZN-M01', 'PPE-1007', 1, 'Respiratory mask for paint/solvent application'),
('PPM-016', 'ZN-U01', 'PPE-1001', 1, 'Utilities boiler room entry PPE'),
('PPM-017', 'ZN-U01', 'PPE-1004', 1, 'Insulated safety boots mandatory in power plant'),
('PPM-018', 'ZN-U01', 'PPE-1006', 1, 'Ear protection for generator room'),
('PPM-019', 'ZN-CHEM', 'PPE-1003', 1, 'Chemical splash goggles mandatory'),
('PPM-020', 'ZN-CHEM', 'PPE-1005', 1, 'Full face shield for acid/alkali transfers'),
('PPM-021', 'ZN-CHEM', 'PPE-1007', 1, 'Dual-cartridge organic vapor respirator'),
('PPM-022', 'ZN-CHEM', 'PPE-1008', 1, 'Chemical-resistant protective suit')
ON DUPLICATE KEY UPDATE
    zone_id = VALUES(zone_id),
    ppe_item_id = VALUES(ppe_item_id),
    required_flag = VALUES(required_flag),
    notes = VALUES(notes);
