from datetime import date

from sqlalchemy.orm import Session
from app.database import engine
from app.models import Base
from app.models.project import Project
from app.models.engineer import Engineer
from app.models.document import Document

# Create all tables
Base.metadata.create_all(engine)

session = Session(engine)

# Clear existing data. Documents go first: they reference projects, so the
# project rows cannot be removed while document rows still point at them.
# Note this clears metadata only — stored files are removed by
# `python -m app.purge_documents`.
session.query(Document).delete()
session.query(Engineer).delete()
session.query(Project).delete()
session.commit()

# Add 3 projects
projects = [
    Project(
        id=1,
        name="CloudSync Platform",
        customer="TechCorp Inc.",
        project_manager="Sarah Mitchell",
        status="active",
        start_date=date(2026, 1, 15),
        end_date=date(2026, 12, 15),
        description="Enterprise file synchronization and collaboration platform.",
        budget=500000,
    ),
    Project(
        id=2,
        name="DataVault Analytics",
        customer="FinanceFlow Ltd.",
        project_manager="Daniel Okafor",
        status="active",
        start_date=date(2026, 3, 1),
        end_date=date(2027, 2, 28),
        description="Real-time financial analytics and reporting suite.",
        budget=750000,
    ),
    Project(
        id=3,
        name="SecureNet Infrastructure",
        customer="GlobalSecurity Corp.",
        project_manager="Priya Nair",
        status="planning",
        start_date=date(2026, 6, 1),
        end_date=None,
        description="Zero-trust network infrastructure rollout.",
        budget=1200000,
    ),
]

session.add_all(projects)
session.commit()

# Add 20 engineers distributed across 3 projects
engineers = [
    # Project 1: CloudSync Platform (7 engineers)
    Engineer(name="Alice Johnson", email="alice.johnson@stratos.ai", role="Senior Engineer", status="active", project_id=1),
    Engineer(name="Bob Chen", email="bob.chen@stratos.ai", role="Backend Engineer", status="active", project_id=1),
    Engineer(name="Carol Martinez", email="carol.martinez@stratos.ai", role="Frontend Engineer", status="active", project_id=1),
    Engineer(name="David Thompson", email="david.thompson@stratos.ai", role="DevOps Engineer", status="active", project_id=1),
    Engineer(name="Emma Wilson", email="emma.wilson@stratos.ai", role="QA Engineer", status="active", project_id=1),
    Engineer(name="Frank Rodriguez", email="frank.rodriguez@stratos.ai", role="Backend Engineer", status="on_leave", project_id=1),
    Engineer(name="Grace Lee", email="grace.lee@stratos.ai", role="Tech Lead", status="active", project_id=1),

    # Project 2: DataVault Analytics (7 engineers)
    Engineer(name="Henry Kim", email="henry.kim@stratos.ai", role="Data Engineer", status="active", project_id=2),
    Engineer(name="Isabella Garcia", email="isabella.garcia@stratos.ai", role="Senior Engineer", status="active", project_id=2),
    Engineer(name="James Anderson", email="james.anderson@stratos.ai", role="Full Stack Engineer", status="active", project_id=2),
    Engineer(name="Kelly White", email="kelly.white@stratos.ai", role="Machine Learning Engineer", status="active", project_id=2),
    Engineer(name="Leo Patel", email="leo.patel@stratos.ai", role="Backend Engineer", status="active", project_id=2),
    Engineer(name="Maya Sharma", email="maya.sharma@stratos.ai", role="QA Engineer", status="active", project_id=2),
    Engineer(name="Nathan Brown", email="nathan.brown@stratos.ai", role="Cloud Architect", status="inactive", project_id=2),

    # Project 3: SecureNet Infrastructure (6 engineers)
    Engineer(name="Olivia Taylor", email="olivia.taylor@stratos.ai", role="Security Engineer", status="active", project_id=3),
    Engineer(name="Patrick Jones", email="patrick.jones@stratos.ai", role="Senior Engineer", status="active", project_id=3),
    Engineer(name="Quinn Davis", email="quinn.davis@stratos.ai", role="DevOps Engineer", status="active", project_id=3),
    Engineer(name="Rachel Green", email="rachel.green@stratos.ai", role="Infrastructure Engineer", status="active", project_id=3),
    Engineer(name="Samuel Miller", email="samuel.miller@stratos.ai", role="Backend Engineer", status="active", project_id=3),
    Engineer(name="Tina Lopez", email="tina.lopez@stratos.ai", role="Security Architect", status="on_leave", project_id=3),
]

session.add_all(engineers)
session.commit()

print("✓ Added 3 projects")
print("✓ Added 20 engineers")
print("✓ Database seeded successfully!")

session.close()
