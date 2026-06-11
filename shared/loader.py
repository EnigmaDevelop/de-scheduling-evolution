# shared/loader.py

import json
import logging
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Engine,
    text,
    Column,
    Integer,
    Float,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session

from shared.models import WeatherRecord

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Base + Table Definition
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class WeatherRecordORM(Base):
    """
    ORM model for weather_records table.
    Maps directly to WeatherRecord Pydantic model.
    """
    __tablename__ = "weather_records"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    city          = Column(String(100), nullable=False, index=True)
    timestamp     = Column(DateTime(timezone=True), nullable=False, index=True)
    temp          = Column(Float, nullable=False)
    feels_like    = Column(Float, nullable=False)
    temp_min      = Column(Float, nullable=False)
    temp_max      = Column(Float, nullable=False)
    pressure      = Column(Integer, nullable=False)
    humidity      = Column(Integer, nullable=False)
    wind_speed    = Column(Float, nullable=False)
    wind_deg      = Column(Integer, nullable=False)
    weather_main  = Column(String(50), nullable=False)
    weather_desc  = Column(String(100), nullable=False)
    raw           = Column(JSONB, nullable=False)    # full API response stored as JSONB

    def __repr__(self) -> str:
        return (
            f"<WeatherRecordORM "
            f"city={self.city} "
            f"temp={self.temp} "
            f"ts={self.timestamp}>"
        )


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------

def build_engine(
    host: str,
    port: int,
    db: str,
    user: str,
    password: str,
    pool_size: int = 5,
    echo: bool = False,
) -> Engine:
    """
    Creates SQLAlchemy engine.
    Called once per process, engine is reused across sessions.

    Args:
        echo : if True, SQLAlchemy logs all SQL statements (debug only)
    """
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(url, pool_size=pool_size, echo=echo)
    logger.info(f"Engine created | host={host} port={port} db={db}")
    return engine


# ---------------------------------------------------------------------------
# Table bootstrap
# ---------------------------------------------------------------------------

def init_db(engine: Engine) -> None:
    """
    Creates all tables if they don't exist.
    Safe to call on every startup — no-op if tables already exist.
    Not a replacement for Alembic migrations in production.
    """
    Base.metadata.create_all(engine)
    logger.info("Database tables initialized")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def load(record: WeatherRecord, engine: Engine) -> int:
    """
    Inserts a single WeatherRecord into PostgreSQL.

    Args:
        record  : Transformed WeatherRecord from extractor
        engine  : SQLAlchemy engine

    Returns:
        id of the inserted row

    Raises:
        SQLAlchemyError : on any DB error
    """
    orm_obj = WeatherRecordORM(
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
        raw=record.raw,
    )

    with Session(engine) as session:
        session.add(orm_obj)
        session.commit()
        session.refresh(orm_obj)
        inserted_id = orm_obj.id

    logger.info(
        f"Record loaded | id={inserted_id} "
        f"city={record.city} "
        f"ts={record.timestamp}"
    )

    return inserted_id
