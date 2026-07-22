from sqlalchemy import Column, Integer, String, ForeignKey
from app.models import Base


class Engineer(Base):
    __tablename__ = "engineers"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String)
    status = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"))
