-- Member 6: Fire Equipment Registry sample data
-- Use this in MySQL after the application creates the table automatically.

INSERT INTO fire_equipment (
    equipment_id,
    asset_type_id,
    subtype,
    department_id,
    zone_id,
    location_detail,
    capacity,
    installation_date,
    expiry_date,
    status,
    vendor,
    qr_code,
    last_inspection_date,
    next_inspection_date
) VALUES
    ('FE-1001', 'CO2', 'Portable Extinguisher', 'DEPT-UTIL', 'ZONE-A', 'Boiler Room', '6 kg', '2023-05-20', '2028-05-20', 'ACTIVE', 'Kidde Safety', 'QR-FE-1001', '2026-07-15', '2027-07-15'),
    ('FE-1002', 'FOAM', 'Mobile Foam Extinguisher', 'DEPT-WH', 'ZONE-B', 'Warehouse A', '9 L', '2022-11-08', '2027-11-08', 'ACTIVE', 'Jactone Fire Systems', 'QR-FE-1002', '2026-06-10', '2026-11-10'),
    ('FE-1003', 'WATER', 'Stored Pressure Extinguisher', 'DEPT-OPS', 'ZONE-C', 'Main Gate', '9 L', '2024-02-14', '2029-02-14', 'ACTIVE', 'Chubb Fire & Security', 'QR-FE-1003', '2026-08-01', '2027-08-01'),
    ('FE-1004', 'HYDRANT', 'Landing Valve', 'DEPT-OPS', 'ZONE-D', 'Plant Yard', '65 mm', '2021-09-30', '2031-09-30', 'MAINTENANCE', 'Johnson Controls', 'QR-FE-1004', '2025-12-01', '2026-09-01'),
    ('FE-1005', 'POWDER', 'Dry Chemical Extinguisher', 'DEPT-ELEC', 'ZONE-E', 'Electrical Room', '6 kg', '2023-07-11', '2028-07-11', 'ACTIVE', 'Amerex Corporation', 'QR-FE-1005', '2026-07-28', '2027-07-28');
