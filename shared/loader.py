# shared/loader.py
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from shared.models import WeatherRecord

DB_USER = os.getenv("POSTGRES_USER", "de_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "de_password")
DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "de_scheduling")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WeatherRecordORM(Base):
    """SQLAlchemy ORM model representing the destination weather table."""
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    temp = Column(Float, nullable=False)
    feels_like = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    pressure = Column(Integer, nullable=False)
    humidity = Column(Integer, nullable=False)
    wind_speed = Column(Float, nullable=False)
    wind_deg = Column(Integer, nullable=False)
    weather_main = Column(String(50), nullable=False)
    weather_desc = Column(String(255), nullable=False)
    raw = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # STRICT DIRECTIVE: Enforces the architectural unique constraint on PostgreSQL layer
    __table_args__ = (
        UniqueConstraint('city', 'timestamp', name='unique_city_timestamp'),
    )

def run_alembic_programmatic():
    """Triggers Alembic migrations programmatically on application startup."""
    import os
    import structlog
    from alembic.config import Config
    from alembic import command
    
    logger = structlog.get_logger()
    logger.info("Executing database migrations via Alembic")
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ini_path = os.path.join(current_dir, "alembic", "alembic.ini")
        
        alembic_cfg = Config(ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(current_dir, "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations completed successfully")
    except Exception as e:
        logger.error("Alembic migration failed", error=str(e))
        raise

def upsert_weather(record: WeatherRecord):
    """Inserts a WeatherRecord or updates it on conflict (Idempotency implementation)."""
    from sqlalchemy.dialects.postgresql import insert
    
    session = SessionLocal()
    try:
        stmt = insert(WeatherRecordORM).values(
            city=record.city,
            timestamp=record.timestamp,
            temp=record.temp,
            feels_like=record.feels_like,
            temp_min=record.temp_min,
            temp_max=record.temp_max,
            pressure=record.pressure,
            humidity=record.humidity,
            wind_speed=record.wind_speed,
            wind_deg=record.wind_deg,
            weather_main=record.weather_main,
            weather_desc=record.weather_desc,
            raw=record.raw
        )
        
        # Safe binding to the exact structural unique constraint name
        upsert_stmt = stmt.on_conflict_do_update(
            constraint='unique_city_timestamp',
            set_={
                'temp': stmt.excluded.temp,
                'feels_like': stmt.excluded.feels_like,
                'temp_min': stmt.excluded.temp_min,
                'temp_max': stmt.excluded.temp_max,
                'pressure': stmt.excluded.pressure,
                'humidity': stmt.excluded.humidity,
                'wind_speed': stmt.excluded.wind_speed,
                'wind_deg': stmt.excluded.wind_deg,
                'weather_main': stmt.excluded.weather_main,
                'weather_desc': stmt.excluded.weather_desc,
                'raw': stmt.excluded.raw
            }
        )
        
        session.execute(upsert_stmt)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
