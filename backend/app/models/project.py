from sqlalchemy import Column, Integer, String, Numeric, Date, Text, DateTime, func
from app.models import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    customer = Column(String, nullable=False)
    project_manager = Column(String)
    status = Column(String, nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(Text)
    # Retained from the original schema so existing data and the
    # /projects response stay backward-compatible.
    budget = Column(Numeric)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
