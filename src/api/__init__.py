from fastapi import APIRouter
from .endpoints.packages import router as packages_router
from .endpoints.package_types import router as package_types_router

api_router = APIRouter()
api_router.include_router(packages_router)
api_router.include_router(package_types_router)
