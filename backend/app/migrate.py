"""Idempotent schema migration for the projects table.

The initial projects table only had (id, name, customer, status, budget).
The Project Management module adds several columns. Because the project has
no migration framework (e.g. Alembic) yet and SQLAlchemy's create_all() does
not ALTER existing tables, this script applies the additive changes directly.

Safe to run multiple times — every statement uses IF NOT EXISTS or is a no-op
when already applied.

Usage (from the backend/ directory, with the virtualenv active):
    python -m app.migrate
"""

from sqlalchemy import text

from app.database import engine

STATEMENTS = [
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_manager VARCHAR",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS start_date DATE",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS end_date DATE",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()",
    # budget is now an optional legacy field (the Project Management module
    # does not collect it), so it must allow NULL for newly created projects.
    "ALTER TABLE projects ALTER COLUMN budget DROP NOT NULL",
    # Backfill timestamps for any rows that predate the new columns.
    "UPDATE projects SET created_at = now() WHERE created_at IS NULL",
    "UPDATE projects SET updated_at = now() WHERE updated_at IS NULL",
    # Normalize legacy status values to the new project status vocabulary
    # (planning, active, on_hold, completed, cancelled).
    "UPDATE projects SET status = 'active' WHERE status = 'in_progress'",
]


def run() -> None:
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))
    print("✓ Projects table migration applied successfully.")


if __name__ == "__main__":
    run()
