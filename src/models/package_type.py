from sqlalchemy import Column, Integer, String
from src.db.base import Base


class PackageType(Base):
    __tablename__ = "package_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
