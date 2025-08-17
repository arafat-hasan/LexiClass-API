# LexiClass API

LexiClass API is a powerful text classification service that provides RESTful endpoints for managing document classification projects, training models, and making predictions.

## Features

- Project Management: Create and manage classification projects
- Document Management: Upload, organize and manage documents for classification
- Model Training: Train custom classification models
- Predictions: Get predictions for new documents
- Asynchronous Processing: Long-running tasks handled via Celery
- API Documentation: OpenAPI/Swagger documentation
- Authentication & Authorization: Secure API access
- Monitoring: Prometheus metrics integration

## Technology Stack

- FastAPI: Modern, fast web framework for building APIs
- SQLAlchemy: SQL toolkit and ORM
- Celery: Distributed task queue
- PostgreSQL: Primary database
- Redis: Cache and Celery broker
- Prometheus: Metrics and monitoring
- Docker: Containerization
- Poetry: Python dependency management

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- Docker & Docker Compose (optional)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lexiclass-api.git
   cd lexiclass-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install poetry
   poetry install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start development server:
   ```bash
   uvicorn src.lexiclass_api.main:app --reload
   ```

7. Start Celery worker (in a separate terminal):
   ```bash
   celery -A src.lexiclass_api.worker worker --loglevel=info
   ```

### Docker Setup

1. Build and start services:
   ```bash
   docker-compose up -d --build
   ```

2. Run migrations:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Core Endpoints

### System
- `GET /health` - Health check endpoint
- `GET /version` - API version information

### Projects
- `POST /projects` - Create a new project
- `GET /projects/{id}` - Get project details
- `DELETE /projects/{id}` - Delete a project

### Documents
- `POST /projects/{id}/documents` - Add documents
- `DELETE /projects/{id}/documents` - Remove documents
- `GET /projects/{id}/documents` - List documents (paginated)

### Indexing
- `POST /projects/{id}/index` - Trigger indexing task
- `GET /projects/{id}/index/status` - Check index status

### Training
- `POST /projects/{id}/train` - Start model training
- `GET /projects/{id}/train/status` - Check training status

### Prediction
- `POST /projects/{id}/predict` - Get predictions
- `GET /projects/{id}/predict/{prediction_id}` - Get prediction results
- `GET /projects/{id}/predict/latest` - Get latest predictions

### Tasks
- `GET /tasks/{task_id}` - Get task status
- `GET /projects/{id}/tasks` - List project tasks
- `PATCH /tasks/{task_id}/cancel` - Cancel task

## Environment Variables

Key environment variables:

```env
# Application
APP_NAME=LexiClass API
APP_VERSION=0.1.0
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/lexiclass

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

## Development

### Code Style

We use:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking
- isort for import sorting

Run quality checks:
```bash
# Format code
black src/
isort src/

# Run linters
flake8 src/
mypy src/
```

### Testing

Run tests with pytest:
```bash
pytest
```

With coverage:
```bash
pytest --cov=src/

# Generate coverage report
coverage html
```

## Deployment

### Production Setup

1. Set secure production values in `.env`:
   ```env
   DEBUG=False
   SECRET_KEY=<secure-secret>
   ```

2. Use production-grade servers:
   ```bash
   gunicorn src.lexiclass_api.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. Set up SSL/TLS with a reverse proxy (nginx/traefik)

### Monitoring

- `/metrics` endpoint provides Prometheus metrics
- Configure Prometheus to scrape metrics
- Use Grafana for visualization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

[License Type] - See LICENSE file for details
