CREATE TABLE IF NOT EXISTS departments (
    department_id VARCHAR(30) PRIMARY KEY,
    department_code VARCHAR(30) NOT NULL UNIQUE,
    department_name VARCHAR(160) NOT NULL,
    manager_employee_id VARCHAR(30),
    hse_contact_id VARCHAR(30),
    location VARCHAR(160),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zones (
    zone_id VARCHAR(30) PRIMARY KEY,
    zone_code VARCHAR(30) NOT NULL UNIQUE,
    zone_name VARCHAR(160) NOT NULL,
    department_id VARCHAR(30),
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    restricted_access BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_zones_department FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(30) PRIMARY KEY,
    employee_code VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(190),
    phone VARCHAR(40),
    job_title VARCHAR(120),
    department_id VARCHAR(30),
    manager_id VARCHAR(30),
    employment_type VARCHAR(30) DEFAULT 'EMPLOYEE',
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    hire_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employees_department FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS app_users (
    user_id VARCHAR(40) PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(160) NOT NULL,
    email VARCHAR(190),
    employee_id VARCHAR(30),
    role VARCHAR(40) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_employee FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id VARCHAR(40) PRIMARY KEY,
    incident_type VARCHAR(40) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    department_id VARCHAR(30),
    zone_id VARCHAR(30),
    reported_by VARCHAR(30),
    occurred_at TIMESTAMP NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    immediate_action TEXT,
    root_cause TEXT,
    lost_time_days INT NOT NULL DEFAULT 0,
    closed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_incidents_department FOREIGN KEY (department_id) REFERENCES departments(department_id),
    CONSTRAINT fk_incidents_zone FOREIGN KEY (zone_id) REFERENCES zones(zone_id)
);

CREATE TABLE IF NOT EXISTS jsa (
    jsa_id VARCHAR(40) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    activity VARCHAR(240) NOT NULL,
    department_id VARCHAR(30),
    zone_id VARCHAR(30),
    prepared_by VARCHAR(30),
    hazards TEXT,
    controls TEXT,
    required_ppe TEXT,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    approved_by VARCHAR(30),
    approved_at TIMESTAMP NULL,
    review_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permits (
    permit_id VARCHAR(40) PRIMARY KEY,
    permit_type VARCHAR(50) NOT NULL,
    department_id VARCHAR(30),
    zone_id VARCHAR(30),
    work_description TEXT NOT NULL,
    requester_id VARCHAR(30),
    issuer_id VARCHAR(30),
    executor_type VARCHAR(30),
    executor_name VARCHAR(160),
    start_at TIMESTAMP NOT NULL,
    expiry_at TIMESTAMP NOT NULL,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    jsa_id VARCHAR(40),
    status VARCHAR(30) NOT NULL DEFAULT 'REQUESTED',
    suspended_reason TEXT,
    actual_close_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_permits_department FOREIGN KEY (department_id) REFERENCES departments(department_id),
    CONSTRAINT fk_permits_zone FOREIGN KEY (zone_id) REFERENCES zones(zone_id),
    CONSTRAINT fk_permits_jsa FOREIGN KEY (jsa_id) REFERENCES jsa(jsa_id)
);

CREATE TABLE IF NOT EXISTS risk_register (
    risk_id VARCHAR(40) PRIMARY KEY,
    department_id VARCHAR(30),
    zone_id VARCHAR(30),
    hazard VARCHAR(240) NOT NULL,
    activity VARCHAR(240),
    likelihood INT NOT NULL,
    severity INT NOT NULL,
    inherent_score INT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    controls TEXT,
    residual_likelihood INT,
    residual_severity INT,
    residual_score INT,
    owner_id VARCHAR(30),
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    last_reviewed_at DATE,
    next_review_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inspections (
    inspection_id VARCHAR(40) PRIMARY KEY,
    inspection_type VARCHAR(60) NOT NULL,
    title VARCHAR(200) NOT NULL,
    department_id VARCHAR(30),
    zone_id VARCHAR(30),
    inspector_id VARCHAR(30),
    scheduled_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    score DECIMAL(5,2),
    status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inspection_findings (
    finding_id VARCHAR(40) PRIMARY KEY,
    inspection_id VARCHAR(40) NOT NULL,
    category VARCHAR(80),
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    photo_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_findings_inspection FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
);

CREATE TABLE IF NOT EXISTS capa (
    capa_id VARCHAR(40) PRIMARY KEY,
    incident_id VARCHAR(40),
    finding_id VARCHAR(40),
    title VARCHAR(200) NOT NULL,
    action_type VARCHAR(30) NOT NULL DEFAULT 'CORRECTIVE',
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    assigned_to VARCHAR(30),
    due_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
    completion_date DATE,
    verification_status VARCHAR(30),
    verified_by VARCHAR(30),
    last_reminder_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chemicals (
    chemical_id VARCHAR(40) PRIMARY KEY,
    chemical_name VARCHAR(180) NOT NULL,
    cas_number VARCHAR(60),
    department_id VARCHAR(30),
    zone_id VARCHAR(30),
    quantity DECIMAL(12,3) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL DEFAULT 'kg',
    hazard_class VARCHAR(80),
    storage_requirements TEXT,
    sds_url VARCHAR(500),
    expiry_date DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health_exams (
    exam_id VARCHAR(40) PRIMARY KEY,
    employee_id VARCHAR(30) NOT NULL,
    exam_type VARCHAR(80) NOT NULL,
    exam_date DATE NOT NULL,
    next_exam_date DATE,
    fitness_status VARCHAR(40) NOT NULL,
    restrictions TEXT,
    provider VARCHAR(160),
    status VARCHAR(30) NOT NULL DEFAULT 'COMPLETED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS training_courses (
    course_id VARCHAR(40) PRIMARY KEY,
    course_code VARCHAR(40) NOT NULL UNIQUE,
    course_name VARCHAR(180) NOT NULL,
    validity_months INT,
    provider VARCHAR(160),
    mandatory BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS certificates (
    certificate_id VARCHAR(40) PRIMARY KEY,
    employee_id VARCHAR(30) NOT NULL,
    course_id VARCHAR(40) NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    certificate_number VARCHAR(80),
    provider VARCHAR(160),
    status VARCHAR(30) NOT NULL DEFAULT 'VALID',
    last_reminder_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(50) PRIMARY KEY,
    recipient_user_id VARCHAR(40),
    recipient_employee_id VARCHAR(30),
    type VARCHAR(60) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    entity_type VARCHAR(40),
    entity_id VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'UNREAD',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id VARCHAR(50) PRIMARY KEY,
    actor_type VARCHAR(30) NOT NULL,
    actor_id VARCHAR(80) NOT NULL,
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(80),
    details_json TEXT,
    correlation_id VARCHAR(80),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automation_rules (
    rule_id VARCHAR(40) PRIMARY KEY,
    rule_name VARCHAR(160) NOT NULL,
    entity_type VARCHAR(40) NOT NULL,
    trigger_type VARCHAR(40) NOT NULL,
    schedule_cron VARCHAR(80),
    conditions_json TEXT,
    action_type VARCHAR(60) NOT NULL,
    action_endpoint VARCHAR(255),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS automation_actions (
    action_record_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL UNIQUE,
    idempotency_key VARCHAR(100) NOT NULL UNIQUE,
    rule_id VARCHAR(40) NOT NULL,
    entity_type VARCHAR(40) NOT NULL,
    entity_id VARCHAR(80) NOT NULL,
    action VARCHAR(80) NOT NULL,
    alert_code VARCHAR(80),
    status VARCHAR(30) NOT NULL,
    payload_json TEXT,
    processed_at_utc TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    audit_id VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS sensor_events (
    sensor_event_id VARCHAR(50) PRIMARY KEY,
    sensor_type VARCHAR(60) NOT NULL,
    zone_id VARCHAR(30),
    reading_value DECIMAL(14,4),
    reading_unit VARCHAR(30),
    threshold_value DECIMAL(14,4),
    alert_level VARCHAR(20),
    source VARCHAR(30) NOT NULL DEFAULT 'SIMULATED',
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ppe_inventory (
    ppe_item_id VARCHAR(50) PRIMARY KEY,
    item_code VARCHAR(50) NOT NULL,
    name_ar VARCHAR(200) NOT NULL,
    category_id VARCHAR(50) NOT NULL,
    unit VARCHAR(30) NOT NULL,
    balance_qty INT NOT NULL DEFAULT 0,
    reorder_threshold INT NOT NULL DEFAULT 0,
    monthly_consumption INT NOT NULL DEFAULT 0,
    supplier VARCHAR(160),
    storage_zone_id VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ppe_matrix (
    matrix_id VARCHAR(50) PRIMARY KEY,
    zone_id VARCHAR(50) NOT NULL,
    ppe_item_id VARCHAR(50) NOT NULL,
    required_flag INT NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ppe_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    ppe_item_id VARCHAR(50),
    employee_id VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    transaction_at TIMESTAMP NULL,
    processed_by VARCHAR(80),
    reason VARCHAR(255),
    permit_id VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ppe_tx_item FOREIGN KEY (ppe_item_id) REFERENCES ppe_inventory(ppe_item_id)
);

CREATE TABLE IF NOT EXISTS fire_equipment (
    equipment_id VARCHAR(50) PRIMARY KEY,
    asset_type_id VARCHAR(50) NOT NULL,
    subtype VARCHAR(100),
    department_id VARCHAR(50),
    zone_id VARCHAR(50),
    location_detail VARCHAR(200),
    capacity VARCHAR(50),
    installation_date DATE,
    expiry_date DATE,
    status VARCHAR(50) NOT NULL,
    vendor VARCHAR(160),
    qr_code VARCHAR(100),
    last_inspection_date DATE,
    next_inspection_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fire_inspections (
    id VARCHAR(50) PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    inspection_date DATE NOT NULL,
    inspector_name VARCHAR(160) NOT NULL,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fixed_safety_assets (
    id VARCHAR(50) PRIMARY KEY,
    asset_name VARCHAR(160) NOT NULL,
    asset_type VARCHAR(80) NOT NULL,
    zone_id VARCHAR(50) NOT NULL,
    location_detail VARCHAR(200),
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id VARCHAR(30),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status_id INT NOT NULL DEFAULT 1,
    mfa_enabled TINYINT(1) DEFAULT 0,
    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_avatars (
    user_id INT PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mfa_codes (
    mfa_code_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    code_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used_flag BOOLEAN DEFAULT FALSE,
    attempt_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS profile_edit_history (
    history_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    field_name VARCHAR(80) NOT NULL,
    old_value VARCHAR(1000),
    new_value VARCHAR(1000),
    modified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

