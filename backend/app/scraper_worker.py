from __future__ import annotations

import argparse
import json
import os
import signal
import sys
from datetime import datetime, timezone
from threading import Event


LEASE_KEY = "covercheck-continuous-scraper"


def _database_url() -> str:
    value = os.environ.get("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL is required for the continuous scraper")
    return value


def _ensure_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS source_registry (
                source_id TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                approval_state TEXT NOT NULL CHECK (
                    approval_state IN ('approved', 'unverified', 'restricted', 'rejected')
                ),
                owner_name TEXT,
                review_date DATE,
                next_scrape_due TIMESTAMPTZ,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                last_success_at TIMESTAMPTZ,
                last_failure_at TIMESTAMPTZ
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraper_runtime (
                worker_name TEXT PRIMARY KEY,
                state TEXT NOT NULL CHECK (
                    state IN ('running', 'degraded', 'stale', 'failed', 'stopped')
                ),
                lease_owner TEXT,
                last_heartbeat TIMESTAMPTZ NOT NULL,
                details JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
    connection.commit()


def _status(connection, state: str, details: dict[str, object] | None = None) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO scraper_runtime (worker_name, state, lease_owner, last_heartbeat, details)
            VALUES ('continuous-scraper', %s, pg_backend_pid()::text, now(), %s::jsonb)
            ON CONFLICT (worker_name) DO UPDATE SET
                state = EXCLUDED.state,
                lease_owner = EXCLUDED.lease_owner,
                last_heartbeat = EXCLUDED.last_heartbeat,
                details = EXCLUDED.details
            """,
            (state, json.dumps(details or {})),
        )
    connection.commit()


def _lease_acquired(connection) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(hashtext(%s))", (LEASE_KEY,))
        return bool(cursor.fetchone()[0])


def check_lock() -> int:
    import psycopg

    with psycopg.connect(_database_url()) as connection:
        _ensure_schema(connection)
        acquired = _lease_acquired(connection)
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(hashtext(%s))", (LEASE_KEY,))
        return 0 if acquired else 1


def run() -> int:
    import psycopg

    interval = max(5, int(os.environ.get("SCRAPE_INTERVAL_SECONDS", "86400")))
    heartbeat_seconds = min(30, interval)
    stop = Event()

    def stop_worker(signum, frame) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    with psycopg.connect(_database_url()) as connection:
        _ensure_schema(connection)
        if not _lease_acquired(connection):
            print(json.dumps({"event": "lease_rejected", "worker": LEASE_KEY}))
            return 2
        print(json.dumps({"event": "lease_acquired", "worker": LEASE_KEY}))
        while not stop.is_set():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT source_id, source_url
                    FROM source_registry
                    WHERE approval_state = 'approved'
                      AND (next_scrape_due IS NULL OR next_scrape_due <= now())
                    ORDER BY next_scrape_due NULLS FIRST, source_id
                    LIMIT 1
                    """
                )
                due_source = cursor.fetchone()
            if due_source is None:
                _status(
                    connection,
                    "running",
                    {
                        "freshness": "unknown",
                        "message": "No approved source is due; worker is waiting.",
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                _status(
                    connection,
                    "degraded",
                    {
                        "source_id": due_source[0],
                        "message": "Approved-source fetch is not enabled in the POC worker.",
                    },
                )
            stop.wait(heartbeat_seconds)
        _status(connection, "stopped", {"reason": "termination_signal"})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CoverCheck singleton scraper worker")
    parser.add_argument("--check-lock", action="store_true")
    arguments = parser.parse_args()
    return check_lock() if arguments.check_lock else run()


if __name__ == "__main__":
    sys.exit(main())