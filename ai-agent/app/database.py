from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

database_url_value = settings.database_url or settings.mysql_url
if not database_url_value and settings.mysql_host and settings.mysql_user:
    database_name = settings.mysql_database or settings.database_name
    database_url_value = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{database_name}"
    )

if not database_url_value:
    raise RuntimeError(
        "DATABASE_URL or Railway MYSQLHOST/MYSQLUSER configuration must be set."
    )

parsed_url = make_url(database_url_value)
db_name = parsed_url.database or settings.database_name or "railway"
database_url = parsed_url.set(database=db_name)

engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Automatically reconnect stale MySQL connections
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
