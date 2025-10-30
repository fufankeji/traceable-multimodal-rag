from fastapi import APIRouter

router = APIRouter()

from .documents import router as documents_router
from .search import router as search_router
from .vectors import router as vectors_router

router.include_router(documents_router, prefix="/documents", tags=["documents"])
router.include_router(search_router, prefix="/search", tags=["search"])
router.include_router(vectors_router, prefix="/vectors", tags=["vectors"])