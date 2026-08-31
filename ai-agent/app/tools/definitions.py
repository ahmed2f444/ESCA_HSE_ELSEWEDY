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
            "name": "get_department_details",
            "description": "Look up complete department profile: manager contact info, HSE officer, total headcount, and list of child zones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Department ID or name (e.g. 1 or 'قطاع الإنتاج A')"}
                },
                "required": ["department_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_department",
            "description": "CRUD CREATE: Add and register a new factory department or production sector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_ar": {"type": "string", "description": "Department name in Arabic (e.g. 'قطاع الكابلات الخاصة')"},
                    "name_en": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Department name in English"},
                    "manager_employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "hse_contact_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]}
                },
                "required": ["name_ar"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_department",
            "description": "CRUD UPDATE: Update department title, manager, HSE officer, or active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Department ID or name to edit"},
                    "name_ar": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "name_en": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "manager_employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "hse_contact_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "active_flag": {"anyOf": [{"type": "boolean"}, {"type": "integer"}, {"type": "null"}]}
                },
                "required": ["department_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_department",
            "description": "CRUD DELETE: Delete or deactivate an organizational department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Department ID or name to delete"}
                },
                "required": ["department_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_zone_details",
            "description": "Look up comprehensive zone profile: risk class, occupancy, active work permits, recent incidents, and fire equipment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Zone ID or name (e.g. 1 or 'خط الإنتاج B')"}
                },
                "required": ["zone_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_department_zones_summary",
            "description": "Summary rollup of total zones, active areas, and headcount capacity grouped by department.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]}
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
                    "limit": {"type": "integer", "default": 50}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_zone",
            "description": "CRUD CREATE: Add and register a new factory zone or production area in a department in the live Railway MySQL database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_ar": {"type": "string", "description": "Zone name in Arabic (e.g. 'خط التجميع' or 'dept test')"},
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Parent department ID (e.g. 1) or department/sector name (e.g. 'Production Sector A' or 'قطاع الإنتاج A')"},
                    "name_en": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Zone name in English (e.g. 'dept test' or 'Assembly Bay')"},
                    "zone_type": {"type": "string", "enum": ["PRODUCTION", "WORKSHOP", "WAREHOUSE", "LABORATORY", "ADMIN", "UTILITY", "LOGISTICS", "CHEMICAL_STORAGE", "SERVICE", "GENERAL"], "default": "GENERAL", "description": "Zone classification category"},
                    "max_occupancy": {"type": "integer", "default": 30, "description": "Maximum occupancy headcount limit"},
                    "risk_class_id": {"type": "integer", "default": 2, "description": "Risk class (1=Low, 2=Medium, 3=High, 4=Critical)"}
                },
                "required": ["name_ar", "department_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_zone",
            "description": "CRUD UPDATE: Update zone details, occupancy, parent department, or active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Zone ID or name to update"},
                    "name_ar": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "name_en": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "department_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "max_occupancy": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "zone_type": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "active_flag": {"anyOf": [{"type": "boolean"}, {"type": "integer"}, {"type": "null"}]}
                },
                "required": ["zone_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_zone",
            "description": "CRUD DELETE: Delete or deactivate a factory zone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Zone ID or name to delete"}
                },
                "required": ["zone_id"]
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
    {
        "type": "function",
        "function": {
            "name": "export_reports_excel",
            "description": "Automate the 'Excel' export button on the Reports & Analytics page (/reports). Exports the official multi-sheet styled Executive HSE Workbook (.xlsx) comprising Executive KPIs, TRIR Trend, ISO 45001 Clauses, Leading Indicators, and Zone Density Heatmap.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "description": "Export scope: 'ALL', 'KPIS', 'TRIR', 'ISO', 'LEADING', 'ZONES'", "default": "ALL"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_reports_pdf",
            "description": "Automate the 'PDF' export / print button on the Reports & Analytics page (/reports). Generates the official printable Executive HSE Safety & Compliance document for management and ISO 45001 audit readiness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "description": "Report title / scope", "default": "التقرير التنفيذي الشامل للسلامة والصحة المهنية"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_report_to_management",
            "description": "Automate the 'إرسال للإدارة' (Send to Management) button on the Reports & Analytics page (/reports). Dispatches the executive safety report to plant leadership/management, logs the action to audit trail, and generates an official dispatch ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "description": "Report type: 'التقرير الشهري للسلامة والصحة المهنية (Monthly HSE)', 'تقرير تحليل الحوادث والأسباب الجذرية (Incident RCA)', 'تقرير الامتثال لمعايير ISO 45001 (Audit Pack)', 'تقرير جاهزية الطوارئ ومعدات مكافحة الحريق'", "default": "التقرير الشهري للسلامة والصحة المهنية (Monthly HSE)"},
                    "recipients": {"type": "string", "description": "Email recipients separated by semicolon", "default": "plant.manager@elsewedy.com; ceo@elsewedy.com; hse.director@elsewedy.com"},
                    "notes": {"type": "string", "description": "Executive notes, recommendations, and action points", "default": "يرجى الاطلاع على ملخص مؤشرات السلامة ومعدل TRIR والامتثال لمعايير ISO 45001 لشهر أغسطس 2026."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_custom_report",
            "description": "Automate the 'توليد الآن' (Generate Now) button in the Ad-Hoc Report Builder on the Reports page (/reports). Generates custom aggregated reports by filtering data source, period, grouping dimension, and export format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Data source: 'الحوادث والبلاغات', 'تصاريح العمل', 'جولات التفتيش', 'معدات الحريق', 'التدريب والكفاءات', 'المواد الكيميائية', 'الصحة المهنية', 'سجل المخاطر'", "default": "الحوادث والبلاغات"},
                    "period": {"type": "string", "description": "Time period: 'هذا الشهر', 'الربع الحالي', 'سنة حتى تاريخه (YTD)', 'فترة مخصصة'", "default": "هذا الشهر"},
                    "group_by": {"type": "string", "description": "Grouping dimension: 'القسم / المنطقة', 'النوع', 'الشدة', 'المسؤول', 'الشهر'", "default": "القسم / المنطقة"},
                    "format": {"type": "string", "description": "Export format: 'Excel (XLSX)', 'PDF', 'CSV'", "default": "Excel (XLSX)"},
                    "recipients": {"type": "string", "description": "Optional recipient emails", "default": "hse@elsewedy.com; plant.manager@elsewedy.com"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_ready_report",
            "description": "Automate inspecting and opening any of the 6 official ready report cards on the Reports page (/reports): 'monthly' (الشهري), 'incidents' (تحليل الحوادث), 'fire' (جاهزية الحريق), 'competency' (الكفاءات والتدريب), 'risk' (سجل المخاطر HIRA), or 'iso' (حزمة التدقيق ISO 45001).",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_id": {"type": "string", "description": "Ready report ID or topic: 'monthly', 'incidents', 'fire', 'competency', 'risk', 'iso'", "default": "monthly"}
                },
                "required": ["report_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_report",
            "description": "Automate the 'حفظ كتقرير مجدول' (Save as Scheduled Report) button on the Reports page (/reports). Activates recurring scheduled distribution of HSE reports to management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_source": {"type": "string", "description": "Data source to schedule", "default": "الحوادث والبلاغات"},
                    "frequency": {"type": "string", "description": "Schedule frequency: 'يومي — 07:00', 'أسبوعي — الأحد 08:00', 'شهري — أول يوم عمل'", "default": "شهري — أول يوم عمل"},
                    "recipients": {"type": "string", "description": "Recipient emails", "default": "plant.manager@elsewedy.com; ceo@elsewedy.com"},
                    "format": {"type": "string", "description": "Report format: 'Excel (XLSX)', 'PDF', 'CSV'", "default": "Excel (XLSX)"}
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
    {
        "type": "function",
        "function": {
            "name": "export_incidents_excel",
            "description": "EXPORT: Generate and export the complete HSE incident register to Excel/CSV with columns: ID, date, time, zone, incident type, title, description, severity, injured employee, status, investigation owner, lost work days, immediate action, and RCA details. (Arabic: تصدير سجل الحوادث إلى إكسل, تصدير Excel, تحميل ملف Excel للحوادث).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Optional filter: ALL, OPEN, INVESTIGATING, CLOSED"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Optional zone filter"},
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Optional severity filter: MINOR, MODERATE, MAJOR, CRITICAL"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_incidents",
            "description": "EXPORT: Alias for export_incidents_excel to export incident register records to Excel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Optional filter: ALL, OPEN, INVESTIGATING, CLOSED"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Optional zone filter"},
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Optional severity filter: MINOR, MODERATE, MAJOR, CRITICAL"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_external_report_template",
            "description": "COMPLIANCE & LEGAL TEMPLATES: Generate official statutory external reporting documents for government, insurance, and environmental bodies. Supports: 'LABOR_OFFICE' (نموذج مكتب العمل - إخطار إصابة عمل حسب قانون العمل 12 لسنة 2003), 'SOCIAL_INSURANCE' (نموذج التأمينات الاجتماعية - إخطار عن وقوع إصابة عمل حسب قانون 148 لسنة 2019), 'INSURANCE_CLAIM' (مطالبة شركة التأمين للتعويض عن أضرار/إصابة), 'ENVIRONMENTAL_AGENCY' (إخطار جهاز شؤون البيئة EEAA عن حوادث التسريب والانبعاثات حسب قانون البيئة 4 لسنة 1994). (Arabic: توليد نموذج مكتب العمل, نموذج التأمينات الاجتماعية, مطالبة شركة التأمين, إخطار جهاز شؤون البيئة, قوالب الإبلاغ الخارجي).",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_type": {
                        "type": "string",
                        "description": "Template code: 'LABOR_OFFICE' (مكتب العمل), 'SOCIAL_INSURANCE' (التأمينات الاجتماعية), 'INSURANCE_CLAIM' (مطالبة التأمين), 'ENVIRONMENTAL_AGENCY' (شؤون البيئة)"
                    },
                    "incident_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Optional linked incident ID (e.g. 1 or 'INC-001') to auto-fill official incident details"
                    },
                    "injured_employee": {
                        "anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}],
                        "description": "Optional employee name or ID"
                    },
                    "notes": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Optional special notes or statutory statements"
                    }
                },
                "required": ["template_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_incident_rca",
            "description": "CRUD CREATE / UPDATE: Record or update Root Cause Analysis (RCA) investigation for an incident with methodology (5-Whys, Fishbone / Ishikawa), problem statement, primary cause category, root cause, and contributing factors. (Arabic: تسجيل تحليل السبب الجذري, توثيق RCA للحادث, إضافة تحليل السبب الجذري).",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "integer", "description": "Incident ID"},
                    "problem_statement": {"type": "string", "description": "Accurate description of the failure / problem statement"},
                    "root_cause": {"type": "string", "description": "The determined root cause verified by the investigation"},
                    "method": {"type": "string", "description": "Methodology used: '5-Whys', 'Fishbone (Ishikawa)', '5 Whys + Fishbone'", "default": "5 Whys + Fishbone (Ishikawa)"},
                    "primary_cause_category": {"type": "string", "description": "Category: 'سلوكات وأخطاء بشرية', 'قصور في إجراءات وتصاريح العمل', 'أعطال ميكانيكية ومعدات', 'بيئة العمل والظروف الجوية'", "default": "قصور في إجراءات وتصاريح العمل"},
                    "contributing_factors": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Secondary contributing factors or conditions"},
                    "completed_by": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Employee ID or name of the lead investigator", "default": 1}
                },
                "required": ["incident_id", "root_cause"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_root_causes_summary",
            "description": "READ: Retrieve Year-To-Date (YTD) root causes distribution percentages, category breakdown (Behaviors 38%, Procedures/Permits 27%, Mechanical failures 22%, Work environment 13%), and recurring trends. (Arabic: تحليل الأسباب الجذرية YTD, نسب أسباب الحوادث, ملخص الأسباب الجذرية).",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"type": "integer", "description": "Year to evaluate (e.g. 2026)", "default": 2026}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "refresh_dashboard",
            "description": "REAL-TIME SYNC & REFRESH: Trigger a live recalculation and refresh of executive dashboard KPIs, days without LTI streak, open incidents, overdue CAPAs, TRIR metrics, and zone safety scores. (Arabic: تحديث لوحة القيادة, تحديث البيانات, إعادة حساب مؤشرات السلامة).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

    # ── 5. Electronic Permits to Work (ePTW) & SIMOPS Module ───────────────────
    {
        "type": "function",
        "function": {
            "name": "create_permit",
            "description": "CRUD CREATE: Issue and register a new electronic Permit to Work (ePTW) in the Railway database. Supports Hot Work, Confined Space, Working at Heights, Electrical Isolation, Mechanical LOTO, Excavation, and Radiography. (Arabic: اصدار تصريح عمل, انشاء تصريح عمل ساخن, تصريح دخول اماكن مغلقة, تصريح مرتفعات).",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_type": {
                        "type": "string",
                        "description": "Permit type: 'HOT_WORK' (عمل ساخن), 'CONFINED_SPACE' (أماكن مغلقة), 'WORK_AT_HEIGHT' (مرتفعات), 'ELECTRICAL' (كهربائي), 'MECHANICAL_LOTO' (ميكانيكي / عزل), 'EXCAVATION' (حفر), 'RADIOGRAPHY' (إشعاعي)."
                    },
                    "work_description": {
                        "type": "string",
                        "description": "Detailed description of the authorized work and task scope"
                    },
                    "zone_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Zone ID (1-10) or zone name (e.g. 'خطوط العزل CCV', 'عنبر 1', 'Zone 2')",
                        "default": 1
                    },
                    "requester_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Employee ID or name requesting the permit (e.g. 1 or 'أحمد سامي')",
                        "default": 1
                    },
                    "issuer_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "HSE Officer / Issuer employee ID or name authorized to issue",
                        "default": 1
                    },
                    "executor_name": {
                        "type": "string",
                        "description": "Contractor or internal technician lead executing the work",
                        "default": "Internal Maintenance Team"
                    },
                    "risk_level": {
                        "type": "string",
                        "description": "Risk level: 'LOW' (منخفض), 'MEDIUM' (متوسط), 'HIGH' (عالي), 'CRITICAL' (حرج)",
                        "default": "HIGH"
                    },
                    "duration_hours": {
                        "type": "integer",
                        "description": "Validity duration in hours (e.g. 8 for shift, 24, 48)",
                        "default": 8
                    },
                    "jsa_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Optional linked Job Safety Analysis ID (e.g. 1 or 'JSA-001')"
                    },
                    "gas_test_required": {
                        "type": "boolean",
                        "description": "True if pre-entry atmospheric gas testing is required (mandatory for Confined Space and Hot Work)",
                        "default": False
                    },
                    "gas_o2": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "description": "Oxygen level % (safe range: 19.5% - 23.5%, default 20.9%)"
                    },
                    "gas_lel": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "description": "Combustible gas % LEL (must be < 10% LEL, default 0)"
                    },
                    "gas_h2s": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "description": "Hydrogen Sulfide H2S ppm (must be < 10 ppm, default 0)"
                    },
                    "gas_co": {
                        "anyOf": [{"type": "number"}, {"type": "null"}],
                        "description": "Carbon Monoxide CO ppm (must be < 35 ppm, default 0)"
                    },
                    "precautions": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Mandatory safety precautions, PPE, and fire watcher assignments"
                    },
                    "status": {
                        "type": "string",
                        "description": "Initial status: 'ACTIVE' (معتمد/نشط) or 'PENDING_APPROVAL' (بانتظار الموافقة)",
                        "default": "ACTIVE"
                    }
                },
                "required": ["permit_type", "work_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_permits",
            "description": "CRUD READ: Query and list electronic permits to work (ePTW) filtered by status, risk level, permit type, zone, or expiry status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Filter by status: 'ACTIVE' (نشط), 'PENDING_APPROVAL' (بانتظار الموافقة), 'APPROVED' (معتمد), 'SUSPENDED' (موقوف), 'CLOSED' (مغلق), 'EXPIRED' (منتهي), 'CANCELLED' (ملغي), 'REJECTED' (مرفوض)"
                    },
                    "permit_type": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Filter by type: 'HOT_WORK', 'CONFINED_SPACE', 'WORK_AT_HEIGHT', 'ELECTRICAL', 'MECHANICAL_LOTO', 'EXCAVATION', 'RADIOGRAPHY'"
                    },
                    "zone_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Filter by zone ID or zone name"
                    },
                    "risk_level": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Filter by risk level: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'"
                    },
                    "expiring_soon": {
                        "type": "boolean",
                        "description": "If True, returns active permits expiring within 6 hours or today"
                    },
                    "query": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Search keyword in work description, contractor, or PTW ID"
                    },
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_permit_details",
            "description": "CRUD READ: Get comprehensive permit details: gas test records, supervisor approvals, safety checklist confirmations, remaining hours to expiry, and zone SIMOPS status by ID (e.g. 5 or 'PTW-005').",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit numeric ID or code (e.g. 10, 'PTW-010', 'PTW-2026-0418')"
                    }
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_permit_status",
            "description": "CRUD UPDATE: Transition permit lifecycle (APPROVE, ACTIVATE, SUSPEND, CLOSE, CANCEL, REJECT, EXTEND) in the Railway database with audit logging.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit ID to update (e.g. 10 or 'PTW-010')"
                    },
                    "status": {
                        "type": "string",
                        "description": "Target status: 'APPROVED' / 'ACTIVE' (اعتماد/تفعيل), 'SUSPENDED' (تعليق/إيقاف), 'CLOSED' (إغلاق/إنهاء), 'CANCELLED' (إلغاء), 'REJECTED' (رفض)"
                    },
                    "reason_or_note": {
                        "type": "string",
                        "description": "Approval sign-off note, suspension hazard reason, or work completion sign-off",
                        "default": "Status updated by HSE Authority"
                    },
                    "approver_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Employee ID or name authorizing the status change"
                    }
                },
                "required": ["permit_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "approve_permit",
            "description": "CRUD UPDATE / APPROVAL: Approve an Electronic Permit to Work (ePTW) by authorized manager.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit ID or code to approve (e.g. 10 or 'PTW-010')"
                    },
                    "reason_or_note": {
                        "type": "string",
                        "description": "Approval authorization note and safety prerequisites sign-off",
                        "default": "Approved by Authorized Manager"
                    }
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_permit",
            "description": "CRUD UPDATE: Activate an approved Electronic Permit to Work (ePTW) for immediate field execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit ID or code to activate"
                    },
                    "reason_or_note": {
                        "type": "string",
                        "description": "Activation note and toolbox talk confirmation",
                        "default": "Activated for work execution"
                    }
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_permit",
            "description": "CRUD UPDATE / CLOSURE: Safely close and sign-off an active permit upon job completion and site housekeeping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit ID or code to close"
                    },
                    "reason_or_note": {
                        "type": "string",
                        "description": "Work completion and site handover sign-off note",
                        "default": "Work completed and site left safe and clean"
                    }
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_permit",
            "description": "CRUD UPDATE: Update permit attributes such as location/zone, work description, executor/contractor, risk level, duration extension, or linked JSA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit ID or code to update (e.g. 73 or 'PTW-073')"
                    },
                    "location": {
                        "anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}],
                        "description": "New location or zone name/ID (e.g. 'production line b', 'خط الإنتاج B', 2)"
                    },
                    "zone_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Zone ID or name (e.g. 2, 'Line B')"
                    },
                    "work_description": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Updated work or activity description"
                    },
                    "executor_name": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Updated contractor or executing technician name"
                    },
                    "risk_level": {
                        "anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}],
                        "description": "Updated risk level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')"
                    },
                    "permit_type": {
                        "anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}],
                        "description": "Updated permit type ('HOT_WORK', 'ELECTRICAL', 'CONFINED_SPACE', etc.)"
                    },
                    "duration_hours": {
                        "anyOf": [{"type": "integer"}, {"type": "number"}, {"type": "null"}],
                        "description": "Total validity duration in hours"
                    },
                    "extend_hours": {
                        "anyOf": [{"type": "integer"}, {"type": "number"}, {"type": "null"}],
                        "description": "Additional hours to extend the existing permit validity"
                    },
                    "jsa_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Linked JSA ID"
                    }
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_permit",
            "description": "CRUD DELETE: Safely delete or purge a permit record from the Railway database (Restricted to Admin & HSE Manager).",
            "parameters": {
                "type": "object",
                "properties": {
                    "permit_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Permit ID or code to delete (e.g. 75, 'PTW-075', '75')"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional administrative reason or notes for the audit log (default: 'Requested by user')",
                        "default": "Requested by user"
                    }
                },
                "required": ["permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_all_permits",
            "description": "CRUD BULK UPDATE: Close all active and suspended permits in the factory and hand over work sites (e.g. 'اغلق كافة التصاريح', 'إغلاق جميع التصاريح', 'close all permits').",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for bulk permit closing (e.g. 'End of shift site handover' or 'إغلاق وتسليم الموقع')",
                        "default": "إغلاق جماعي لكافة تصاريح العمل وتسليم المواقع"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_all_permits",
            "description": "CRUD BULK DELETE: Permanently delete all permits from database (Restricted to Admin & HSE Manager).",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Administrative rationale for bulk permit deletion",
                        "default": "Administrative bulk deletion requested by user"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_simops_conflicts",
            "description": "SIMOPS Conflict Detection: Evaluates simultaneous operations hazards by identifying conflicting active permits in the same factory zone (e.g. Hot Work vs Flammable Chemicals, Confined Space vs Radiography).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}],
                        "description": "Optional zone ID or zone name to check specifically"
                    },
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
            "description": "CRUD CREATE: Schedule or book a future safety walkthrough, periodic audit, or compliance inspection in a plant zone. (Arabic: جدولة فحص سلامة, جدولة جولة تفتيش, جدول جولة, تحديد موعد معاينة, حجز تفتيش).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_type": {"type": "string", "description": "Inspection type (e.g. 'تفتيش السلامة الأسبوعي لمصنع الكابلات', 'ROUTINE_WALK', 'FIRE_SAFETY', 'ELECTRICAL_AUDIT', 'ISO_45001_AUDIT', 'HOUSEKEEPING', 'PPE_COMPLIANCE')", "default": "تفتيش السلامة الأسبوعي لمصنع الكابلات"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Zone/Area ID or name (e.g. 'خطوط العزل CCV', 'عنبر السحب والجدل', 1, 'Zone 1')", "default": 1},
                    "lead_inspector_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Lead inspector employee ID or name (e.g. 'م. مصطفى (مدير السلامة)', 'م. كريم حسني', 1)"},
                    "frequency": {"type": "string", "description": "Recurrence frequency (e.g. 'أسبوعي (Weekly)', 'شهري (Monthly)', 'يومي (Daily)', 'ربع سنوي (Quarterly)')", "default": "أسبوعي"},
                    "scheduled_at": {"type": "string", "description": "Scheduled date / next walk date (e.g. '2026-08-31', '08/31/2026', 'tomorrow', 'next week')"},
                    "scheduled_in_days": {"type": "integer", "description": "Days from now if relative (e.g. 1, 7, 30)", "default": 7},
                    "template": {"type": "string", "description": "Approved checklist standard/template (e.g. 'ISO 45001 — تدقيق السلامة والصحة المهنية', 'ISO 14001', 'OSHA General Industry', 'NFPA', 'BBS', '5S')", "default": "ISO 45001 — تدقيق السلامة والصحة المهنية"},
                    "notes": {"type": "string", "description": "Scope notes, special directions, or focus points", "default": "جولة تفتيش دورية مجدولة"}
                },
                "required": ["inspection_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_inspection_walk",
            "description": "CRUD CREATE: Submit, complete, and certify a live inspection walkthrough with compliance score %, template version, checklist items evaluation, and non-conformance findings. (Arabic: بدء جولة تفتيش, تسجيل جولة ميدانية, اعتماد جولة تفتيش, إنهاء تفتيش).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_type": {"type": "string", "description": "Inspection type (e.g. 'تفتيش السلامة الميداني الشامل', 'ROUTINE_WALK', 'ISO_45001_AUDIT', 'FIRE_SAFETY')", "default": "تفتيش السلامة الميداني الشامل"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Zone/Area ID or name (e.g. 'خطوط العزل CCV', 1)", "default": 1},
                    "lead_inspector_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Lead inspector employee ID or name", "default": 1},
                    "score_pct": {"type": "number", "description": "Compliance score percentage (e.g. 95.0, 100.0)", "default": 95.0},
                    "checklist_version": {"type": "string", "description": "Checklist template standard/version (e.g. 'ISO 45001 — تدقيق السلامة والصحة المهنية')", "default": "ISO 45001 — تدقيق السلامة والصحة المهنية"},
                    "notes": {"type": "string", "description": "Walk summary notes and recommendations", "default": "تم استكمال الجولة الميدانية وتسجيل نتائج الفحص بنجاح"},
                    "checklist": {
                        "type": "array",
                        "description": "Evaluated checklist items with status PASS, FAIL, or NA",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "status": {"type": "string", "description": "PASS, FAIL, NA"}
                            }
                        }
                    },
                    "findings": {
                        "type": "array",
                        "description": "Non-conformance findings observed during the walk (auto-creates CAPA actions)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "category": {"type": "string", "default": "بيئة العمل والسلامة الميدانية"},
                                "severity": {"type": "string", "description": "CRITICAL, MAJOR, MINOR", "default": "MAJOR"},
                                "due_days": {"type": "integer", "default": 7}
                            }
                        }
                    }
                },
                "required": ["inspection_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_inspections",
            "description": "List safety inspections and audits with compliance score percentages, status, zone, and inspector. (Arabic: قائمة جولات التفتيش, سجل الفحص, استعلام المعاينات).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Filter by status: SCHEDULED, IN_PROGRESS, COMPLETED"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Filter by Zone ID or name"},
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inspection_details",
            "description": "Get complete detailed view of a specific inspection record by ID, including its zone, inspector, score, and all linked non-conformance findings. (Arabic: تفاصيل التفتيش, بيانات جولة الفحص).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Primary Key ID of inspection"}
                },
                "required": ["inspection_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inspection_stats",
            "description": "Get aggregated statistics, compliance scores %, completed vs scheduled ratio, and open/overdue findings for the Inspections module. (Arabic: إحصائيات التفتيش, نسبة امتثال الجولات).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_inspection_status",
            "description": "CRUD UPDATE: Complete or update an inspection status, compliance score percentage, and closing notes. (Arabic: إنهاء التفتيش, تحديث حالة الفحص, اعتماد نتيجة التفتيش).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Inspection ID"},
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
            "name": "update_inspection",
            "description": "CRUD UPDATE: Update inspection metadata such as type, zone, inspector, schedule date, notes, or score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Inspection ID to update"},
                    "inspection_type": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated type"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Updated zone ID or name"},
                    "lead_inspector_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Updated lead inspector"},
                    "scheduled_at": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated schedule timestamp"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated notes"},
                    "score_pct": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Updated score percentage"}
                },
                "required": ["inspection_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_inspection",
            "description": "CRUD DELETE: Safely delete an inspection record and remove/unlink associated findings with audit trail. (Arabic: حذف جولة التفتيش, مسح التفتيش).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Inspection ID to delete"},
                    "reason": {"type": "string", "description": "Justification reason for deletion", "default": "Requested by user"}
                },
                "required": ["inspection_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_inspection_finding",
            "description": "CRUD CREATE: Log a non-conformance or safety finding during an inspection, with responsible person, due date, and automated CAPA triggering. (Arabic: تسجيل ملاحظة تفتيش, رصد مخالفة, تقييد عدم مطابقة).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Inspection ID"},
                    "category": {"type": "string", "description": "Finding category (e.g. PPE, HOUSEKEEPING, ELECTRICAL, FIRE, WORK_AT_HEIGHT)", "default": "HOUSEKEEPING"},
                    "description": {"type": "string", "description": "Factual finding description"},
                    "severity": {"type": "string", "description": "MINOR, MODERATE, MAJOR, CRITICAL", "default": "MODERATE"},
                    "responsible_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Employee ID or name responsible for fixing", "default": 1},
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
            "description": "List non-conformance findings across inspections, filtered by severity, status, or inspection ID. (Arabic: قائمة ملاحظات التفتيش, مخالفات الفحص المفتوحة).",
            "parameters": {
                "type": "object",
                "properties": {
                    "inspection_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
                    "category": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 15}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_inspection_finding",
            "description": "CRUD UPDATE: Update finding status (e.g. CLOSED, OPEN, IN_PROGRESS), severity, responsible employee, or notes. (Arabic: إغلاق ملاحظة التفتيش, معالجة المخالفة, تحديث الملاحظة).",
            "parameters": {
                "type": "object",
                "properties": {
                    "finding_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Finding ID to update"},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "CLOSED, IN_PROGRESS, OPEN"},
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "MINOR, MODERATE, MAJOR, CRITICAL"},
                    "description": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated finding description"},
                    "responsible_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Updated responsible person"},
                    "due_date": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated due date (YYYY-MM-DD)"}
                },
                "required": ["finding_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_inspection_finding",
            "description": "CRUD DELETE: Safely delete a specific inspection non-conformance finding. (Arabic: حذف ملاحظة التفتيش).",
            "parameters": {
                "type": "object",
                "properties": {
                    "finding_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Finding ID to delete"},
                    "reason": {"type": "string", "description": "Justification reason", "default": "Requested by user"}
                },
                "required": ["finding_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_inspection_templates",
            "description": "List standard inspection checklists and audit templates (e.g. Daily Walkthrough, ISO 45001, Electrical Safety, 5S, BBS).",
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
            "name": "generate_inspection_checklist",
            "description": "AI standards-compliant checklist advisor: generates checklist checkpoints tailored to a zone and standard (ISO 45001, OSHA 1910, NFPA, 5S, BBS). (Arabic: توليد قائمة فحص, اقتراح بنود تفتيش).",
            "parameters": {
                "type": "object",
                "properties": {
                    "standard": {"type": "string", "description": "ISO_45001, OSHA_1910, NFPA, 5S, BBS", "default": "ISO_45001"},
                    "zone_name": {"type": "string", "description": "Factory zone name", "default": "خطوط العزل CCV"},
                    "hazard_focus": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Specific hazard focus if any"}
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
    {
        "type": "function",
        "function": {
            "name": "get_risk_assessment_details",
            "description": "Get detailed risk assessment record: hazard, activity, inherent vs residual scores, control hierarchy, and review dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_id": {"type": "integer", "description": "Risk ID"}
                },
                "required": ["risk_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_risk_assessment",
            "description": "CRUD DELETE: Delete a hazard entry from the Risk Register.",
            "parameters": {
                "type": "object",
                "properties": {
                    "risk_id": {"type": "integer", "description": "Risk ID to delete"}
                },
                "required": ["risk_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_residual_risk",
            "description": "Calculate hierarchy-of-controls risk reduction percentage and new residual risk score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "likelihood": {"type": "integer", "description": "Initial likelihood (1-5)", "default": 4},
                    "severity": {"type": "integer", "description": "Initial severity (1-5)", "default": 4},
                    "engineering_control": {"type": "boolean", "default": True},
                    "administrative_control": {"type": "boolean", "default": True},
                    "ppe_control": {"type": "boolean", "default": True}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_high_risk_hazards",
            "description": "Query critical and high-risk hazards from the Risk Register requiring immediate mitigation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_score": {"type": "integer", "default": 10},
                    "limit": {"type": "integer", "default": 10}
                }
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
    {
        "type": "function",
        "function": {
            "name": "delete_jsa",
            "description": "CRUD DELETE: Delete a JSA document and all its sequence steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jsa_id": {"type": "integer", "description": "JSA ID to delete"}
                },
                "required": ["jsa_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_jsa_step",
            "description": "CRUD CREATE: Add a sequential task step with hazards and controls to an existing JSA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jsa_id": {"type": "integer", "description": "JSA ID"},
                    "step_description": {"type": "string", "description": "Description of the specific activity step"},
                    "potential_hazards": {"type": "string", "description": "Hazards identified in this step"},
                    "control_measures": {"type": "string", "description": "Mandatory safety control measures for this step"},
                    "step_no": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                },
                "required": ["jsa_id", "step_description", "potential_hazards", "control_measures"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_jsa_step",
            "description": "CRUD UPDATE: Edit a specific task step in a JSA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "integer", "description": "JSA Step ID"},
                    "step_description": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "potential_hazards": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "control_measures": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["step_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_jsa_step",
            "description": "CRUD DELETE: Delete a specific step from a JSA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step_id": {"type": "integer", "description": "JSA Step ID to remove"}
                },
                "required": ["step_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "link_jsa_permit",
            "description": "Link a JSA document to an active Work Permit (ePTW).",
            "parameters": {
                "type": "object",
                "properties": {
                    "jsa_id": {"type": "integer", "description": "JSA ID"},
                    "permit_id": {"type": "integer", "description": "Permit ID"}
                },
                "required": ["jsa_id", "permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unlink_jsa_permit",
            "description": "Unlink a JSA document from a Work Permit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "jsa_id": {"type": "integer", "description": "JSA ID"},
                    "permit_id": {"type": "integer", "description": "Permit ID"}
                },
                "required": ["jsa_id", "permit_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_permits_for_jsa",
            "description": "List active work permits in a zone that require or can be linked to a JSA.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "limit": {"type": "integer", "default": 10}
                }
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
            "name": "create_ppe_supply_order",
            "description": "CRUD CREATE: Automatically raise or create an official PPE Supply Order / Reorder Request (طلب توريد مهمات الوقاية) for items below reorder threshold or specific PPE catalog items. Calculates deficits, replenishment batch quantities, and assigned suppliers. (Arabic: رفع طلب توريد, طلب شراء مهمات وقاية, إعادة طلب الأصناف الناقصة).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ppe_item_ids": {
                        "anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "string"}, {"type": "null"}],
                        "description": "Optional list or comma-separated item codes/IDs (e.g. ['PPE-EY-01', 'PPE-HD-01']). Omit to automatically scan and order all items below reorder threshold."
                    },
                    "order_notes": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Justification or procurement order notes (e.g. 'طلب توريد عاجل لسد عجز المخزن وبدء الوردية الجديدة')"
                    },
                    "urgency": {
                        "type": "string",
                        "description": "STANDARD, URGENT, EMERGENCY",
                        "default": "STANDARD"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_ppe_item",
            "description": "CRUD CREATE: Add and register a new PPE item in the catalog inventory (e.g. safety helmets, cut-resistant gloves, steel-toe boots, respirators, safety goggles). (Arabic: إضافة صنف وقاية جديد, تسجيل صنف مهمات).",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_code": {"type": "string", "description": "Unique PPE item code (e.g. 'PPE-HD-05', 'PPE-HLM-02')"},
                    "name_ar": {"type": "string", "description": "Arabic item title (e.g. 'خوذة حماية كهربائية 20kV', 'نظارة واقية كيميائية')"},
                    "category": {"type": "string", "description": "HEAD, HANDS, EYES, FEET, FACE, HEARING, RESPIRATORY, BODY, FALL_PROTECTION", "default": "HEAD"},
                    "unit": {"type": "string", "description": "Unit of measure (e.g. 'Piece', 'Pair', 'Box', 'قطعة (pcs)')", "default": "Piece"},
                    "balance_qty": {"type": "number", "description": "Initial physical stock quantity count", "default": 50.0},
                    "reorder_threshold": {"type": "number", "description": "Reorder alert trigger threshold quantity", "default": 15.0},
                    "monthly_consumption": {"type": "number", "description": "Average monthly consumption rate", "default": 10.0},
                    "supplier": {"type": "string", "description": "Approved supplier name", "default": "Safety Supply Co"},
                    "storage_zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Storage warehouse zone ID or name (1-10)", "default": 5}
                },
                "required": ["item_code", "name_ar"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ppe_item",
            "description": "CRUD UPDATE: Modify catalog details, specifications, monthly consumption, supplier, or zone of an existing PPE item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ppe_item_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "PPE Item ID, Item Code (e.g. 'PPE-HD-01'), or Arabic name"},
                    "name_ar": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated Arabic title"},
                    "item_code": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated item code"},
                    "category": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "HEAD, HANDS, EYES, FEET, FACE, HEARING, RESPIRATORY, BODY, FALL_PROTECTION"},
                    "unit": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Unit of measure"},
                    "balance_qty": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Updated stock count"},
                    "reorder_threshold": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Updated reorder threshold"},
                    "monthly_consumption": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Updated monthly consumption rate"},
                    "supplier": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Updated supplier name"},
                    "storage_zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Updated warehouse zone"}
                },
                "required": ["ppe_item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_ppe_item",
            "description": "CRUD DELETE: Safely delete a PPE item from catalog inventory (validates that no transaction history is attached).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ppe_item_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "PPE Item ID, Item Code, or name to delete"}
                },
                "required": ["ppe_item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_inventory",
            "description": "List PPE items (masks, gloves, helmets, safety shoes, goggles) with current stock balances, reorder thresholds, and consumption rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Optional category filter: HEAD, HANDS, EYES, FEET, RESPIRATORY, BODY"},
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
            "description": "CRUD UPDATE: Set or update zone mandatory PPE requirements in the PPE Zone Matrix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "integer", "description": "Zone ID (1-10)"},
                    "ppe_item_id": {"type": "integer", "description": "PPE Item ID"},
                    "required_flag": {"type": "integer", "description": "1 for Required, 0 for Optional/Task-based", "default": 1},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["zone_id", "ppe_item_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_ppe_matrix_rule",
            "description": "CRUD DELETE: Remove a zone PPE requirement rule from the PPE Matrix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "matrix_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Matrix rule ID"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Zone ID"},
                    "ppe_item_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "PPE Item ID"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_ppe_stock",
            "description": "CRUD UPDATE: Update PPE stock balance physical quantity or reorder threshold directly in inventory.",
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
            "description": "CRUD CREATE: Log and execute a PPE transaction: ISSUE (صرف لموظف - خصم من الرصيد) or RETURN (إرجاع للمخزن - إضافة للرصيد). Validates available balance, updates live inventory, links to work permits, and logs audit trail. (Arabic: صرف مهمات وقاية, تسجيل إرجاع مهمة, تسليم مهمات للموظف).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ppe_item_id": {
                        "anyOf": [{"type": "integer"}, {"type": "string"}],
                        "description": "Target PPE Item. Exact Catalog Codes: 'PPE-EY-01' (Safety Glasses / Goggles / نظارة واقية), 'PPE-HD-01' (Safety Helmet / Hard Hat / خوذة أمان), 'PPE-SH-01' (Safety Shoes / Boots / حذاء أمان), 'PPE-GL-05' (Cut-Resistant Gloves / قفاز مقاوم للقطع), 'PPE-EL-01' (Electrical 1000V Gloves / قفاز عازل), 'PPE-ER-01' (Earplugs / Earmuffs / واقي أذن), 'PPE-RP-01' (Half-Face Mask / Respirator / كمامة نصف وجه), 'PPE-FR-01' (FR Coverall / أفرول), 'PPE-HR-01' (Full Body Harness / حزام أمان), 'PPE-FS-01' (Face Shield / درع وجه), or numeric item ID (1-19).",
                        "default": 1
                    },
                    "employee_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Employee ID, code (e.g. 'EMP-001'), or name (e.g. 'أحمد سامي', 'Ahmed Samy')", "default": 1},
                    "quantity": {"type": "integer", "description": "Quantity issued or returned (must be >= 1)", "default": 1},
                    "transaction_type": {"type": "string", "description": "ISSUE (صرف لموظف) or RETURN (إرجاع للمخزن)", "default": "ISSUE"},
                    "reason": {"type": "string", "description": "Reason for issuance or return (e.g. 'صرف دوري لبدء وردية العمل', 'استبدال تالف', 'إرجاع عهدة')", "default": "صرف دوري لبدء وردية العمل"},
                    "permit_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Associated Work Permit ID or Code (e.g. 'PTW-2026-041', 10)"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Additional notes"}
                },
                "required": ["quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_ppe_transaction",
            "description": "CRUD DELETE: Cancel/revert a previously logged PPE transaction and restore the physical inventory stock balance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "integer", "description": "Transaction ID to revert"}
                },
                "required": ["transaction_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_transactions",
            "description": "List PPE transaction and issuance history by employee, PPE item, or transaction type.",
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
            "description": "CRUD CREATE: Register a fixed safety asset (e.g. Emergency Eyewash Station, Emergency Shower, AED Defibrillator, LOTO Station, First Aid Box). (Arabic: تسجيل معدة سلامة ثابتة, محطة غسيل عيون, دش طوارئ).",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_name": {"type": "string", "description": "Name/description of asset (e.g. 'محطة غسيل عيون طوارئ عنبر 2', 'دش الطوارئ للتعامل مع الكيماويات')"},
                    "asset_type": {"type": "string", "description": "EYEWASH, SHOWER, EMERGENCY_SHOWER, AED, FIRST_AID, LOTO_STATION, ASSEMBLY_POINT", "default": "EYEWASH"},
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
            "name": "record_fixed_safety_asset_inspection",
            "description": "CRUD UPDATE/LOG: Record routine testing and inspection for fixed safety assets (Emergency Eyewash Stations, Emergency Showers, AED Defibrillators, First Aid Kits). Updates test date, next inspection date, and readiness. (Arabic: فحص محطة غسيل العيون, اختبار دش الطوارئ, فحص أجهزة الصدمات AED).",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_summary_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Fixed safety asset ID or name (e.g. 1, 'Emergency shower / eyewash', 'محطة غسيل العيون')"},
                    "test_result": {"type": "string", "description": "PASS (صالحة ومطابقة) or FAIL (تحتاج صيانة)", "default": "PASS"},
                    "operational_qty": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Operational working units count"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Inspection and testing notes"},
                    "next_test_days": {"type": "integer", "description": "Days until next scheduled test (default: 30)", "default": 30}
                },
                "required": ["asset_summary_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_fixed_safety_asset",
            "description": "CRUD LOG: Alias for record_fixed_safety_asset_inspection to test and inspect fixed safety assets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_summary_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Fixed safety asset ID or name"},
                    "test_result": {"type": "string", "description": "PASS or FAIL", "default": "PASS"},
                    "operational_qty": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Operational working units count"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Inspection notes"}
                },
                "required": ["asset_summary_id"]
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
            "description": "CRUD CREATE: Log, record, or simulate mobile QR inspection of fire equipment (e.g. 'محاكاة مسح الكود', 'سجل فحص طفاية', 'فحص QR طفاية QR-FE-A-014', 'مسح كود المعدة').",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Fire equipment ID or tag number (e.g. 'QR-FE-A-014', 'FE-A-014', 1)", "default": 1},
                    "inspector_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Inspector employee ID or name", "default": 1},
                    "result": {"type": "string", "description": "PASS, PASS_WITH_ACTION, FAIL", "default": "PASS"},
                    "pressure_ok": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "description": "Pressure gauge in green safe range", "default": True},
                    "hose_ok": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "description": "Discharge hose and nozzle intact", "default": True},
                    "safety_pin_ok": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "description": "Safety pin and tamper seal intact", "default": True},
                    "access_clear": {"anyOf": [{"type": "boolean"}, {"type": "string"}], "description": "Access path free of obstacles", "default": True},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Inspection findings or remediation note"}
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
            "description": "List fixed safety assets (eyewash stations, emergency showers, AEDs, first aid stations) and their operational readiness status.",
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
            "name": "service_fire_equipment",
            "description": "CRUD SERVICE & WORK ORDER: Execute service, refill, or replacement on a fire extinguisher or fire protection equipment (Arabic: استبدال فوري, إعادة تعبئة, أمر شغل صيانة طفاية). Automatically computes new expiry (+5 yrs for REPLACE, +2 yrs for REFILL), updates status to VALID, records work order ID, and logs maintenance inspection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Equipment ID or code (e.g. 'FE-0004', 'FE-0005', 4)"},
                    "action_type": {"type": "string", "description": "REFILL (إعادة تعبئة) or REPLACE (استبدال فوري) or MAINTENANCE", "default": "REFILL"},
                    "technician_name": {"type": "string", "description": "Name of authorized technician or vendor", "default": "م. حسام الدين (فريق الصيانة المعتمد)"},
                    "vendor": {"type": "string", "description": "Vendor / Manufacturer", "default": "Safety Egypt"},
                    "new_expiry_date": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Optional custom new expiry date YYYY-MM-DD"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Maintenance work details or replacement rationale"},
                    "recommission_now": {"type": "boolean", "description": "Whether to immediately recommission the equipment to VALID/ACTIVE status", "default": True}
                },
                "required": ["equipment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_fire_service_order",
            "description": "CRUD SERVICE & WORK ORDER: Alias for service_fire_equipment to create a maintenance/refill/repair work order for fire equipment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Equipment ID or code"},
                    "action_type": {"type": "string", "description": "REFILL or REPLACE or MAINTENANCE", "default": "REFILL"},
                    "technician_name": {"type": "string", "description": "Technician name", "default": "Maintenance Team"},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Service notes"}
                },
                "required": ["equipment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fire_equipment_detail",
            "description": "READ: Inspect full technical profile, location, capacity, zone, status, expiry date, field QR scan code, and recent inspection history for a fire equipment unit (Arabic: تفاصيل معدة الإطفاء, كود المسح الميداني, بيانات الطفاية).",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Equipment ID, code, or QR tag (e.g. 'FE-0031', 'FE-0004', 31)"}
                },
                "required": ["equipment_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fire_readiness_report",
            "description": "READ/REPORT: Generate comprehensive readiness report for all fire equipment, suppression systems, hydrants (pressure 8.5 bar), smoke detectors (62/64 operational), zone readiness percentages, and compliance with NFPA 10/13 and Civil Defense codes (Arabic: تقرير الجاهزية, تقرير جاهزية معدات الحريق, نسبة الجاهزية).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Optional zone filter"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_fire_readiness_report",
            "description": "EXPORT: Alias for get_fire_readiness_report to export the complete Fire Readiness Report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Optional zone filter"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fire_inspection_schedule",
            "description": "READ: Retrieve the periodic fire inspection schedule (15th of every month), inspection routes, testing checklist protocols, and upcoming equipment due for inspection (Arabic: جدول الفحص, جدول الفحص الدوري, مواعيد فحص معدات الإطفاء).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Optional zone filter"},
                    "month": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Target month name or code"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fire_attention_list",
            "description": "READ: List fire equipment requiring immediate attention (expired, damaged, due soon) with recommended corrective actions (Immediate Replacement / Refill) (Arabic: معدات تحتاج انتباه فوري, طفايات منتهية الصلاحية, معدات معيبة).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum records to return", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fire_coverage_by_zone",
            "description": "READ: Get distribution, unit count, serviceable count, and readiness percentage of fire equipment across all factory industrial zones (Zone A, Quality Lab, Zone B, Workshop, Warehouses, Admin, Substation, Shipping, Chem store, Services) (Arabic: تغطية وجاهزية الشبكة حسب المنطقة, تغطية شبكة الإطفاء).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Optional zone filter"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_fire_equipment_stats",
            "description": "READ: Get live executive KPI summary tiles for fire equipment: total, serviceable (ready), expiring in 30 days, expired/damaged, hydrants count (24 @ 8.5 bar), and smoke detectors working status (62/64) (Arabic: إحصائيات معدات الحريق, كواشف الدخان, حنفيات الحريق).",
            "parameters": {
                "type": "object",
                "properties": {}
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
                    "asset_summary_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Asset Summary ID or Name"},
                    "operational_qty": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "total_qty": {"anyOf": [{"type": "integer"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "notes": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["asset_summary_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_fixed_safety_asset",
            "description": "CRUD DELETE: Remove a fixed safety asset record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_summary_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Asset Summary ID or Name to delete"}
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
                    "trade_name": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Commercial product trade name"},
                    "chemical_name": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Scientific chemical formula/name"},
                    "cas_number": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Chemical Abstracts Service (CAS) number (e.g. 67-64-1)"},
                    "supplier": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Supplier/Manufacturer name"},
                    "quantity": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Initial stock quantity", "default": 100.0},
                    "unit": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Unit (Liters, KG, Drums, Cylinders)", "default": "Liters"},
                    "ghs_classes": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "GHS Hazard classes (e.g. Flammable Liquid, Corrosive, Toxic)", "default": "Flammable Liquid"},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}], "description": "Storage Zone ID", "default": 4}
                }
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
                    "chemical_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Chemical ID or trade/scientific name"},
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
                    "chemical_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Chemical ID or trade/scientific name"},
                    "trade_name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "ghs_classes": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                },
                "required": ["chemical_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_chemical_details",
            "description": "Look up complete chemical profile: CAS number, quantity, GHS pictograms, emergency first aid, and storage location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemical_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Chemical ID, trade name, or CAS number"}
                },
                "required": ["chemical_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_chemical",
            "description": "CRUD DELETE: Delete a chemical record from HazMat inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemical_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Chemical ID or name to delete"}
                },
                "required": ["chemical_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_chemical_storage_safety",
            "description": "Audit hazardous chemical storage compatibility and segregation in a factory zone according to NFPA 400 codes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_msds_sheet",
            "description": "Look up Material Safety Data Sheet (MSDS / SDS) 16-section guidelines (first aid, firefighting, spill control, PPE required).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Chemical trade name, scientific name, or CAS number"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_chemical_emergency_guide",
            "description": "Automate Emergency Safety Guide: Immediate first aid, eye-wash protocols, firefighting, required PPE, and spill response for a hazardous chemical.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chemical_id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}], "description": "Chemical ID or name"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_sds_records",
            "description": "List and audit SDS (Safety Data Sheets) archive: view versions, issue dates, expiry status, and emergency files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Filter by chemical name, code, or CAS"},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Filter by CURRENT or EXPIRED"}
                }
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

    # ── 16. Security, Roles, Users & Integrations ─────────────────────────────
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
            "name": "get_role_permissions",
            "description": "Inspect detailed granular permissions and module access for a given role ID or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name_or_id": {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_users",
            "description": "List user accounts, status, MFA adoption, and assigned roles.",
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
            "name": "get_user_details",
            "description": "Look up comprehensive user profile, assigned roles, zone scope, and recent audit activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id_or_username": {"anyOf": [{"type": "integer"}, {"type": "string"}]}
                },
                "required": ["user_id_or_username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_user_role_assignment",
            "description": "CRUD CREATE: Assign a security role or zone scope to a user account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
                    "role_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "default": 2},
                    "zone_id": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                },
                "required": ["user_id", "role_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_role",
            "description": "CRUD UPDATE: Modify user role assignment or active status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
                    "role_id": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
                    "active_status": {"type": "boolean", "default": True}
                },
                "required": ["user_id", "role_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_audit_log_chain",
            "description": "Validate cryptographic SHA-256 integrity of the immutable audit log chain.",
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
            "name": "get_security_audit_summary",
            "description": "Executive security metrics: Active users, MFA adoption, role distributions, and recent audit events.",
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
    {
        "type": "function",
        "function": {
            "name": "get_integration_status",
            "description": "Check live sync status, latency, pending events, and connection health for an enterprise integration connector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "integration_id_or_name": {"anyOf": [{"type": "integer"}, {"type": "string"}]}
                },
                "required": ["integration_id_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sync_integration_connector",
            "description": "Trigger an on-demand batch sync operation for an external integration connector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "integration_id_or_name": {"anyOf": [{"type": "integer"}, {"type": "string"}]}
                },
                "required": ["integration_id_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_integration_connection",
            "description": "Ping endpoint and test authentication handshake for an enterprise integration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "integration_id_or_name": {"anyOf": [{"type": "integer"}, {"type": "string"}]}
                },
                "required": ["integration_id_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_integration_config",
            "description": "CRUD UPDATE: Update integration connector endpoint or scheduling frequency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "integration_id_or_name": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
                    "base_endpoint": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "frequency": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                },
                "required": ["integration_id_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_integration_sync_logs",
            "description": "Retrieve recent integration transaction payloads and outbox processing queue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },

    # ── 17. System Architecture & Diagnostics ─────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_system_architecture",
            "description": "Get complete architectural topology: Microservices, ports, database layers, and IoT hardware pipeline.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service_health_status",
            "description": "Live health check of all microservices (FastAPI, Spring Boot, Vite React, MySQL DB, Groq LLM, Ollama).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_metrics",
            "description": "Query table volumes, records count across 137 database tables, and connection pool status in MySQL.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_api_endpoints_catalog",
            "description": "Catalog of available REST API endpoints across all HSE modules.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trir_ltifr_metrics",
            "description": "Calculate OSHA Total Recordable Incident Rate (TRIR) and Lost Time Injury Frequency Rate (LTIFR) based on safe man-hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "year": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
                }
            }
        }
    },

    # ── 17. Superuser CRUD Delete, Cancel & Direct DML Tools ──────────────────
    {
        "type": "function",
        "function": {
            "name": "delete_record",
            "description": "CRUD DELETE: Safely delete a record from authorized tables (with safety checks and automatic audit log).",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Allowed table: 'incidents', 'permits', 'capa', 'inspections', 'ppe_inventory', 'fire_equipment', 'chemicals', 'risk_register', 'jsa', 'certificates', 'employees', 'health_exams'."
                    },
                    "record_id": {"anyOf": [{"type": "integer"}, {"type": "string"}], "description": "Primary Key ID or reference of the record to delete (e.g. 75, 'PTW-075')"},
                    "reason": {"type": "string", "description": "Optional justification reason for audit log", "default": "Requested by user"}
                },
                "required": ["table_name", "record_id"]
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
,
{
    "type": "function",
    "function": {
        "name": "export_incidents_to_excel",
        "description": "Automated tool for export incidents to excel. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "generate_statutory_incident_report",
        "description": "Automated tool for generate statutory incident report. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "export_hazmat_sds_pdf",
        "description": "Automated tool for export hazmat sds pdf. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "generate_jsa_pdf",
        "description": "Automated tool for generate jsa pdf. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "export_ppe_stock_report",
        "description": "Automated tool for export ppe stock report. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "generate_inspection_walk_report",
        "description": "Automated tool for generate inspection walk report. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "export_risk_register_excel",
        "description": "Automated tool for export risk register excel. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "generate_monthly_hse_report_pdf",
        "description": "Automated tool for generate monthly hse report pdf. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "generate_root_cause_analysis_report",
        "description": "Automated tool for generate root cause analysis report. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "download_iso45001_compliance_report",
        "description": "Automated tool for download iso45001 compliance report. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "export_simops_conflict_report",
        "description": "Automated tool for export simops conflict report. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "generate_occupational_health_summary",
        "description": "Automated tool for generate occupational health summary. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "export_fire_equipment_maintenance_schedule",
        "description": "Automated tool for export fire equipment maintenance schedule. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "download_audit_log_csv",
        "description": "Automated tool for download audit log csv. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "export_safety_dashboard_pdf",
        "description": "Automated tool for export safety dashboard pdf. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "send_report_to_management",
        "description": "Automated tool for send report to management. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "download_training_certificates",
        "description": "Automated tool for download training certificates. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "send_email_notification_to_manager",
        "description": "Automated tool for send email notification to manager. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "schedule_recurring_inspection",
        "description": "Automated tool for schedule recurring inspection. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "trigger_site_wide_evacuation_alarm",
        "description": "Automated tool for trigger site wide evacuation alarm. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_ppe_record",
        "description": "Automated tool for sync ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_ppe_record",
        "description": "Automated tool for validate ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_ppe_record",
        "description": "Automated tool for archive ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_ppe_record",
        "description": "Automated tool for restore ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_ppe_record",
        "description": "Automated tool for approve ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_ppe_record",
        "description": "Automated tool for reject ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_ppe_record",
        "description": "Automated tool for lock ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_ppe_record",
        "description": "Automated tool for unlock ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_ppe_record",
        "description": "Automated tool for escalate ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_ppe_record",
        "description": "Automated tool for summarize ppe record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_incidents_record",
        "description": "Automated tool for sync incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_incidents_record",
        "description": "Automated tool for validate incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_incidents_record",
        "description": "Automated tool for archive incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_incidents_record",
        "description": "Automated tool for restore incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_incidents_record",
        "description": "Automated tool for approve incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_incidents_record",
        "description": "Automated tool for reject incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_incidents_record",
        "description": "Automated tool for lock incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_incidents_record",
        "description": "Automated tool for unlock incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_incidents_record",
        "description": "Automated tool for escalate incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_incidents_record",
        "description": "Automated tool for summarize incidents record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_hazmat_record",
        "description": "Automated tool for sync hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_hazmat_record",
        "description": "Automated tool for validate hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_hazmat_record",
        "description": "Automated tool for archive hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_hazmat_record",
        "description": "Automated tool for restore hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_hazmat_record",
        "description": "Automated tool for approve hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_hazmat_record",
        "description": "Automated tool for reject hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_hazmat_record",
        "description": "Automated tool for lock hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_hazmat_record",
        "description": "Automated tool for unlock hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_hazmat_record",
        "description": "Automated tool for escalate hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_hazmat_record",
        "description": "Automated tool for summarize hazmat record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_fire_equipment_record",
        "description": "Automated tool for sync fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_fire_equipment_record",
        "description": "Automated tool for validate fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_fire_equipment_record",
        "description": "Automated tool for archive fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_fire_equipment_record",
        "description": "Automated tool for restore fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_fire_equipment_record",
        "description": "Automated tool for approve fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_fire_equipment_record",
        "description": "Automated tool for reject fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_fire_equipment_record",
        "description": "Automated tool for lock fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_fire_equipment_record",
        "description": "Automated tool for unlock fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_fire_equipment_record",
        "description": "Automated tool for escalate fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_fire_equipment_record",
        "description": "Automated tool for summarize fire equipment record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_jsa_record",
        "description": "Automated tool for sync jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_jsa_record",
        "description": "Automated tool for validate jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_jsa_record",
        "description": "Automated tool for archive jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_jsa_record",
        "description": "Automated tool for restore jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_jsa_record",
        "description": "Automated tool for approve jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_jsa_record",
        "description": "Automated tool for reject jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_jsa_record",
        "description": "Automated tool for lock jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_jsa_record",
        "description": "Automated tool for unlock jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_jsa_record",
        "description": "Automated tool for escalate jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_jsa_record",
        "description": "Automated tool for summarize jsa record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_inspections_record",
        "description": "Automated tool for sync inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_inspections_record",
        "description": "Automated tool for validate inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_inspections_record",
        "description": "Automated tool for archive inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_inspections_record",
        "description": "Automated tool for restore inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_inspections_record",
        "description": "Automated tool for approve inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_inspections_record",
        "description": "Automated tool for reject inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_inspections_record",
        "description": "Automated tool for lock inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_inspections_record",
        "description": "Automated tool for unlock inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_inspections_record",
        "description": "Automated tool for escalate inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_inspections_record",
        "description": "Automated tool for summarize inspections record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_training_record",
        "description": "Automated tool for sync training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_training_record",
        "description": "Automated tool for validate training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_training_record",
        "description": "Automated tool for archive training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_training_record",
        "description": "Automated tool for restore training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_training_record",
        "description": "Automated tool for approve training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_training_record",
        "description": "Automated tool for reject training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_training_record",
        "description": "Automated tool for lock training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_training_record",
        "description": "Automated tool for unlock training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_training_record",
        "description": "Automated tool for escalate training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_training_record",
        "description": "Automated tool for summarize training record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_reports_record",
        "description": "Automated tool for sync reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_reports_record",
        "description": "Automated tool for validate reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_reports_record",
        "description": "Automated tool for archive reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_reports_record",
        "description": "Automated tool for restore reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_reports_record",
        "description": "Automated tool for approve reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_reports_record",
        "description": "Automated tool for reject reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_reports_record",
        "description": "Automated tool for lock reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_reports_record",
        "description": "Automated tool for unlock reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_reports_record",
        "description": "Automated tool for escalate reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_reports_record",
        "description": "Automated tool for summarize reports record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_iot_record",
        "description": "Automated tool for sync iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_iot_record",
        "description": "Automated tool for validate iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_iot_record",
        "description": "Automated tool for archive iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_iot_record",
        "description": "Automated tool for restore iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_iot_record",
        "description": "Automated tool for approve iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_iot_record",
        "description": "Automated tool for reject iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_iot_record",
        "description": "Automated tool for lock iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_iot_record",
        "description": "Automated tool for unlock iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_iot_record",
        "description": "Automated tool for escalate iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_iot_record",
        "description": "Automated tool for summarize iot record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "sync_security_record",
        "description": "Automated tool for sync security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "validate_security_record",
        "description": "Automated tool for validate security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "archive_security_record",
        "description": "Automated tool for archive security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "restore_security_record",
        "description": "Automated tool for restore security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "approve_security_record",
        "description": "Automated tool for approve security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "reject_security_record",
        "description": "Automated tool for reject security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "lock_security_record",
        "description": "Automated tool for lock security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unlock_security_record",
        "description": "Automated tool for unlock security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "escalate_security_record",
        "description": "Automated tool for escalate security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "summarize_security_record",
        "description": "Automated tool for summarize security record. Fully covers front-end API capability.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the record to process."
                },
                "options": {
                    "type": "string",
                    "description": "Additional JSON string options."
                }
            },
            "required": [
                "id"
            ]
        }
    }
}
]

# For local Ollama models (optimized for rapid function calling on RTX 3050)
LOCAL_TOOLS = list(TOOLS)
