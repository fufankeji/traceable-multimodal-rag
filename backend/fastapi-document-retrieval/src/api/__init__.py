# src/api/__init__.py

from fastapi import APIRouter

router = APIRouter()

from .routes import documents, search, vectors

router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(vectors.router, prefix="/vectors", tags=["vectors"])