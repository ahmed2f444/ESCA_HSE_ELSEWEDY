"""
ORM models for the MySQL database tables accessed by the AI agents.
The agents connect to the MySQL database in read-only mode for querying HSE intelligence.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from app.database import Base


# ---------------------------------------------------------------------------
# Reference data (owned by Member 1, read-only here)
# ---------------------------------------------------------------------------
class Department(Base):
    __tablename__ = "departments"
    department_id = Column(String, primary_key=True)
    name_ar = Column(String)
    name_en = Column(String)
    department_type = Column(String)
    manager_employee_id = Column(String)
    hse_contact_id = Column(String)
    active_flag = Column(Boolean)


class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(String, primary_key=True)
    display_name = Column(String)
    department_id = Column(String)
    zone_id = Column(String)
    job_title = Column(String)
    manager_id = Column(String)
    employment_type = Column(String)
    hire_date = Column(DateTime)
    email_alias = Column(String)
    phone_ext = Column(Integer)
    active_flag = Column(Boolean)


# ---------------------------------------------------------------------------
# Core safety modules (owned by Member 1 / Member 2, read-only here)
# ---------------------------------------------------------------------------
class Incident(Base):
    __tablename__ = "incidents"
    incident_id = Column(String, primary_key=True)
    reported_at = Column(DateTime)
    department_id = Column(String)
    zone_id = Column(String)
    reported_by = Column(String)
    incident_type = Column(String)
    severity = Column(String)
    title = Column(String)
    description = Column(Text)
    injured_employee_id = Column(String)
    lost_days = Column(Integer)
    status = Column(String)
    investigation_owner_id = Column(String)
    target_close_date = Column(DateTime)
    actual_close_date = Column(DateTime)
    source = Column(String)


class Permit(Base):
    __tablename__ = "permits"
    permit_id = Column(String, primary_key=True)
    permit_type = Column(String)
    department_id = Column(String)
    zone_id = Column(String)
    work_description = Column(Text)
    requester_id = Column(String)
    issuer_id = Column(String)
    executor_type = Column(String)
    executor_name = Column(String)
    start_at = Column(DateTime)
    expiry_at = Column(DateTime)
    risk_level = Column(String)
    jsa_id = Column(String)
    status = Column(String)
    suspended_reason = Column(String)
    actual_close_at = Column(DateTime)
    hours_to_expiry = Column(Float)
    automation_flag = Column(Boolean)


class Finding(Base):
    __tablename__ = "findings"
    finding_id = Column(String, primary_key=True)
    inspection_id = Column(String)
    category = Column(String)
    description = Column(Text)
    severity = Column(String)
    responsible_id = Column(String)
    due_date = Column(DateTime)
    status = Column(String)
    closed_at = Column(DateTime)
    capa_required = Column(Boolean)
    capa_id = Column(String)


class CAPA(Base):
    __tablename__ = "capas"
    capa_id = Column(String, primary_key=True)
    incident_id = Column(String)
    finding_id = Column(String)
    title = Column(String)
    action_type = Column(String)
    priority = Column(String)
    assigned_to = Column(String)
    due_date = Column(DateTime)
    status = Column(String)
    completion_date = Column(DateTime)
    verification_status = Column(String)
    verified_by = Column(String)
    last_reminder_at = Column(DateTime)
    days_overdue = Column(Integer)
    automation_flag = Column(Boolean)


class RiskRegister(Base):
    __tablename__ = "risk_register"
    risk_id = Column(String, primary_key=True)
    department_id = Column(String)
    zone_id = Column(String)
    hazard = Column(String)
    activity = Column(String)
    likelihood = Column(Integer)
    severity = Column(Integer)
    inherent_score = Column(Integer)
    risk_level = Column(String)
    controls = Column(Text)
    residual_likelihood = Column(Integer)
    residual_severity = Column(Integer)
    residual_score = Column(Integer)
    owner_id = Column(String)
    status = Column(String)
    last_reviewed_at = Column(DateTime)
    next_review_date = Column(DateTime)
    review_flag = Column(Boolean)


class Certificate(Base):
    __tablename__ = "certificates"
    certificate_id = Column(String, primary_key=True)
    employee_id = Column(String)
    course_id = Column(String)
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime)
    status = Column(String)
    evidence_ref = Column(String)
    manager_id = Column(String)
    days_to_expiry = Column(Integer)
    automation_flag = Column(Boolean)


class TrainingCourse(Base):
    __tablename__ = "training_courses"
    course_id = Column(String, primary_key=True)
    name_ar = Column(String)
    name_en = Column(String)
    target_group = Column(String)
    validity_months = Column(Integer)
    mandatory_flag = Column(Boolean)
    provider = Column(String)
    active_flag = Column(Boolean)


class PPEInventory(Base):
    __tablename__ = "ppe_inventory"
    ppe_item_id = Column(String, primary_key=True)
    item_code = Column(String)
    name_ar = Column(String)
    category = Column(String)
    unit = Column(String)
    balance_qty = Column(Float)
    reorder_threshold = Column(Float)
    monthly_consumption = Column(Float)
    supplier = Column(String)
    storage_zone_id = Column(String)
    stock_status = Column(String)


class FireEquipment(Base):
    __tablename__ = "fire_equipment"
    equipment_id = Column(String, primary_key=True)
    asset_type = Column(String)
    subtype = Column(String)
    department_id = Column(String)
    zone_id = Column(String)
    location_detail = Column(String)
    capacity = Column(String)
    installation_date = Column(DateTime)
    expiry_date = Column(DateTime)
    last_inspection_date = Column(DateTime)
    next_inspection_date = Column(DateTime)
    status = Column(String)
    vendor = Column(String)
    qr_code = Column(String)


class Chemical(Base):
    __tablename__ = "chemicals"
    chemical_id = Column(Integer, primary_key=True)
    trade_name = Column(String)
    chemical_name = Column(String)
    cas_number = Column(String)
    supplier = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    ghs_classes = Column(String)
    storage_class = Column(String)
    zone_id = Column(Integer)
    status_id = Column(Integer)


class Inspection(Base):
    __tablename__ = "inspections"
    inspection_id = Column(String, primary_key=True)
    inspection_type = Column(String)
    department_id = Column(String)
    zone_id = Column(String)
    scheduled_at = Column(DateTime)
    completed_at = Column(DateTime)
    lead_inspector_id = Column(String)
    status = Column(String)
    score_pct = Column(Float)


class JSA(Base):
    __tablename__ = "jsa"
    jsa_id = Column(String, primary_key=True)
    task_name = Column(String)
    department_id = Column(String)
    zone_id = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime)
    frequency = Column(String)
    permit_required = Column(Boolean)
    permit_type = Column(String)
    inherent_score = Column(Integer)
    residual_score = Column(Integer)
    status = Column(String)


class WearableDevice(Base):
    __tablename__ = "wearable_devices"
    device_id = Column(String, primary_key=True)
    employee_id = Column(String)
    device_type = Column(String)
    assigned_at = Column(DateTime)
    status = Column(String)
    battery_pct = Column(Float)


class WearableEvent(Base):
    __tablename__ = "wearable_events"
    wearable_event_id = Column(String, primary_key=True)
    device_id = Column(String)
    employee_id = Column(String)
    captured_at = Column(DateTime)
    metric_type = Column(String)
    value = Column(Float)
    unit = Column(String)
    severity = Column(String)
    status = Column(String)


class MonthlyKPI(Base):
    __tablename__ = "monthly_kpis"
    kpi_id = Column(String, primary_key=True)
    month = Column(String)
    hours_worked = Column(Float)
    recordable_incidents = Column(Integer)
    lost_time_injuries = Column(Integer)
    lost_days = Column(Integer)
    near_misses = Column(Integer)
    safety_observations = Column(Integer)
    trir = Column(Float)
    ltifr = Column(Float)


# ---------------------------------------------------------------------------
# AI / IoT simulation module — owned by AI Student 2 (Member 5 / you)
# ---------------------------------------------------------------------------
class IoTSensor(Base):
    __tablename__ = "iot_sensors"
    sensor_id = Column(String, primary_key=True)
    sensor_type = Column(String)          # VOC, NOISE, GAS, TEMP, ...
    department_id = Column(String)
    zone_id = Column(String)
    unit = Column(String)
    safe_min = Column(Float)
    safe_max = Column(Float)
    warning_min = Column(Float)
    warning_max = Column(Float)
    status = Column(String)
    last_calibrated_at = Column(DateTime)
    next_calibration_at = Column(DateTime)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    reading_id = Column(String, primary_key=True)
    sensor_id = Column(String)
    captured_at = Column(DateTime)
    value = Column(Float)
    unit = Column(String)
    quality = Column(String)
    safe_min = Column(Float)
    safe_max = Column(Float)
    warning_min = Column(Float)
    warning_max = Column(Float)
    alert_level = Column(String)          # NORMAL, WARNING, CRITICAL


class Camera(Base):
    __tablename__ = "cameras"
    camera_id = Column(String, primary_key=True)
    zone_id = Column(String)
    capabilities = Column(String)         # semicolon-separated, e.g. "PPE;FIRE;MAN_DOWN"
    model_version = Column(String)
    processing_fps = Column(Integer)
    status = Column(String)
    last_heartbeat_at = Column(DateTime)
    stream_ref = Column(String)


class AIModel(Base):
    __tablename__ = "ai_models"
    model_id = Column(String, primary_key=True)
    model_name = Column(String)
    version = Column(String)
    task_type = Column(String)
    target_labels = Column(String)
    confidence_threshold = Column(Float)
    validation_precision = Column(Float)
    validation_recall = Column(Float)
    status = Column(String)
    deployed_at = Column(DateTime)


class AIEvent(Base):
    __tablename__ = "ai_events"
    ai_event_id = Column(String, primary_key=True)
    detected_at = Column(DateTime)
    event_type = Column(String)           # PPE_VIOLATION, RESTRICTED_ZONE, FIRE, MAN_DOWN
    camera_id = Column(String)
    zone_id = Column(String)
    employee_id = Column(String)
    confidence_pct = Column(Float)
    severity = Column(String)
    status = Column(String)
    action_taken = Column(String)
    linked_incident_id = Column(String)


# ---------------------------------------------------------------------------
# Conversational Q&A audit trail — owned by AI Student 2 (Member 5 / you)
# ---------------------------------------------------------------------------
class QASession(Base):
    __tablename__ = "qa_sessions"
    session_id = Column(String, primary_key=True)
    admin_user_id = Column(String)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    status = Column(String)               # ACTIVE, CLOSED
    purpose = Column(String)
    sensitivity = Column(String)


class QAMessage(Base):
    __tablename__ = "qa_messages"
    message_id = Column(String, primary_key=True)
    session_id = Column(String)
    message_order = Column(Integer)
    role = Column(String)                 # USER, ASSISTANT
    created_at = Column(DateTime)
    content = Column(Text)
    source_count = Column(Integer)
    safety_flag = Column(String)          # SAFE, BLOCKED
    status = Column(String)


class QAToolCall(Base):
    __tablename__ = "qa_tool_calls"
    tool_call_id = Column(String, primary_key=True)
    message_id = Column(String)
    tool_name = Column(String)
    entity_type = Column(String)
    query_summary = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    rows_returned = Column(Integer)
    outcome = Column(String)              # SUCCESS, ERROR
    audit_id = Column(String)
    write_performed = Column(Boolean)     # must always be False for Q&A tools


# ---------------------------------------------------------------------------
# PPE & Fire Safety Sub-modules (Member 6 / Karim's module)
# ---------------------------------------------------------------------------
class PPEMatrix(Base):
    __tablename__ = "ppe_matrix"
    matrix_id = Column(String, primary_key=True)
    zone_id = Column(String)
    ppe_item_id = Column(String)
    required_flag = Column(Integer)
    notes = Column(Text)


class PPETransaction(Base):
    __tablename__ = "ppe_transactions"
    transaction_id = Column(String, primary_key=True)
    ppe_item_id = Column(String)
    employee_id = Column(String)
    transaction_type = Column(String)     # ISSUE, RETURN
    quantity = Column(Integer)
    transacted_at = Column(DateTime)
    processed_by = Column(String)
    reason = Column(String)
    permit_id = Column(String)
    notes = Column(Text)


class FireInspection(Base):
    __tablename__ = "fire_inspections"
    id = Column(String, primary_key=True)
    equipment_id = Column(String)
    inspection_date = Column(String)
    inspector_name = Column(String)
    status = Column(String)               # PASSED, FAILED, MAINTENANCE_REQUIRED
    notes = Column(Text)


class FixedSafetyAsset(Base):
    __tablename__ = "fixed_safety_assets"
    id = Column(String, primary_key=True)
    asset_name = Column(String)
    asset_type = Column(String)
    zone_id = Column(String)
    location_detail = Column(String)
    status = Column(String)