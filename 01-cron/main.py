import sys
import os
from datetime import datetime, timezone
import structlog

# Force validation of root path for shared modules resolution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from shared.extractor import extract
from shared.loader import run_alembic_programmatic, upsert_weather

logger = structlog.get_logger()

def main():
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("Cron data pipeline task initiated", execution_timestamp=timestamp)
    
    try:
        # Step 1: Enforce schema safety on startup via programmatic migrations
        run_alembic_programmatic()
        
        # Step 2: Resolve runtime configuration from environment variables
        city = os.getenv("TARGET_CITY", "Istanbul")
        api_key = os.getenv("OPENWEATHER_API_KEY", "MOCK_MODE")
        
        # Step 3: Execute resilient extraction layer
        weather_record = extract(api_key=api_key, city=city)
        logger.info("Ingestion telemetry captured successfully", city=city, calculated_temp=weather_record.temp)
        
        # Step 4: Execute idempotent load layer
        upsert_weather(weather_record)
        logger.info("Cron pipeline cycle finalized successfully")
        
    except Exception as e:
        # Catch-all block implemented to ensure system survivability per specification
        logger.error("Non-fatal exception caught during cron pipeline cycle", error=str(e))
        # Exit cleanly with status 0 to prevent container crash, leaving scheduling system alive for next period
        sys.exit(0)

if __name__ == "__main__":
    main()
