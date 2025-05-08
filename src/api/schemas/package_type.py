from pydantic import BaseModel


class PackageTypeCreate(BaseModel):
    name: str


class PackageTypeRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
