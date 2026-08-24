import os
import re
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:admin12345678@127.0.0.1:3306/esca_hse"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "seed_excel")

# Skip meta/documentation sheets that are not domain data tables
EXCLUDE_SHEETS = {
    'README', 'Summary', 'Package_Index', 'Data_Dictionary', 
    'Status_Values', 'Relationships'
}

# Explicit table name overrides for clean database naming
TABLE_NAME_OVERPRIDES = {
    "CAPA": "capas",
    "Audit_Log": "audit_logs",
    "IoT_Sensors": "iot_sensors",
    "PPE_Stock": "ppe_inventory",
    "PPE": "ppe_inventory",
}

def clean_column_name(col: str) -> str:
    """Converts Excel headers to standard database snake_case."""
    s = str(col).strip()
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'[^a-zA-Z0-9]+', '_', s).lower().strip('_')
    
    mapping = {
        "id": "incident_id",
        "incident_no": "incident_id",
        "incident_number": "incident_id",
    }
    return mapping.get(s, s)

def detect_header_row_index(xls, sheet_name):
    """Scans the top rows to skip title banners and find the true header row."""
    raw_df = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=15)
    for idx, row in raw_df.iterrows():
        non_null = [str(val).strip() for val in row.dropna() if str(val).strip()]
        if len(non_null) < 2:
            continue

        if len({v.lower() for v in non_null}) == 1:
            continue

        row_values = [v.lower() for v in non_null]
        combined_row_text = " ".join(row_values)

        banner_markers = (
            "esca hse", "register", "owner:", "synthetic", "snapshot",
            "summary", "readme", "sample data", "workbook",
        )
        if any(marker in combined_row_text for marker in banner_markers):
            continue

        header_like = sum(
            1 for v in row_values
            if re.match(r"^[a-z][a-z0-9_]*$", v.replace(" ", "_")) and len(v) <= 40
        )
        if header_like >= 2:
            return idx

    return 0

def load_sheet_data(xls, sheet_name):
    header_idx = detect_header_row_index(xls, sheet_name)
    df = pd.read_excel(xls, sheet_name=sheet_name, header=header_idx)
    df.columns = [clean_column_name(c) for c in df.columns]
    df = df.dropna(how="all").dropna(how="all", axis=1)
    return df

def seed_database():
    print("Connecting to MySQL database...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    excel_files = [
        "ESCA_HSE_01_Master_Data_and_Dictionary.xlsx",
        "ESCA_HSE_02_Core_Operations_Sample_Data.xlsx",
        "ESCA_HSE_03_Assets_Training_Health_Sample_Data.xlsx",
        "ESCA_HSE_04_AI_IoT_Integrations_Audit_Sample_Data.xlsx"
    ]

    sheets_to_load = []
    for fname in excel_files:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            print(f"WARNING: File missing: {fname}")
            continue
        xls = pd.ExcelFile(fpath)
        for sname in xls.sheet_names:
            if sname in EXCLUDE_SHEETS:
                continue
            tbl_name = TABLE_NAME_OVERPRIDES.get(sname, clean_column_name(sname))
            sheets_to_load.append((fpath, sname, tbl_name))

    print(f"Found {len(sheets_to_load)} domain tables to seed.")

    print("Wiping old tables to ensure fresh schema sync...")
    with engine.begin() as conn:
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0;")
        for _, _, tbl_name in sheets_to_load:
            conn.exec_driver_sql(f"DROP TABLE IF EXISTS `{tbl_name}`;")
        conn.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1;")

    print("Seeding data into MySQL tables...\n")
    loaded_count = 0
    for fpath, sname, tbl_name in sheets_to_load:
        try:
            xls = pd.ExcelFile(fpath)
            df = load_sheet_data(xls, sname)
            if not df.empty:
                df.to_sql(tbl_name, con=engine, if_exists="replace", index=False)
                loaded_count += 1
                print(f"  [OK] Table '{tbl_name}' [{len(df)} rows] (Sheet: {sname})")
        except Exception as e:
            print(f"  [ERROR] Seeding '{tbl_name}' from '{sname}': {e}")

    print(f"\n[OK] Database re-seeded successfully with {loaded_count} domain tables!")

if __name__ == "__main__":
    seed_database()