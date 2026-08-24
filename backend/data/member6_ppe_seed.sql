-- Member 6 sample PPE items (for validation alongside fire equipment)

INSERT INTO ppe_inventory (
    ppe_item_id,
    item_code,
    name_ar,
    category_id,
    unit,
    balance_qty,
    reorder_threshold,
    monthly_consumption,
    supplier,
    storage_zone_id
) VALUES
    ('PPE-1001', 'HEAD-001', 'Safety Helmet', 'HEAD', 'Unit', 42, 18, 120, 'Safety Supply Co', 'ZONE-A'),
    ('PPE-1002', 'HANDS-002', 'Work Gloves', 'HANDS', 'Pair', 8, 12, 90, 'Safety Supply Co', 'ZONE-A'),
    ('PPE-1003', 'EYES-003', 'Safety Goggles', 'EYES', 'Pair', 11, 10, 60, 'Vision First Ltd', 'ZONE-B'),
    ('PPE-1004', 'FEET-004', 'Safety Boots', 'FEET', 'Pair', 26, 14, 75, 'Industrial Gear Ltd', 'ZONE-C'),
    ('PPE-1005', 'FACE-005', 'Face Shield', 'FACE', 'Unit', 6, 12, 70, 'Protective Gear Co', 'ZONE-D'),
    ('PPE-1006', 'HEAR-006', 'Ear Plugs', 'HEARING', 'Pack', 35, 16, 100, 'Hearing Guard Ltd', 'ZONE-E'),
    ('PPE-1007', 'RESP-007', 'Respiratory Mask', 'RESPIRATORY', 'Unit', 7, 10, 80, 'Air Safe Industries', 'ZONE-F'),
    ('PPE-1008', 'BODY-008', 'Protective Coverall', 'BODY', 'Unit', 13, 12, 55, 'Safety Supply Co', 'ZONE-G'),
    ('PPE-1009', 'HEAD-009', 'Hard Hat', 'HEAD', 'Unit', 20, 15, 45, 'Industrial Gear Ltd', 'ZONE-A'),
    ('PPE-1010', 'HANDS-010', 'Cut Resistant Gloves', 'HANDS', 'Pair', 30, 18, 110, 'Safety Supply Co', 'ZONE-B')
ON DUPLICATE KEY UPDATE
    category_id = VALUES(category_id),
    item_code = VALUES(item_code),
    name_ar = VALUES(name_ar);
