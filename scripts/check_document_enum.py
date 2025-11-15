"""
Utility script to inspect Postgres documenttype enum and alembic version.
"""
from sqlalchemy import create_engine, text

from app.core.config import settings


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version();")).scalar()
        print("DB version:", version)

        enums = conn.execute(
            text(
                """
                SELECT enumlabel
                FROM pg_enum
                JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
                WHERE pg_type.typname = 'documenttype'
                ORDER BY enumlabel;
                """
            )
        ).fetchall()
        print("documenttype enums:", [row[0] for row in enums])

        alembic_versions = conn.execute(
            text("SELECT version_num FROM alembic_version;")
        ).fetchall()
        print("alembic_version rows:", [row[0] for row in alembic_versions])


if __name__ == "__main__":
    main()

