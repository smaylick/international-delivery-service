from fastapi import (
    APIRouter,
    Request,
    status,
    Depends,
    Query,
    HTTPException,
)
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.schemas.package import PackageCreate, PackageRead
from src.db.deps import get_async_session
from src.models.package import Package
from src.models.package_type import PackageType

router = APIRouter(
    prefix="/packages",
    tags=["Packages"],
    redirect_slashes=False,
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_package(
    request: Request,
    data: PackageCreate,
    db: AsyncSession = Depends(get_async_session),
):
    exists = await db.execute(
        select(PackageType.id).where(PackageType.id == data.type_id)
    )
    if not exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PackageType {data.type_id} does not exist",
        )

    pkg = Package(session=request.state.session_id, **data.model_dump())
    db.add(pkg)
    await db.commit()
    await db.refresh(pkg)

    out = PackageRead.model_validate(pkg).model_dump()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder({"success": True, "data": out}),
    )


@router.get("", status_code=status.HTTP_200_OK)
async def get_packages(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    type_id: int | None = None,
    db: AsyncSession = Depends(get_async_session),
):
    offset = (page - 1) * page_size

    q = select(Package).where(Package.session == request.state.session_id)
    if type_id:
        q = q.where(Package.type_id == type_id)
    q = q.offset(offset).limit(page_size)

    rows = (await db.execute(q)).scalars().all()
    items = [PackageRead.model_validate(p).model_dump() for p in rows]
    return jsonable_encoder({"success": True, "data": items})


@router.get("/{package_id}", status_code=status.HTTP_200_OK)
async def get_package(
    request: Request,
    package_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    q = select(Package).where(
        Package.id == package_id,
        Package.session == request.state.session_id,
    )
    pkg = (await db.execute(q)).scalar_one_or_none()
    if not pkg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Package not found")

    if pkg.delivery_cost_rub is None:
        return jsonable_encoder({"success": True, "data": {"message": "Не рассчитано"}})

    out = PackageRead.model_validate(pkg).model_dump()
    return jsonable_encoder({"success": True, "data": out})
