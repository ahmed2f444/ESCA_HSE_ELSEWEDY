"""
Tool (function) definitions handed to the LLM.
Both Groq and Local agents use MySQL exclusively.
Keep this list in sync with app/tools/handlers.py.
"""

# All MySQL-backed, read-only tools available to the AI agent.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_read_only_query",
            "description": "Execute a SQL SELECT query on the MySQL database to fetch records from any table (chemicals, inspections, permits, ppe_inventory, employees, incidents, capa, ai_events, monthly_kpis, risk_register, certificates, etc.). Use for custom aggregations, filters, counts, or JOINs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "SQL SELECT statement to run (e.g. 'SELECT * FROM chemicals LIMIT 10').",
                    },
                },
                "required": ["sql_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_db_schema",
            "description": "Inspect column names and data types of a table, or list all table names. Use this before run_read_only_query if unsure of column names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Optional table name to inspect. Omit to list all table names.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_incidents",
            "description": "List recent HSE incidents and near-misses from MySQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "e.g. OPEN, CLOSED, INVESTIGATING"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_overdue_capas",
            "description": "List overdue CAPAs from MySQL (past due_date and not completed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_info",
            "description": "Look up employee details from MySQL by employee_id (e.g. EMP-001) or by name/job title search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "query": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Name or job title search term"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_kpis",
            "description": "Get monthly safety KPI metrics from MySQL (hours worked, TRIR, LTIFR, recordable incidents).",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "e.g. 2026-07"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 12},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_ai_events",
            "description": "List AI camera detection events from MySQL (PPE violations, restricted zone entry, fire).",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "LOW, MEDIUM, HIGH, CRITICAL"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_sensor_alerts",
            "description": "List IoT sensor readings and alert conditions from MySQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_chemicals",
            "description": "List chemicals from the MySQL inventory (trade name, CAS, GHS hazard class, quantity).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Chemical name or hazard class search term"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_permits",
            "description": "List work permits from MySQL (HOT_WORK, CONFINED_SPACE, WORKING_AT_HEIGHT, status, risk level).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "e.g. APPROVED, ACTIVE, EXPIRED, CLOSED"},
                    "risk_level": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "LOW, MEDIUM, HIGH"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_inspections",
            "description": "List safety inspections from MySQL (type, status, score percentage).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "COMPLETED, SCHEDULED, IN_PROGRESS"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_inventory",
            "description": "List PPE stock items from MySQL (masks, gloves, helmets, stock status).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_risk_register",
            "description": "List hazards and risk register entries from MySQL (hazard, activity, inherent score, residual score).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_training",
            "description": "List expired or soon-to-expire employee training certificates from MySQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_fire_equipment",
            "description": "List fire safety equipment (extinguishers, hydrants, detectors) and their inspection dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ppe_stock_status",
            "description": "Get detailed PPE inventory stock status, including items below threshold and days until stockout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "below_threshold_only": {"anyOf": [{"type": "boolean"}, {"type": "null"}], "default": False},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_expired_fire_equipment",
            "description": "List expired or maintenance-due fire extinguishers and equipment requiring urgent replacement/refill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_fire_inspections",
            "description": "List periodic inspection logs for fire equipment (passed, maintenance required, failed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "status": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "PASSED, FAILED, MAINTENANCE_REQUIRED"},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_fixed_safety_assets",
            "description": "List fixed safety assets (eyewash stations, emergency showers, AEDs, LOTO stations) by zone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "limit": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": 15},
                },
            },
        },
    },
]

# Streamlined tool definitions for local Ollama
LOCAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_read_only_query",
            "description": "Execute any SQL SELECT statement directly on MySQL (JOINs, aggregations, counts, any table).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {"type": "string", "description": "SQL SELECT query to execute"}
                },
                "required": ["sql_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_fire_equipment",
            "description": "List fire safety equipment (extinguishers, hydrants, detectors, suppression systems) and inspection dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expired_fire_equipment",
            "description": "List expired or inspection-due fire extinguishers and equipment requiring service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_fire_inspections",
            "description": "List fire equipment inspection records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "string", "description": "Filter by equipment ID (e.g. FE-0001)"},
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_ppe_inventory",
            "description": "List PPE inventory items (helmets, gloves, boots, vests) and stock balances.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category filter (optional)"},
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ppe_stock_status",
            "description": "List low stock PPE items below reorder threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "below_threshold_only": {"type": "boolean", "description": "Only show items below threshold"},
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_incidents",
            "description": "List HSE incidents and near-misses from MySQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Status filter (e.g. OPEN, CLOSED, INVESTIGATING)."},
                    "limit": {"type": "integer", "description": "Row limit (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_permits",
            "description": "List work permits (HOT_WORK, CONFINED_SPACE, HEIGHT, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "APPROVED, ACTIVE, EXPIRED, PENDING_APPROVAL"},
                    "risk_level": {"type": "string", "description": "LOW, MEDIUM, HIGH, CRITICAL"},
                    "limit": {"type": "integer", "description": "Row limit (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_overdue_capas",
            "description": "List overdue CAPA corrective actions from MySQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_info",
            "description": "Look up employee details by ID (e.g. EMP-001) or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string", "description": "e.g. EMP-001"},
                    "query": {"type": "string", "description": "Name search"},
                    "limit": {"type": "integer", "description": "Row limit (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_kpis",
            "description": "Get monthly safety KPIs (TRIR, LTIFR, hours worked, incidents).",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "e.g. 2026-07"},
                    "limit": {"type": "integer", "description": "Row limit (default 12)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_fixed_safety_assets",
            "description": "List fixed safety assets (eyewashes, showers, AEDs, LOTO stations).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone_id": {"type": "string", "description": "Zone filter (optional)"},
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_chemicals",
            "description": "List chemical inventory and GHS hazard classes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Chemical name search"},
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_training",
            "description": "List expired or expiring employee training certificates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Row limit (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_db_schema",
            "description": "Get table schema or list all table names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Table name (optional)"}
                }
            }
        }
    }
]
