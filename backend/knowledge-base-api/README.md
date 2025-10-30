# Knowledge Base API

This project is a FastAPI application designed for storing, retrieving, deleting, and recalling dense vectors using SQL and Milvus as data storage solutions. It provides a structured API for managing knowledge bases, files, and chunk information.

## Project Structure

- **src/**: Contains the main application code.
  - **main.py**: Entry point of the application, initializes the FastAPI instance and sets up routes.
  - **api/**: Contains the API modules.
    - **v1/**: Version 1 of the API.
      - **endpoints/**: Contains individual endpoint definitions for knowledge base, files, chunks, and search functionalities.
  - **core/**: Core functionalities including configuration, database setup, and security.
  - **crud/**: CRUD operations for knowledge bases, files, and chunks.
  - **db/**: Database-related modules for SQL and Milvus.
  - **schemas/**: Pydantic schemas for data validation and serialization.
  - **services/**: Business logic for handling knowledge bases, files, chunks, and vector operations.
  - **utils/**: Utility functions for file handling, embedding, and logging.

- **tests/**: Contains unit tests for the API and services.
- **migrations/**: Database migration files managed by Alembic.
- **requirements.txt**: Lists the required Python dependencies.
- **pyproject.toml**: Project metadata and dependency configuration.
- **docker-compose.yml**: Configuration for Docker services.
- **Dockerfile**: Instructions for building the Docker image.
- **.env.example**: Example environment variables.
- **.gitignore**: Files to be ignored by version control.
- **README.md**: Documentation and usage instructions for the project.

## Features

- Upload and manage files.
- Store and retrieve knowledge base entries.
- Handle chunk information for large documents.
- Perform dense vector recall using Milvus.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd knowledge-base-api
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the environment variables in a `.env` file based on `.env.example`.

4. Run the application:
   ```
   uvicorn src.main:app --reload
   ```

## API Endpoints

- **Knowledge Base**
  - Create, retrieve, and delete knowledge base entries.

- **Files**
  - Upload files and retrieve file information.

- **Chunks**
  - Store and retrieve chunk information.

- **Search**
  - Perform dense vector recall operations.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.