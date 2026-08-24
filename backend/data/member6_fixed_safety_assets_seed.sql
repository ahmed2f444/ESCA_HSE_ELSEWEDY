-- Member 6: Fixed Safety Assets sample data

INSERT INTO fixed_safety_assets (id, asset_name, asset_type, zone_id, location_detail, status) VALUES
('FSA-001', 'Emergency Eyewash Station 1', 'EYEWASH_STATION', 'ZN-CHEM', 'Chemical Storage Bay entrance', 'OPERATIONAL'),
('FSA-002', 'Emergency Body Drench Shower', 'EMERGENCY_SHOWER', 'ZN-CHEM', 'Chemical mixing floor', 'OPERATIONAL'),
('FSA-003', 'Master LOTO Station', 'LOTO_STATION', 'ZN-M01', 'Maintenance workshop tool room', 'OPERATIONAL'),
('FSA-004', 'Automated External Defibrillator (AED)', 'AED', 'ZN-A1', 'Assembly Line A Main Corridor', 'OPERATIONAL'),
('FSA-005', 'Emergency Exit Push Bar Door 1', 'EMERGENCY_EXIT', 'ZN-B1', 'Warehouse West Exit', 'OPERATIONAL'),
('FSA-006', 'Secondary Eyewash Unit', 'EYEWASH_STATION', 'ZN-M01', 'Battery charging area', 'UNDER_MAINTENANCE')
ON DUPLICATE KEY UPDATE
    asset_name = VALUES(asset_name),
    asset_type = VALUES(asset_type),
    zone_id = VALUES(zone_id),
    location_detail = VALUES(location_detail),
    status = VALUES(status);
