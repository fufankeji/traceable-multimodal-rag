from fastapi import APIRouter
from api.v1.endpoints import knowledge_base, files, chunks, search

router = APIRouter()

router.include_router(knowledge_base.router, prefix="/knowledge_base", tags=["knowledge_base"])
router.include_router(files.router, prefix="/files", tags=["files"])
router.include_router(chunks.router, prefix="/chunks", tags=["chunks"])
router.include_router(search.router, prefix="/search", tags=["search"])