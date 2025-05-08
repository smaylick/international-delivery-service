from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from src.db.base import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    session = Column(String(32), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    weight = Column(Float, nullable=False)
    content_cost_usd = Column(Float, nullable=False)
    delivery_cost_rub = Column(Float, nullable=True)

    type_id = Column(Integer, ForeignKey("package_types.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    package_type = relationship("PackageType", lazy="selectin")
