#!/usr/bin/env python3
import sys
import os
import argparse
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.db import Database
from src.pipeline import WatchdogPipeline

def main():
    parser = argparse.ArgumentParser(description="Zeleneč Board Watchdog")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.yaml"), help="Path to config.yaml")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "data" / "watchdog.db"), help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Do not send real notifications, just log and mark seen")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger("watchdog")
    logger.info(f"Loading config from {args.config}")
    cfg = load_config(args.config)

    # Ensure data directory exists
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    db = Database(args.db)
    db.init_schema()

    pipeline = WatchdogPipeline(config=cfg, db=db, dry_run=args.dry_run)
    pipeline.run_cycle()

if __name__ == "__main__":
    main()
