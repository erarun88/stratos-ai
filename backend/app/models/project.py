from sqlalchemy import Column, Integer, String, Numeric
from app.models import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    customer = Column(String)
    status = Column(String)
    budget = Column(Numeric)
