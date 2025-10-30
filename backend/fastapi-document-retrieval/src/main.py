from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import documents, search, vectors

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(vectors.router, prefix="/vectors", tags=["vectors"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Document Retrieval API"}