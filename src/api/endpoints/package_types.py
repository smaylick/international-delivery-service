from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from src.db.deps import get_async_session
from src.models.package_type import PackageType
from src.api.schemas.package_type import PackageTypeCreate, PackageTypeRead

router = APIRouter(
    prefix="/package-types",
    tags=["Package Types"],
    redirect_slashes=False,
)


@router.post("", status_code=status.HTTP_200_OK)
async def create_package_type(
    payload: PackageTypeCreate,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        pt = PackageType(name=payload.name)
        db.add(pt)
        await db.commit()
        await db.refresh(pt)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PackageType '{payload.name}' already exists",
        ) from exc

    out = PackageTypeRead.model_validate(pt).model_dump()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder({"success": True, "data": out}),
    )


@router.get("", status_code=status.HTTP_200_OK)
async def get_package_types(
    db: AsyncSession = Depends(get_async_session),
):
    rows = (await db.execute(select(PackageType))).scalars().all()
    items = [PackageTypeRead.model_validate(r).model_dump() for r in rows]
    return jsonable_encoder({"success": True, "data": items})
