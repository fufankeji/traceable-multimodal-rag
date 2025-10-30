# FastAPI Document Retrieval

This project is a FastAPI application designed for document storage, retrieval, and dense vector recall using SQL and Milvus. It provides a RESTful API for managing documents and their associated vectors, allowing users to upload, search, and delete documents efficiently.

## Features

- **Document Management**: Upload, search, and delete documents with associated metadata.
- **Dense Vector Operations**: Upload and query dense vectors for advanced search capabilities.
- **SQL Database Integration**: Store document metadata and information in a SQL database.
- **Milvus Integration**: Utilize Milvus for efficient vector storage and retrieval.

## Project Structure

```
fastapi-document-retrieval
├── src
│   ├── main.py                # Entry point for the FastAPI application
│   ├── api                    # API routes and dependencies
│   │   ├── routes             # Route definitions
│   │   │   ├── documents.py    # Document upload and management routes
│   │   │   ├── search.py       # Document search routes
│   │   │   └── vectors.py      # Dense vector operations routes
│   │   └── dependencies.py      # Dependency injection for database and Milvus
│   ├── core                   # Core application logic
│   │   ├── config.py           # Configuration settings
│   │   ├── database.py         # SQL database operations
│   │   └── milvus_client.py    # Milvus client operations
│   ├── models                 # Data models and schemas
│   │   ├── database            # Database models
│   │   │   ├── document.py      # Document model
│   │   │   ├── chunk.py        # Chunk model
│   │   │   └── metadata.py     # Metadata model
│   │   ├── schemas             # Pydantic schemas for validation
│   │   │   ├── document.py      # Document schema
│   │   │   ├── search.py        # Search schema
│   │   │   └── response.py      # Response schema
│   │   └── milvus              # Milvus collection models
│   │       ├── collection.py    # Milvus collection model
│   ├── services                # Business logic services
│   │   ├── document_service.py  # Document service
│   │   ├── vector_service.py    # Vector service
│   │   └── search_service.py     # Search service
│   └── utils                  # Utility functions
│       ├── vector_utils.py      # Vector utility functions
│       └── text_processing.py    # Text processing functions
├── migrations                  # Database migration files
│   └── versions
├── tests                       # Unit tests
│   ├── test_documents.py        # Document tests
│   ├── test_search.py           # Search tests
│   └── test_vectors.py          # Vector tests
├── requirements.txt            # Project dependencies
├── alembic.ini                # Alembic configuration for migrations
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Dockerfile for building the application
└── README.md                  # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd fastapi-document-retrieval
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database and Milvus according to the configuration in `src/core/config.py`.

## Usage

To run the FastAPI application, execute the following command:

```
uvicorn src.main:app --reload
```

You can access the API documentation at `http://127.0.0.1:8000/docs`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.