from pydantic import BaseModel, Field, PositiveFloat, PositiveInt
from datetime import datetime


class PackageCreate(BaseModel):
    name: str = Field(..., max_length=100)
    weight: PositiveFloat = Field(..., gt=0, description="Вес в кг (>0)")
    content_cost_usd: PositiveFloat = Field(..., gt=0, description="Стоимость (>0 USD)")
    type_id: PositiveInt = Field(..., description="ID из package_types")


class PackageRead(PackageCreate):
    id: int
    delivery_cost_rub: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True
