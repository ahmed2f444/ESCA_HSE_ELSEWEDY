import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    sql = text("""
        UPDATE permits
        SET work_description = 'نقل وتفريغ الشحنات والمواد الثقيلة داخل المصنع (Inside the factory carrying shipments)',
            permit_type_id = 4,
            status_id = 3,
            start_at = NOW(),
            expiry_at = DATE_ADD(NOW(), INTERVAL 8 HOUR),
            hours_to_expiry = 8.0,
            executor_name = 'فريق الصيانة الداخلي (Internal Maintenance)'
        WHERE permit_id = 11
    """)
    db.execute(sql)
    db.commit()
    print("SUCCESS: Updated permit_id = 11 in MySQL database.")
    
    r11 = db.execute(text("SELECT permit_id, permit_type_id, work_description, status_id, executor_name, start_at, expiry_at FROM permits WHERE permit_id=11")).mappings().all()
    print("PTW-011 Current Data:")
    for row in r11:
        print(dict(row))
finally:
    db.close()
