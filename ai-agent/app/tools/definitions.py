"""
Tool (function) definitions handed to the LLM.
Supports both Cloud Groq and Local Ollama models.
Covers RAG Knowledge Search, Live Database Retrieval, and full CRUD Operations across all 15 ESCA HSE Modules.
"""

TOOLS = [
    # ── 1. RAG Knowledge & Universal Search Tools ─────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_hse_knowledge",
            "description": "RAG Knowledge Base Search: Search official HSE regulations, ISO 45001:2018 clauses, OSHA standards (1910/1926), Elsewedy Cables (ESCA) 10 Safety Golden Rules, GHS hazard codes, atmospheric gas testing thresholds (O2, LEL, H2S, CO), and safety KPI calculation formulas (TRIR, LTIFR, Days Until Stockout).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic or question keywords (e.g., 'ISO 45001 Clause 6', 'Confined space gas limits', 'TRIR formula', 'LOTO steps', 'Golden Rule 3')."
                    },
                    "category": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Optional category: 'ISO_45001', 'OSHA', 'ESCA_GOLDEN_RULES', 'CALCULATIONS'."
                    },
                    "limit": {"type": "integer", "default": 4}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_database_entities",
            "description": "Universal database entity search: Search across incidents, permits, CAPA actions, employees, chemicals, equipment, PPE items, and risk register by keyword or ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., 'Transformer', 'Hot Work', 'EMP-001', 'Acetone', 'Helmet', 'Zone 1')."
                    },
                    "entity_type": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Optional entity filter: 'incidents', 'permits', 'capa', 'employees', 'chemicals', 'fire_equipment', 'ppe_inventory', 'risk_register'."
                    },
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_read_only_query",
            "description": "Execute any read-only SQL SELECT query on the live Railway MySQL database (135 tables). Use for custom aggregations, calculations, JOINs, or specific record lookups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "SQL SELECT statement to run (e.g., 'SELECT zone_id, COUNT(*) FROM incidents GROUP BY zone_id')."
                    }
                },
                "required": ["sql_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_db_schema",
            "description": "Inspect column names and data types of any table or list all table names in the Railway MySQL database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Table name to inspect. Omit to list all available tables."
                    }
                },
                "required": []
            }
        }
    },

    # ── 2. Master Data & Organization Module ──────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_departments",
            "description": "List factory departments, manager employee IDs, HSE contacts, and active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "active_only": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_zones",
            "description": "List factory production and utility zones, plant areas, risk classifications, and occupancy limits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_employees",
            "description": "List employees filtered by department, zone, job title, or active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "job_title": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "active_only": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_info",
            "description": "Look up comprehensive employee profile: contact info, assigned zone, active permits, certifications, and medical exams by employee ID or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]},
                    "query": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Employee name search term (e.g. 'أحمد سامي' or 'Ahmed Samy')"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_employee",
            "description": "CRUD CREATE: Add and register a new employee in the factory personnel roster.",
            "parameters": {
                "type": "object",
                "properties": {
                    "display_name": {"type": "string", "description": "Full employee name (Arabic or English)"},
                    "job_title": {"type": "string", "description": "Job title/role", "default": "Technician"},
                    "zone_id": {"type": "integer", "description": "Assigned zone ID (1-10)", "default": 1},
                    "manager_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Manager employee ID"},
                    "email_alias": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Corporate email alias"},
                    "phone_ext": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Internal phone extension"}
                },
                "required": ["display_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_employee",
            "description": "CRUD UPDATE: Update employee profile, job title, assigned zone, or active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Employee ID or name"},
                    "job_title": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "manager_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "active_flag": {"anyOf": [{"type": "boolean"}, {"type": "null"}]}
                },
                "required": ["employee_id"]
            }
        }
    },

    # ── 3. Dashboard, Executive Safety KPIs & Audit Trail ───────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_summary",
            "description": "Get executive HSE dashboard summary: Days without LTI, best streak, safe man-hours, open incidents, high-severity open, overdue CAPAs, TRIR & delta, fire readiness %, PPE compliance %.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_kpis",
            "description": "Get monthly safety KPI records (hours worked, TRIR, LTIFR, lost days, recordable incidents, near misses, safety observations).",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "e.g., 2026-07"},
                    "limit": {"type": "integer", "default": 12}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_safety_scores",
            "description": "Get safety score rankings and compliance index across all plant zones.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_audit_logs",
            "description": "Inquire the immutable audit log: Track all state mutations, actor, action, entity type, entity ID, cryptographic hash, and timestamp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "e.g., INCIDENT, PERMIT, CERTIFICATE, CAPA, PPE"},
                    "action": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },

    # ── 4. Incidents & Safety Observations Module ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_incident",
            "description": "CRUD CREATE: Report and register a new HSE incident, near miss, unsafe act, or injury in the Railway database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Brief summary title of the incident"},
                    "description": {"type": "string", "description": "Detailed factual description of what occurred"},
                    "zone_id": {"type": "integer", "description": "Zone/Plant Area ID (e.g. 1 for Zone 1, 2 for Zone 2)", "default": 1},
                    "reported_by": {"type": "integer", "description": "Employee ID reporting the incident (e.g. 1)", "default": 1},
                    "severity": {"type": "string", "description": "MINOR, MODERATE, MAJOR, or CRITICAL", "default": "MINOR"},
                    "incident_type": {"type": "string", "description": "NEAR_MISS, FIRST_AID, LTI, UNSAFE_ACT, UNSAFE_CONDITION, PROPERTY_DAMAGE", "default": "NEAR_MISS"},
                    "lost_days": {"type": "integer", "description": "Lost work days (0 for near miss / first aid)", "default": 0},
                    "injured_employee_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Optional injured employee ID"}
                },
                "required": ["title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_safety_observation",
            "description": "CRUD CREATE: Record an Unsafe Act, Unsafe Condition, or Positive Safety Observation. (Arabic: تسجيل ملاحظة سلامة, سلوك غير آمن, تصرف خطر).",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Detailed observation description"},
                    "zone_id": {"type": "integer", "description": "Zone ID", "default": 1},
                    "observation_type": {"type": "string", "description": "UNSAFE_ACT, UNSAFE_CONDITION, POSITIVE_BEHAVIOR", "default": "UNSAFE_ACT"},
                    "reported_by": {"type": "integer", "description": "Employee ID", "default": 1},
                    "action_taken": {"type": "string", "description": "Immediate corrective action taken on the spot", "default": "Addressed immediately with worker"}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_incidents",
            "description": "List recent HSE incidents, near-misses, and injury logs from the live database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "e.g., REPORTED, CLASSIFIED, INVESTIGATING, CAPA_ASSIGNED, CLOSED"},
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "MINOR, MODERATE, MAJOR, CRITICAL"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_details",
            "description": "Get deep investigation details, root causes (RCA), contributing factors, linked CAPAs, and injured worker data for a specific incident ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "integer", "description": "Incident ID"}
                },
                "required": ["incident_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_incident_rca",
            "description": "Get Root Cause Analysis (RCA) records, 5-Whys methodology, problem statement, and primary cause categories for an incident.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "integer", "description": "Incident ID"}
                },
                "required": ["incident_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_incident_status",
            "description": "CRUD UPDATE: Update the lifecycle status, lost days, or closure details of an incident in the Railway database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "integer", "description": "Incident ID to update"},
                    "status": {"type": "string", "description": "REPORTED, CLASSIFIED, INVESTIGATING, CAPA_ASSIGNED, PENDING_VERIFICATION, CLOSED"},
                    "lost_days": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Updated lost work days"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Investigation or resolution note"}
                },
                "required": ["incident_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_incident",
            "description": "CRUD UPDATE: Update incident title, description, zone, severity, or investigation owner.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "integer", "description": "Incident ID"},
                    "title": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "description": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "lost_days": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "investigation_owner_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                },
                "required": ["incident_id"]
            }
        }
    },

    # ── 5. Electronic Permits to Work (ePTW) & SIMOPS Module ───────────────────
    {
        "type": "function",
        "function": {
            "name": "create_permit",
            "description": "CRUD CREATE: Issue and register a new electronic Permit to Work (ePTW) in the Railway database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_type": {"type": "string", "description": "HOT_WORK, CONFINED_SPACE, WORK_AT_HEIGHT, ELECTRICAL, MECHANICAL_LOTO, EXCAVATION, RADIOGRAPHY"},
                    "zone_id": {"type": "integer", "description": "Zone/Area ID (1-10)", "default": 1},
                    "work_description": {"type": "string", "description": "Detailed description of the authorized work"},
                    "requester_id": {"type": "integer", "description": "Employee ID requesting the permit", "default": 1},
                    "issuer_id": {"type": "integer", "description": "HSE Officer / Issuer employee ID", "default": 1},
                    "executor_name": {"type": "string", "description": "Contractor or Technician lead executing the work", "default": "Internal Maintenance Team"},
                    "risk_level": {"type": "string", "description": "LOW, MEDIUM, HIGH, CRITICAL", "default": "MEDIUM"},
                    "duration_hours": {"type": "integer", "description": "Validity duration in hours", "default": 8}
                },
                "required": ["permit_type", "work_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_permits",
            "description": "List electronic permits to work (ePTW) by status, risk level, or type (HOT_WORK, CONFINED_SPACE, HEIGHT, ELECTRICAL).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "ACTIVE, APPROVED, PENDING_APPROVAL, EXPIRED, SUSPENDED, CLOSED"},
                    "risk_level": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "LOW, MEDIUM, HIGH, CRITICAL"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_permit_details",
            "description": "Get deep permit details: Gas test results, checklist confirmations, required approvals, executor info, and remaining hours to expiry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {"type": "integer", "description": "Permit ID"}
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_permit_status",
            "description": "CRUD UPDATE: Transition permit lifecycle (APPROVE, ACTIVATE, SUSPEND, CLOSE, CANCEL) in the Railway database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {"type": "integer", "description": "Permit ID to update"},
                    "status": {"type": "string", "description": "ACTIVE, APPROVED, SUSPENDED, CLOSED, CANCELLED, REJECTED"},
                    "reason_or_note": {"type": "string", "description": "Approval note, closure sign-off, or suspension reason", "default": "Status updated by HSE Authority"}
                },
                "required": ["permit_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_simops_conflicts",
            "description": "Detect Simultaneous Operations (SIMOPS) conflicts: Identifies overlapping high-risk permits in the same plant zone (e.g. Hot Work + Chemical / Confined Space).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Optional zone ID to check specifically"},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },

    # ── 6. Inspections & Safety Audits Module ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "schedule_safety_inspection",
            "description": "CRUD CREATE: Schedule or book a safety walkthrough, audit, or compliance inspection in a plant zone. (Arabic: جدولة فحص سلامة, جدول تفتيش, موعد فحص, تحديد موعد معاينة).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_type": {"type": "string", "description": "e.g., ROUTINE_WALK, FIRE_SAFETY, ELECTRICAL_AUDIT, ISO_45001_AUDIT", "default": "ROUTINE_WALK"},
                    "zone_id": {"type": "integer", "description": "Zone/Area ID", "default": 1},
                    "lead_inspector_id": {"type": "integer", "description": "Inspector employee ID", "default": 1},
                    "scheduled_in_days": {"type": "integer", "description": "Days from now for scheduled date", "default": 7},
                    "notes": {"type": "string", "description": "Scope notes or focus points", "default": "Scheduled inspection"}
                },
                "required": ["inspection_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_inspections",
            "description": "List safety inspections and audits with compliance score percentages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_inspection_status",
            "description": "CRUD UPDATE: Complete or update an inspection record with compliance score percentage and status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"type": "integer", "description": "Inspection ID"},
                    "status": {"type": "string", "description": "SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED", "default": "COMPLETED"},
                    "score_pct": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Compliance score percentage (e.g. 95.5)"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Inspection summary / closing notes"}
                },
                "required": ["inspection_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_inspection_finding",
            "description": "CRUD CREATE: Log a non-conformance or safety finding during an inspection, with responsible person, due date, and CAPA requirement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"type": "integer", "description": "Inspection ID"},
                    "category": {"type": "string", "description": "Finding category (e.g. PPE, HOUSEKEEPING, ELECTRICAL, FIRE, WORK_AT_HEIGHT)", "default": "HOUSEKEEPING"},
                    "description": {"type": "string", "description": "Factual finding description"},
                    "severity": {"type": "string", "description": "MINOR, MODERATE, MAJOR, CRITICAL", "default": "MODERATE"},
                    "responsible_id": {"type": "integer", "description": "Employee ID responsible for fixing", "default": 1},
                    "due_days": {"type": "integer", "description": "Days until deadline", "default": 7},
                    "capa_required": {"type": "boolean", "description": "Whether a formal CAPA must be triggered", "default": True}
                },
                "required": ["inspection_id", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_inspection_findings",
            "description": "List non-conformance findings across inspections, filtered by severity, status, or inspection ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "category": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_inspection_templates",
            "description": "List standard inspection checklists and audit templates (e.g. Daily Walkthrough, ISO 45001, Electrical Safety).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },

    # ── 7. CAPA (Corrective & Preventive Actions) Module ───────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_capa",
            "description": "CRUD CREATE: Create a new Corrective and Preventive Action (CAPA) assigned to a responsible person.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Action title and specific remediation requirement"},
                    "incident_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Associated incident ID (optional)"},
                    "finding_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Associated inspection finding ID (optional)"},
                    "action_type": {"type": "string", "description": "CORRECTIVE, PREVENTIVE", "default": "CORRECTIVE"},
                    "priority": {"type": "string", "description": "LOW, MEDIUM, HIGH, CRITICAL", "default": "HIGH"},
                    "assigned_to": {"type": "integer", "description": "Employee ID responsible for implementing action", "default": 1},
                    "due_days": {"type": "integer", "description": "Days until deadline from today", "default": 7}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_capas",
            "description": "List CAPA actions filtered by status (OPEN, IN_PROGRESS, COMPLETED), priority, or assignee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "priority": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "assigned_to": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_overdue_capas",
            "description": "List overdue CAPA corrective actions from the database (past due_date and not completed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_capa_details",
            "description": "Get complete CAPA details: Root incident/finding linkage, assignee, verification status, and completion timeline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "capa_id": {"type": "integer", "description": "CAPA ID"}
                },
                "required": ["capa_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_capa_status",
            "description": "CRUD UPDATE: Update CAPA completion status (OPEN, IN_PROGRESS, COMPLETED, CANCELLED) and record completion notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "capa_id": {"type": "integer", "description": "CAPA ID to update"},
                    "status": {"type": "string", "description": "OPEN, IN_PROGRESS, COMPLETED, CANCELLED"},
                    "completion_notes": {"type": "string", "description": "Remediation evidence or verification notes", "default": "Action completed and verified"}
                },
                "required": ["capa_id", "status"]
            }
        }
    },

    # ── 8. Risk Assessment Register (HIRA) Module ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_risk_assessment",
            "description": "CRUD CREATE: Register a new hazard identification and risk assessment (HIRA) in the Risk Register. (Arabic: تسجيل تقييم مخاطر, اضافة خطر, تقييم خطورة نشاط).",
            "parameters": {
                "type": "object",
                "properties": {
                    "hazard": {"type": "string", "description": "Specific hazard identified"},
                    "activity": {"type": "string", "description": "Plant activity or process", "default": "Plant Operations"},
                    "controls": {"type": "string", "description": "Hierarchy of controls implemented", "default": "Standard HSE Controls"},
                    "zone_id": {"type": "integer", "description": "Zone ID", "default": 1},
                    "likelihood": {"type": "integer", "description": "Likelihood rating (1-5)", "default": 3},
                    "severity": {"type": "integer", "description": "Severity rating (1-5)", "default": 3}
                },
                "required": ["hazard"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_risk_register",
            "description": "List risk assessment register items (hazards, activities, inherent and residual risk scores, controls).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "risk_level": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_risk_matrix",
            "description": "Get risk distribution matrix: Summary counts of Critical, High, Medium, and Low risks, top hazardous activities, and review status.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_risk_assessment",
            "description": "CRUD UPDATE: Update residual risk scores, control measures, and review status of a hazard in the Risk Register.",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_id": {"type": "integer", "description": "Risk ID"},
                    "residual_likelihood": {"type": "integer", "description": "Residual likelihood (1-5)", "default": 1},
                    "residual_severity": {"type": "integer", "description": "Residual severity (1-5)", "default": 2},
                    "controls": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated control measures"}
                },
                "required": ["risk_id"]
            }
        }
    },

    # ── 9. Job Safety Analysis (JSA) Module ────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_jsa",
            "description": "CRUD CREATE: Create a new Job Safety Analysis (JSA) for high-risk plant activities with step-by-step hazard breakdowns and controls.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {"type": "string", "description": "Name of the task/job (e.g. 'صيانة لوحة الكهرباء الرئيسية')"},
                    "zone_id": {"type": "integer", "description": "Zone ID", "default": 1},
                    "created_by": {"type": "integer", "description": "Employee ID creating JSA", "default": 1},
                    "permit_required": {"type": "boolean", "description": "Whether permit to work is mandatory", "default": True},
                    "permit_type": {"type": "string", "description": "Required permit type (e.g. ELECTRICAL, HOT_WORK)", "default": "HOT_WORK"},
                    "inherent_score": {"type": "integer", "description": "Initial risk score (1-25)", "default": 15},
                    "residual_score": {"type": "integer", "description": "Residual score after controls (1-25)", "default": 4}
                },
                "required": ["task_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_jsas",
            "description": "List Job Safety Analysis (JSA) documents filtered by zone, permit requirement, or status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_jsa_details",
            "description": "Get detailed step-by-step task breakdown, hazard identification, and control measures for a specific JSA ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jsa_id": {"type": "integer", "description": "JSA ID"}
                },
                "required": ["jsa_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_jsa",
            "description": "CRUD UPDATE: Update JSA approval status (APPROVED, DRAFT, ARCHIVED), controls, or residual score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jsa_id": {"type": "integer", "description": "JSA ID"},
                    "status": {"type": "string", "description": "DRAFT, PENDING_APPROVAL, APPROVED, ARCHIVED", "default": "APPROVED"},
                    "residual_score": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                },
                "required": ["jsa_id"]
            }
        }
    },

    # ── 10. Training & Certifications Module ───────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_training_course",
            "description": "CRUD CREATE: Add a new HSE training course to the catalog (validity months, mandatory flag, target group, provider).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_ar": {"type": "string", "description": "Course Arabic title (e.g. 'السلامة في الأماكن المغلقة')"},
                    "name_en": {"type": "string", "description": "Course English title (e.g. 'Confined Space Safety')"},
                    "validity_months": {"type": "integer", "description": "Validity period in months (e.g. 12 or 24)", "default": 12},
                    "mandatory_flag": {"type": "boolean", "description": "Whether course is mandatory", "default": True},
                    "target_group": {"type": "string", "description": "Target audience (e.g. All Production Technicians)", "default": "All Plant Personnel"},
                    "provider": {"type": "string", "description": "Internal or External Provider", "default": "ESCA HSE Academy"}
                },
                "required": ["name_ar", "name_en"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_certificate",
            "description": "CRUD CREATE: Issue and record a training qualification certificate for an employee in the Railway database. Evaluates exact expiration timestamp and triggers real-time safety automation alerts (AUT-002) if expired at the time of creation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string", "description": "Full name of the employee (e.g. 'Ahmed Samy' or 'أحمد سامي')"},
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Employee ID (optional if employee_name is provided)"},
                    "course_name": {"type": "string", "description": "Course title (e.g. 'Work at Height Safety', 'Hot Work', 'General Induction')", "default": "General Safety Induction"},
                    "course_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Course ID (optional if course_name is provided)"},
                    "expiry_date": {"type": "string", "description": "Expiration date in YYYY-MM-DD format (e.g. '2026-08-29')"},
                    "expiry_time": {"type": "string", "description": "Exact expiration time (e.g. '01:50 AM', '1:50', '13:45', '150 am')", "default": "23:59"},
                    "evidence_ref": {"type": "string", "description": "Certificate reference code or document ID (e.g. 'CERT-2026-0042')"}
                },
                "required": ["employee_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_certificates",
            "description": "List employee training certificates with course names, validity status, and expiration dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Filter by employee ID or name"},
                    "status": {"type": "string", "description": "VALID, EXPIRED, RENEWAL_BOOKED, SUSPENDED"},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_training_courses",
            "description": "List all available HSE training courses, validity duration in months, target groups, and providers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_training",
            "description": "List expired or soon-to-expire employee training certifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_certificate_status",
            "description": "CRUD UPDATE: Update or renew training certificate validity status (VALID, EXPIRED), expiration date, or exact expiration time. Supports relative durations like '+1 year' (default standard renewal), '+2 years', '+6 months' or ISO 'YYYY-MM-DD'. Omit expiry_date to automatically apply standard accredited course validity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "certificate_id": {"description": "Certificate ID or reference code (e.g. 63 or 'TRN-063'). If omitted, the latest certificate is updated."},
                    "status": {"type": "string", "description": "New status: VALID (default for renewal) or EXPIRED (optional)"},
                    "expiry_date": {"type": "string", "description": "New expiry date or renewal duration: '+1 year' (default standard renewal), '+2 years', '+6 months', or ISO 'YYYY-MM-DD' (e.g. '2027-08-29'). Omit to automatically apply course validity."},
                    "expiry_time": {"type": "string", "description": "New exact expiration time (e.g. '23:59', '12:36 PM', '14:00') (optional, default: 23:59)"},
                    "reason": {"type": "string", "description": "Reason for modification"}
                },
                "required": ["certificate_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_certificate",
            "description": "CRUD UPDATE: Update or renew training certificate expiration date, time, or status. Defaults to standard course duration (+1 Year).",
            "parameters": {
                "type": "object",
                "properties": {
                    "certificate_id": {"description": "Certificate ID or code (e.g. 63 or 'TRN-063')"},
                    "status": {"type": "string", "description": "New status: VALID or EXPIRED (optional)"},
                    "expiry_date": {"type": "string", "description": "New expiry date in '+1 year', '2 years', '6 months', or 'YYYY-MM-DD' (optional)"},
                    "expiry_time": {"type": "string", "description": "New exact expiration time (e.g. '23:59', '12:36 PM') (optional)"},
                    "reason": {"type": "string", "description": "Reason for modification"}
                },
                "required": ["certificate_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_training_course",
            "description": "CRUD UPDATE: Update course name, validity duration in months, or active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer", "description": "Course ID"},
                    "name_ar": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "name_en": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "validity_months": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "active_flag": {"anyOf": [{"type": "boolean"}, {"type": "null"}]}
                },
                "required": ["course_id"]
            }
        }
    },

    # ── 11. PPE Management (Personal Protective Equipment) Module ───────────────
    {
        "type": "function",
        "function": {
            "name": "add_ppe_item",
            "description": "CRUD CREATE: Add a new PPE item to the plant inventory catalog (e.g. safety helmets, cut-resistant gloves, steel-toe boots, respirators).",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_code": {"type": "string", "description": "Unique PPE code (e.g. 'PPE-HD-05')"},
                    "name_ar": {"type": "string", "description": "Arabic item title (e.g. 'خوذة حماية كهربائية 20kV')"},
                    "category": {"type": "string", "description": "HEAD, EYE, HAND, FOOT, RESPIRATORY, BODY", "default": "HEAD"},
                    "unit": {"type": "string", "description": "Unit (Piece, Pair, Box)", "default": "Piece"},
                    "balance_qty": {"type": "number", "description": "Initial physical stock quantity", "default": 50.0},
                    "reorder_threshold": {"type": "number", "description": "Reorder alert trigger quantity", "default": 15.0},
                    "supplier": {"type": "string", "description": "Supplier name", "default": "3M Egypt"},
                    "storage_zone_id": {"type": "integer", "description": "Storage warehouse zone ID", "default": 5}
                },
                "required": ["item_code", "name_ar"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_inventory",
            "description": "List PPE items (masks, gloves, helmets, safety shoes) with current stock balances and thresholds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ppe_stock_status",
            "description": "Get PPE inventory stock analysis showing items below reorder threshold and estimated days until stockout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "below_threshold_only": {"type": "boolean", "default": False},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_matrix",
            "description": "List mandatory PPE requirements per plant zone/work area.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ppe_matrix",
            "description": "CRUD UPDATE: Update zone mandatory PPE requirements in the PPE Matrix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "integer", "description": "Zone ID"},
                    "ppe_item_id": {"type": "integer", "description": "PPE Item ID"},
                    "required_flag": {"type": "integer", "description": "1 for Required, 0 for Optional", "default": 1},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["zone_id", "ppe_item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ppe_stock",
            "description": "CRUD UPDATE: Update PPE stock balance quantity or reorder threshold in inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ppe_item_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "PPE Item ID or Item Code"},
                    "balance_qty": {"anyOf": [{"type": "integer"}, {"type": "number"}, {"type": "null"}], "description": "New physical count quantity"},
                    "reorder_threshold": {"anyOf": [{"type": "integer"}, {"type": "number"}, {"type": "null"}], "description": "New reorder alert threshold"}
                },
                "required": ["ppe_item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ppe_transaction",
            "description": "CRUD CREATE: Issue or adjust PPE inventory stock (helmets, gloves, shoes, masks) for an employee. (Arabic: صرف مهمات وقاية, صرف خوذة سلامة, تسليم مهمات للموظف).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ppe_item_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "PPE item ID, Item Code, or item name (e.g. 1, 'PPE-HD-01', or 'خوذة سلامة')", "default": 1},
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Employee ID or name (e.g. 1, 'EMP-001', 'أحمد سامي', 'Ahmed Samy')", "default": 1},
                    "quantity": {"type": "integer", "description": "Quantity issued or adjusted", "default": 1},
                    "transaction_type": {"type": "string", "description": "ISSUE, RETURN, ADJUSTMENT, DISPOSAL", "default": "ISSUE"},
                    "reason": {"type": "string", "description": "Reason for issuance or replacement", "default": "Standard periodic issue"}
                },
                "required": ["quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_transactions",
            "description": "List PPE transactions and issuance history by employee, PPE item, or transaction type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "ppe_item_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },

    # ── 12. Fire Safety & Fixed Assets Module ──────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "add_fire_equipment",
            "description": "CRUD CREATE: Add and register a new fire extinguisher or fire protection asset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {"type": "string", "description": "EXTINGUISHER, HYDRANT, HOSE_REEL, DETECTOR, SUPPRESSION_PANEL", "default": "EXTINGUISHER"},
                    "subtype": {"type": "string", "description": "CO2_6KG, DCP_6KG, FOAM_9L, WATER_9L, FM200", "default": "DCP_6KG"},
                    "zone_id": {"type": "integer", "description": "Zone ID", "default": 1},
                    "location_detail": {"type": "string", "description": "Precise location (e.g., Near Main Panel Line 3)"},
                    "vendor": {"type": "string", "description": "Vendor / Manufacturer", "default": "Bavaria Egypt"},
                    "capacity": {"type": "string", "description": "Capacity (e.g. 6 KG, 9 Liters)", "default": "6 KG"}
                },
                "required": ["asset_type", "subtype", "location_detail"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_fixed_safety_asset",
            "description": "CRUD CREATE: Register a fixed safety asset (e.g. Emergency Eyewash Station, Safety Shower, AED Defibrillator, LOTO Station, Assembly Point).",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_name": {"type": "string", "description": "Name/description of asset (e.g. 'محطة غسيل عيون طوارئ عنبر 2')"},
                    "asset_type": {"type": "string", "description": "EYEWASH, SHOWER, AED, LOTO_STATION, ASSEMBLY_POINT", "default": "EYEWASH"},
                    "total_qty": {"type": "integer", "description": "Total quantity", "default": 1},
                    "operational_qty": {"type": "integer", "description": "Operational quantity", "default": 1},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["asset_name", "asset_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_fire_equipment",
            "description": "List fire safety equipment (extinguishers, hydrants, detectors) and their inspection dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expired_fire_equipment",
            "description": "List expired or maintenance-due fire extinguishers and safety equipment requiring service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_fire_inspection",
            "description": "CRUD CREATE: Log, record, or submit a fire extinguisher / protection inspection result (e.g. 'سجل فحص طفاية', 'تسجيل فحص طفاية', 'توثيق فحص طفاية حريق').",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "integer", "description": "Fire equipment ID", "default": 1},
                    "inspector_id": {"type": "integer", "description": "Inspector employee ID", "default": 1},
                    "result": {"type": "string", "description": "PASS, PASS_WITH_ACTION, FAIL", "default": "PASS"},
                    "pressure_ok": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "default": True},
                    "hose_ok": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "default": True},
                    "safety_pin_ok": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "default": True},
                    "action_required": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Remediation note if any"}
                },
                "required": ["equipment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_fire_inspections",
            "description": "List periodic inspection logs for fire equipment (passed, maintenance required, failed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_fixed_safety_assets",
            "description": "List fixed safety assets (eyewash stations, emergency showers, AEDs, LOTO stations) and their operational status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_fire_equipment",
            "description": "CRUD UPDATE: Update fire equipment status, next inspection due date, or location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "integer", "description": "Equipment ID"},
                    "status": {"type": "string", "description": "VALID, DUE_SOON, ACTION_REQUIRED, EXPIRED, OUT_OF_SERVICE"},
                    "next_inspection_in_months": {"type": "integer", "description": "Next inspection due in months (e.g. 1 or 12)", "default": 1}
                },
                "required": ["equipment_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_fixed_safety_asset",
            "description": "CRUD UPDATE: Update fixed safety asset operational status, quantity, or test date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_summary_id": {"type": "integer", "description": "Asset Summary ID"},
                    "operational_qty": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["asset_summary_id"]
            }
        }
    },

    # ── 13. HazMat & Chemicals Management Module ──────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "add_chemical",
            "description": "CRUD CREATE: Register a new chemical product in the plant's Hazardous Materials (HazMat) inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trade_name": {"type": "string", "description": "Commercial product trade name"},
                    "chemical_name": {"type": "string", "description": "Scientific chemical formula/name"},
                    "cas_number": {"type": "string", "description": "Chemical Abstracts Service (CAS) number (e.g. 67-64-1)"},
                    "supplier": {"type": "string", "description": "Supplier/Manufacturer name"},
                    "quantity": {"type": "number", "description": "Initial stock quantity", "default": 100.0},
                    "unit": {"type": "string", "description": "Unit (Liters, KG, Drums, Cylinders)", "default": "Liters"},
                    "ghs_classes": {"type": "string", "description": "GHS Hazard classes (e.g. Flammable Liquid, Corrosive, Toxic)", "default": "Flammable Liquid"},
                    "zone_id": {"type": "integer", "description": "Storage Zone ID", "default": 4}
                },
                "required": ["trade_name", "chemical_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_chemicals",
            "description": "List chemical inventory, CAS numbers, GHS hazard classes, and storage zones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Chemical name or CAS number"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_chemical_compatibility",
            "description": "Evaluate chemical compatibility and storage segregation: Checks reactivity matrix (e.g. Flammables vs Oxidizers, Acids vs Bases) in plant chemical warehouses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemical_a": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "chemical_b": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_chemical_stock",
            "description": "CRUD UPDATE: Update hazardous chemical current quantity balance or storage zone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemical_id": {"type": "integer", "description": "Chemical ID"},
                    "quantity": {"type": "number", "description": "Updated stock quantity"}
                },
                "required": ["chemical_id", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_chemical",
            "description": "CRUD UPDATE: Update chemical metadata, trade name, CAS number, or GHS classes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemical_id": {"type": "integer", "description": "Chemical ID"},
                    "trade_name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "ghs_classes": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                },
                "required": ["chemical_id"]
            }
        }
    },

    # ── 14. Occupational Health & Industrial Hygiene Module ────────────────────
    {
        "type": "function",
        "function": {
            "name": "record_medical_exam",
            "description": "CRUD CREATE: Record an occupational health medical examination result (Audiometry, Spirometry, Vision, Blood Lead, Fitness for Duty) for an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Employee ID or name"},
                    "protocol_id": {"type": "integer", "description": "Protocol ID (1: Audiometry, 2: Spirometry, 3: Vision, 4: Blood Lead)", "default": 1},
                    "fitness_result": {"type": "string", "description": "FIT, FIT_WITH_RESTRICTIONS, UNFIT", "default": "FIT"},
                    "restriction_summary": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Medical restriction notes if any"},
                    "clinician_alias": {"type": "string", "description": "Doctor / Clinician name", "default": "Dr. HSE Clinic"}
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_medical_exam",
            "description": "CRUD CREATE: Schedule an upcoming periodic medical exam for an employee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Employee ID or name"},
                    "protocol_id": {"type": "integer", "description": "Exam Protocol ID", "default": 1},
                    "scheduled_in_days": {"type": "integer", "description": "Days from now for scheduled exam", "default": 14}
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_medical_exams",
            "description": "List occupational medical exams, clearance status (FIT, FIT_WITH_RESTRICTIONS, UNFIT), and next due dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_medical_exam",
            "description": "CRUD UPDATE: Update medical examination results, fitness clearance status, or restriction notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "integer", "description": "Exam ID"},
                    "fitness_result": {"type": "string", "description": "FIT, FIT_WITH_RESTRICTIONS, UNFIT"},
                    "restriction_summary": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["exam_id", "fitness_result"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_occupational_exposures",
            "description": "List industrial hygiene workplace exposure monitoring records: Noise (dB), Dust (mg/m3), VOC (ppm), and Heat Index (WBGT).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "exposure_type": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_wearable_devices",
            "description": "List worker smart safety wearables, battery status, heart rate / telemetry tracking, and assigned workers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },

    # ── 15. AI Vision & IoT Environmental Monitoring Module ───────────────────
    {
        "type": "function",
        "function": {
            "name": "add_iot_sensor",
            "description": "CRUD CREATE: Register a new IoT environmental sensor (VOC, Noise, Gas, Temperature, Humidity) in a plant zone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sensor_type": {"type": "string", "description": "VOC, NOISE, H2S, CO, TEMP, HUMIDITY", "default": "VOC"},
                    "zone_id": {"type": "integer", "description": "Zone ID", "default": 1},
                    "unit": {"type": "string", "description": "Measurement unit (ppm, dB, degC, %)", "default": "ppm"},
                    "safe_max": {"type": "number", "description": "Safe operating upper threshold", "default": 50.0},
                    "warning_max": {"type": "number", "description": "Warning upper threshold", "default": 80.0}
                },
                "required": ["sensor_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_iot_sensors",
            "description": "List all IoT environmental sensors with current calibration dates and safe/warning operating thresholds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_sensor_alerts",
            "description": "List IoT environmental sensor readings and alert conditions (NORMAL, WARNING, CRITICAL).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_iot_sensor",
            "description": "CRUD UPDATE: Update IoT sensor safe/warning thresholds, status, or calibration dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sensor_id": {"type": "integer", "description": "Sensor ID"},
                    "safe_max": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "warning_max": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["sensor_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_cameras",
            "description": "List smart AI vision CCTV cameras, processing FPS, status, and AI detection capabilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_ai_events",
            "description": "List AI camera detection events (PPE violations, restricted zone entry, fire/smoke alerts, man-down).",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_ai_event",
            "description": "CRUD CREATE: Record or simulate an AI computer vision detection event (PPE violation, restricted zone breach, fire alert, worker fall).",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string", "description": "PPE_VIOLATION, RESTRICTED_ZONE, FIRE, MAN_DOWN", "default": "PPE_VIOLATION"},
                    "camera_id": {"type": "integer", "description": "Camera ID", "default": 1},
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Worker ID if identified"},
                    "confidence_pct": {"type": "number", "description": "Vision model confidence percentage", "default": 96.5},
                    "severity": {"type": "string", "description": "NORMAL, MEDIUM, HIGH, CRITICAL", "default": "HIGH"},
                    "action_taken": {"type": "string", "description": "Automated alarm or notification dispatched", "default": "Audio alert triggered in zone"}
                },
                "required": ["event_type"]
            }
        }
    },

    # ── 16. Security, Roles & Integrations ────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_security_roles",
            "description": "List system RBAC roles, permission scopes, and sign-off authority matrix.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_integrations",
            "description": "List external integration connectors, webhooks, ERP synchronization, and outbox queue status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },

    # ── 17. Superuser CRUD Delete, Cancel & Direct DML Tools ──────────────────
    {
        "type": "function",
        "function": {
            "name": "delete_record",
            "description": "CRUD DELETE: Safely delete a draft or test record from authorized tables (with safety checks and automatic audit log).",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Allowed table: 'incidents', 'permits', 'capa', 'inspections', 'ppe_inventory', 'fire_equipment', 'chemicals', 'risk_register', 'jsa', 'certificates', 'employees', 'health_exams'."
                    },
                    "record_id": {"type": "integer", "description": "Primary Key ID of the record to delete"},
                    "reason": {"type": "string", "description": "Mandatory justification reason for audit log"}
                },
                "required": ["table_name", "record_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_entity",
            "description": "CRUD SOFT DELETE / CANCEL: Safely cancel an active permit, incident, or CAPA without deleting history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "description": "PERMIT, INCIDENT, CAPA"},
                    "entity_id": {"type": "integer", "description": "Entity ID to cancel"},
                    "reason": {"type": "string", "description": "Cancellation reason"}
                },
                "required": ["entity_type", "entity_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_database_dml",
            "description": "CRUD DML: Execute an advanced validated INSERT, UPDATE, or DELETE SQL statement inside an ACID transaction with automated audit logging (Restricted to Admin & HSE Manager).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "SQL INSERT, UPDATE, or DELETE statement (e.g. 'UPDATE capa SET priority_id=4 WHERE capa_id=5')."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Administrative rationale for executing this SQL operation."
                    }
                },
                "required": ["sql_query", "reason"]
            }
        }
    }
]

# For local Ollama models (optimized for rapid function calling on RTX 3050)
LOCAL_TOOLS = list(TOOLS)
