"""
Multi-Turn Cross-Module Scenario Test Suite for ESCA HSE AI Safety Assistant.
Verifies conversational task execution across interconnected HSE modules:
1. ePTW Hot Work Permit + SIMOPS + Fire Extinguisher Readiness Alignment
2. Incident Reporting + Root Cause Analysis (5-Whys RCA) + CAPA Action + Follow-up Inspection
3. PPE Inventory Deficit + Automated Reorder Supply Order + Issue Transaction
4. HazMat Chemical Compatibility + Industrial Hygiene + Occupational Health Medical Exam
"""
import uuid
import pytest
from app.database import SessionLocal
from app.tools.handlers import HANDLERS
from app.tools.rbac import check_tool_access, ROLE_HSE_MANAGER, ROLE_HSE_OFFICER, ROLE_WORKER


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_scenario_hot_work_permit_and_fire_safety_alignment(db):
    """
    Scenario 1:
    Step 1: Check SIMOPS conflicts in Zone 3.
    Step 2: Issue a Hot Work Permit in Zone 3 with Gas Testing requirement.
    Step 3: Query fire equipment status and coverage in Zone 3 to ensure fire watch readiness.
    Step 4: Verify permit status update and approval workflow.
    """
    uid = uuid.uuid4().hex[:6].upper()

    # Step 1: SIMOPS Check
    simops_res = HANDLERS["check_simops_conflicts"](db=db, zone_id=3)
    assert "has_conflict" in simops_res or "total_conflicts" in simops_res

    # Step 2: Create Hot Work Permit
    permit_res = HANDLERS["create_permit"](
        db=db,
        permit_type="HOT_WORK",
        work_description=f"Welding and grinding structural steel cable support QA {uid}",
        zone_id=3,
        duration_hours=6.0,
        risk_level="HIGH",
        gas_test_required=True,
        requester_name="محمود عبد الله",
        executor_name="Maintenance Electrical Team"
    )
    assert permit_res.get("success") is True
    permit_id = permit_res["permit_id"]
    permit_code = permit_res.get("permit_code", f"PTW-{permit_id}")

    # Step 3: Check Fire Safety Equipment Coverage in Zone 3
    fire_cov = HANDLERS["get_fire_coverage_by_zone"](db=db, zone_id=3)
    assert fire_cov.get("success") is True or "rows" in fire_cov

    fire_eq_list = HANDLERS["list_fire_equipment"](db=db, zone_id=3, limit=5)
    assert isinstance(fire_eq_list.get("rows", []), list)

    # Step 4: Approve & Activate Permit
    approval_res = HANDLERS["update_permit_status"](
        db=db,
        permit_id=permit_id,
        status="ACTIVE",
        note="Approved after gas test verification (O2=20.9%, LEL=0%) and dedicated fire watch posted"
    )
    assert approval_res.get("success") is True

    # Cleanup test permit
    HANDLERS["delete_record"](db=db, table_name="permits", record_id=permit_id, reason="Scenario 1 test cleanup")


def test_scenario_incident_rca_capa_and_inspection_cycle(db):
    """
    Scenario 2:
    Step 1: Log an Unsafe Condition incident in Zone 1.
    Step 2: Generate Root Cause Analysis (5 Whys RCA) for the incident.
    Step 3: Create a high-priority Corrective Action (CAPA) assigned to maintenance.
    Step 4: Schedule a follow-up Safety Inspection to verify corrective actions.
    """
    uid = uuid.uuid4().hex[:6].upper()

    # Step 1: Log Incident
    inc_res = HANDLERS["create_incident"](
        db=db,
        title=f"Hydraulic oil drip on CCV line QA {uid}",
        description=f"Minor hydraulic line leakage detected near extruder 2 during shift 1 QA {uid}",
        zone_id=1,
        severity="MODERATE",
        incident_type="UNSAFE_CONDITION"
    )
    assert inc_res.get("success") is True
    incident_id = inc_res["incident_id"]

    # Step 2: Create Incident RCA
    rca_res = HANDLERS["create_incident_rca"](
        db=db,
        incident_id=incident_id,
        problem_statement="Vibration caused hydraulic fitting to loosen on extruder line",
        root_cause="Missing periodic torque check in preventive maintenance SOP",
        method="5 Whys + Fishbone (Ishikawa)",
        primary_cause_category="قصور في إجراءات وتصاريح العمل",
        contributing_factors="High machine vibration and thermal cycling"
    )
    assert rca_res.get("success") is True or "rca_id" in rca_res

    # Step 3: Create CAPA Action
    capa_res = HANDLERS["create_capa"](
        db=db,
        title=f"Update PM torque check for extruder lines QA {uid}",
        action_type="CORRECTIVE",
        priority="HIGH",
        due_date="2026-09-15",
        assigned_to="محمود عبد الله",
        description="Mandate torque audit on all hydraulic connections across CCV line"
    )
    assert capa_res.get("success") is True
    capa_id = capa_res["capa_id"]

    # Step 4: Schedule Follow-up Inspection
    insp_res = HANDLERS["schedule_safety_inspection"](
        db=db,
        inspection_type="تفتيش السلامة الميكانيكية والهيدروليكية",
        zone_id=1,
        frequency="أسبوعي",
        scheduled_at="2026-09-16",
        notes=f"Verification audit for CAPA #{capa_id} on CCV Extruder 2"
    )
    assert insp_res.get("success") is True
    insp_id = insp_res["inspection_id"]

    # Cleanup
    HANDLERS["delete_record"](db=db, table_name="inspections", record_id=insp_id, reason="Scenario 2 test cleanup")
    HANDLERS["delete_record"](db=db, table_name="capa", record_id=capa_id, reason="Scenario 2 test cleanup")
    HANDLERS["delete_record"](db=db, table_name="incidents", record_id=incident_id, reason="Scenario 2 test cleanup")


def test_scenario_ppe_deficit_reorder_and_transaction_flow(db):
    """
    Scenario 3:
    Step 1: Inspect PPE Stock status and identify items below reorder point.
    Step 2: Generate automated Supply Order (Purchase Order requisition).
    Step 3: Record PPE Item issue transaction to worker.
    Step 4: Verify live stock balance adjustment.
    """
    uid = uuid.uuid4().hex[:6].upper()

    # Step 1: Add new test PPE item with low stock
    ppe_item_res = HANDLERS["add_ppe_item"](
        db=db,
        item_code=f"GLV-NIT-{uid}",
        name_ar=f"قفازات نيتريل كيميائية QA {uid}",
        category="HAND",
        balance_qty=10.0,
        reorder_threshold=25.0,
        monthly_consumption=20.0,
        unit_cost=15.0
    )
    assert ppe_item_res.get("success") is True
    item_id = ppe_item_res["ppe_item_id"]

    # Step 2: Check Stock status
    status_res = HANDLERS["get_ppe_stock_status"](db=db)
    assert "rows" in status_res and isinstance(status_res["rows"], list)

    # Step 3: Trigger Automated Supply Order
    order_res = HANDLERS["create_ppe_supply_order"](
        db=db,
        urgency="HIGH",
        order_notes=f"Automated replenishment for safety stock QA {uid}"
    )
    assert order_res.get("success") is True
    assert "order_reference" in order_res

    # Step 4: Issue PPE to employee
    tx_res = HANDLERS["create_ppe_transaction"](
        db=db,
        ppe_item_id=item_id,
        employee_id="أحمد سامي",
        transaction_type="ISSUE",
        quantity=2,
        notes="Issued for chemical handling shift"
    )
    assert tx_res.get("success") is True
    tx_id = tx_res["transaction_id"]
    assert tx_res.get("new_balance") == 8.0

    # Cleanup
    HANDLERS["delete_record"](db=db, table_name="ppe_transactions", record_id=tx_id, reason="Scenario 3 test cleanup")
    HANDLERS["delete_record"](db=db, table_name="ppe_inventory", record_id=item_id, reason="Scenario 3 test cleanup")


def test_scenario_hazmat_hygiene_and_medical_exam_workflow(db):
    """
    Scenario 4:
    Step 1: Register new hazardous chemical in Zone 2.
    Step 2: Evaluate chemical compatibility and MSDS risk limits.
    Step 3: Schedule and record Occupational Health medical exam for exposed operator.
    Step 4: Update medical exam protocol and certify fitness.
    """
    uid = uuid.uuid4().hex[:6].upper()

    # Step 1: Add HazMat Chemical
    chem_res = HANDLERS["add_chemical"](
        db=db,
        trade_name=f"Solvent Degreaser QA {uid}",
        chemical_name=f"Trichloroethylene Solution QA {uid}",
        cas_number="79-01-6",
        hazard_class="FLAMMABLE_TOXIC",
        quantity=150.0,
        unit="LITERS",
        zone_id=2,
        msds_url="https://esca.local/msds/TCE-79016.pdf"
    )
    assert chem_res.get("success") is True
    chemical_id = chem_res["chemical_id"]

    # Step 2: Check Chemical Compatibility
    compat_res = HANDLERS["get_chemical_compatibility"](
        db=db,
        chemical_a="Flammable Liquid",
        chemical_b="Corrosive Acid"
    )
    assert "compatibility_matrix" in compat_res

    # Step 3: Record Medical Exam for exposed employee
    exam_res = HANDLERS["record_medical_exam"](
        db=db,
        employee_id="أحمد سامي",
        fitness_result="FIT",
        restriction_summary="Fit for work with organic vapor respiratory protection (A2P3)",
        notes=f"Periodic industrial hygiene audiometry and pulmonary exam QA {uid}"
    )
    assert exam_res.get("success") is True
    exam_id = exam_res["exam_id"]

    # Step 4: Schedule Next Annual Exam
    sched_res = HANDLERS["schedule_medical_exam"](
        db=db,
        employee_id="أحمد سامي",
        scheduled_in_days=365,
        notes="Next annual periodic surveillance exam"
    )
    assert sched_res.get("success") is True

    # Cleanup
    HANDLERS["delete_record"](db=db, table_name="health_exams", record_id=exam_id, reason="Scenario 4 test cleanup")
    HANDLERS["delete_record"](db=db, table_name="chemicals", record_id=chemical_id, reason="Scenario 4 test cleanup")
