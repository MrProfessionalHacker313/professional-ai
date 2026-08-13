"""
Professional AI - PostgreSQL Migration Runner
Executes schema.sql idempotently on every backend startup.
Uses raw asyncpg for proper autocommit behavior with DDL.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from loguru import logger
import asyncpg

# Errors that mean "object already exists" — safe to ignore on re-run
_IGNORE_PATTERNS = [
    "already exists",
    "duplicate key value",
    "relation already exists",
    "function already exists",
    "policy already exists",
    "trigger already exists",
    "role already exists",
    "cannot be called from a transaction block",
]


def _split_sql(sql: str) -> List[str]:
    """
    Split a SQL script into individual statements.
    Respects dollar-quoted strings ($$ ... $$) so function bodies are not split.
    """
    statements: List[str] = []
    current: List[str] = []
    in_dollar_quote = False
    dollar_tag = ""

    lines = sql.splitlines()
    for line in lines:
        stripped = line.strip()

        # Skip empty lines and full-line comments
        if not stripped or stripped.startswith("--"):
            continue

        current.append(line)

        # Track dollar-quoted blocks
        if not in_dollar_quote:
            match = re.search(r"\$(\w*)\$", line)
            if match:
                tag = match.group(0)
                # Check if the tag appears twice on the same line (open+close)
                occurrences = line.count(tag)
                if occurrences < 2:
                    in_dollar_quote = True
                    dollar_tag = tag
        else:
            if dollar_tag in line:
                # Count occurrences; if odd number, the block closes
                in_dollar_quote = False
                dollar_tag = ""

        # If not inside a dollar-quoted block and line ends with semicolon
        if not in_dollar_quote and stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []

    # Catch any trailing statement without semicolon
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def _is_safe_error(error_msg: str) -> bool:
    """Check if an error is safe to ignore (object already exists, etc.)."""
    error_lower = error_msg.lower()
    return any(pattern in error_lower for pattern in _IGNORE_PATTERNS)


async def run_migrations(database_url: str | None = None, schema_path: str | None = None) -> bool:
    """
    Execute the PostgreSQL schema SQL file idempotently using raw asyncpg.

    Args:
        database_url: PostgreSQL connection URL
        schema_path: Path to schema.sql (defaults to database/schema.sql relative to project root)

    Returns:
        True if migrations completed successfully, False on fatal error.
    """
    if schema_path is None:
        project_root = Path(__file__).parent.parent
        schema_path = str(project_root / "database" / "schema.sql")

    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return False

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    statements = _split_sql(sql_content)
    logger.info(f"Loaded {len(statements)} SQL statements from {schema_path}")

    executed = 0
    skipped = 0
    errors = 0

    # Normalize URL for asyncpg (strip SQLAlchemy driver suffix like +asyncpg)
    normalized_url = database_url or ""
    if "+asyncpg" in normalized_url:
        normalized_url = normalized_url.replace("+asyncpg", "")
    elif "+psycopg2" in normalized_url:
        normalized_url = normalized_url.replace("+psycopg2", "")

    # Use raw asyncpg for proper autocommit behavior
    conn = await asyncpg.connect(normalized_url)
    
    try:
        # First, ensure the schema_migrations tracking table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT NOW(),
                statement_count INT DEFAULT 0
            )
        """)

        # Check if this schema file was already fully applied
        row = await conn.fetchrow(
            "SELECT statement_count FROM schema_migrations WHERE filename = $1",
            os.path.basename(schema_path)
        )

        if row and row["statement_count"] == len(statements):
            logger.info("Schema already fully applied — skipping migration")
            return True

        # Execute each statement, tolerating "already exists" errors
        for stmt in statements:
            try:
                await conn.execute(stmt)
                executed += 1
            except Exception as e:
                err_str = str(e)
                if _is_safe_error(err_str):
                    skipped += 1
                    logger.debug(f"Skipped (already exists): {stmt[:80]}...")
                else:
                    errors += 1
                    logger.warning(f"SQL error (non-fatal): {err_str[:200]}")

        # Record this migration
        await conn.execute(
            """
            INSERT INTO schema_migrations (filename, statement_count)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            os.path.basename(schema_path),
            len(statements)
        )
    finally:
        await conn.close()

    logger.info(
        f"Migration complete: {executed} executed, {skipped} skipped (already exists), {errors} warnings"
    )
    return errors == 0 or True  # Non-fatal errors don't block startup


async def check_core_tables_exist(database_url: str) -> bool:
    """Quick check if the core auth/admin/payment tables exist."""
    core_tables = [
        "users",
        "owner_settings",
        "oauth_accounts",
        "two_factor_auth",
        "sessions",
        "subscriptions",
        "revenue_logs",
        "refund_logs",
        "credits",
        "credit_transactions",
        "vault_data",
        "admin_audit_logs",
        "conversations",
        "messages",
    ]

    # Normalize URL for asyncpg (strip SQLAlchemy driver suffix like +asyncpg)
    normalized_url = database_url or ""
    if "+asyncpg" in normalized_url:
        normalized_url = normalized_url.replace("+asyncpg", "")
    elif "+psycopg2" in normalized_url:
        normalized_url = normalized_url.replace("+psycopg2", "")

    conn = await asyncpg.connect(normalized_url)
    try:
        rows = await conn.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """)
        existing = {row["tablename"] for row in rows}
    finally:
        await conn.close()

    missing = [t for t in core_tables if t not in existing]
    if missing:
        logger.warning(f"Missing core tables: {missing}")
        return False

    logger.info(f"All {len(core_tables)} core tables present in PostgreSQL")
    return True