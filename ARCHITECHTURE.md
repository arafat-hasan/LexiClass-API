# Lexiclass System - Architecture & Documentation

## Overview

Lexiclass is a distributed ML-driven document classification platform built with a microservice architecture. The system enables automated document categorization using Support Vector Machines (SVM) with ICU tokenization.

## System Architecture

### Core Components

| Component | Responsibility | Tech Stack |
|-----------|---------------|------------|
| **Lexiclass (ML Library)** | ML core - tokenization, vectorization, training, prediction | Python, scikit-learn (SVM), ICU tokenizer |
| **Lexiclass-Core** | Shared models, schemas, configs, and utilities | Python, SQLAlchemy, Pydantic |
| **Lexiclass-API** | REST interface for user/project/document management and job submission | FastAPI, Redis (job queue), PostgreSQL |
| **Lexiclass-Worker** | Asynchronous task executor for indexing/training/prediction | Celery, Redis, Lexiclass, Lexiclass-Core |

### Component Interaction

```
┌──────────────────────────┐
│        Client / UI       │
│  (e.g., Dashboard, CLI)  │
└────────────┬─────────────┘
             │ REST API
             ▼
┌────────────────────────────┐
│      Lexiclass-API         │
│ - FastAPI service          │
│ - Uses Lexiclass-Core      │
│ - Submits jobs to Redis    │
└───────┬──────────────┬─────┘
 Celery │              │
 Task   │              │
 Queue  │              │
        ▼              ▼
┌──────────┐   ┌──────────────────────────┐
│ Redis    │   │    PostgreSQL Database   │
│ (Broker) │   │ - Shared via Core models │
└──────┬───┘   └──────────────────────────┘
       │               ▲        
       ▼               │ 
┌──────────────────────┴───┐
│    Lexiclass-Worker      │
│ - Celery worker process  │
│ - Executes ML tasks      │
│ - Uses Lexiclass + Core  │
└──────────────────────────┘
```

## Dependency Graph

```
Lexiclass (Independent ML Library)
└── Standalone, stateless ML logic
    (tokenize, index, train, predict)


Lexiclass-Core (Foundation Layer)
├── Defines ORM Models, Schemas, Configs, and Utilities
└── Acts as the shared data contract for all services
      ↑
      │
      ├── Lexiclass-API
      │    ├── Uses Core ORM models and Schemas
      │    ├── Exposes REST endpoints
      │    └── Dispatches ML tasks to Worker
      │
      └── Lexiclass-Worker
           ├── Depends on Core for ORM/Schemas
           ├── Imports Lexiclass ML Library for task execution
           └── Persists results via Core models

```

### Dependency Details

- **Lexiclass-Core**: No dependencies on other components
  - Defines ORM models, schemas, configuration constants, shared utilities
  - Single source of truth for data structures

- **Lexiclass (ML Library)**: Standalone ML logic
  - Pure ML operations, stateless

- **Lexiclass-API**: Depends on Core
  - Uses Lexiclass indirectly through Workers
  - Handles REST endpoints and job orchestration

- **Lexiclass-Worker**: Depends on both Core and Lexiclass
  - Executes ML tasks
  - Persists results via Core models

## Component Details

### Lexiclass-Core

**Purpose**: Centralized module for shared infrastructure

**Responsibilities**:
- Database models (SQLAlchemy ORM)
- Pydantic schemas for API I/O
- Configuration management (storage, Redis, DB)
- Shared enums and constants
- Utility functions

**Key Features**:
- Acts as single source of truth between API and Worker
- Ensures consistency across services
- Provides type safety with Pydantic

### Lexiclass (ML Library)

**Purpose**: Pure ML logic for document classification

**Responsibilities**:
- Document tokenization (ICU)
- Feature extraction (Bag of Words / TF-IDF)
- Model training (SVM)
- Prediction and vector search

**Key Features**:
- Stateless design
- Can be reused independently
- Easy to test in isolation
- No direct database dependencies

### Lexiclass-API

**Purpose**: FastAPI-based REST service

**Responsibilities**:
- Project and document CRUD operations
- Field definition management
- Job submission endpoints (`/index`, `/train`, `/predict`)
- Task dispatch via Celery
- Job status polling

**Key Features**:
- Does not execute ML tasks directly
- Delegates to Workers via Celery
- Handles authentication and authorization
- Request validation using Core schemas

### Lexiclass-Worker

**Purpose**: Celery worker for async ML execution

**Responsibilities**:
- Execute `index_documents()` tasks
- Execute `train_model()` tasks
- Execute `predict()` tasks
- Update job status
- Persist results to database

**Key Features**:
- Connected to Redis for task queue
- Uses Lexiclass for ML operations
- Uses Core for database persistence
- Scalable (can run multiple workers)

## Data Flow Examples

### Training Job Flow

1. **Client → API**
   - User requests `POST /projects/{project_id}/fields/{field_id}/train`

2. **API → Redis**
   - API validates input using Core schemas
   - Submits Celery task: `train_field_model.delay(field_id, project_id)`
   - Returns job ID to client

3. **Worker → ML → Database & Disk**
   - Worker receives task from Redis
   - Loads field, classes, and training labels via Core models
   - Determines next version number (latest_version + 1)
   - Creates model record with TRAINING status
   - Trains SVM classifier using scikit-learn
   - Saves model files to: `STORAGE_PATH/{project-id}/models/{field-id}/v{version}/`
     - `model.pkl`: Trained classifier
     - `vectorizer.pkl`: TF-IDF vectorizer
   - Updates model record with READY status, accuracy, and metrics
   - Updates job status

4. **Client polls API**
   - Client requests `GET /tasks/{id}`
   - API returns status from Redis or database

### Prediction Flow

1. **Client submits documents** via API
2. **API queues prediction task** with field_id and document_ids
3. **Worker loads trained model** using dynamically generated path
4. **Worker runs predictions** using Lexiclass
5. **Results saved** to:
   - **Disk**: Complete prediction scores in `STORAGE_PATH/{project-id}/predictions/{field-id}/predictions_v{version}.jsonl`
   - **Database**: Latest prediction per document in prediction table
6. **Client retrieves results** via API from database (fast access) or disk (historical data)

## Storage & Persistence

| Storage Type | Purpose | Technology |
|--------------|---------|------------|
| **PostgreSQL** | Metadata storage | Projects, documents, models, users |
| **Disk/Object Storage** | Serialized models, document files, prediction scores | Local filesystem or S3-compatible |
| **Redis** | Task queue, job status cache | In-memory key-value store |

### Database Schema Design

#### ID Type: BIGSERIAL
All tables use `BIGSERIAL` (auto-incrementing 64-bit integer) as primary keys instead of UUID:
- Better performance for indexing and joins
- Smaller storage footprint
- Simpler integer-based references

#### Model File Path Generation
Model and vectorizer paths are generated dynamically instead of being stored in the database:
- **Pattern**: `STORAGE_PATH/{project-id}/models/{field-id}/v{version-no}/model.pkl`
- **Pattern**: `STORAGE_PATH/{project-id}/models/{field-id}/v{version-no}/vectorizer.pkl`
- Eliminates redundant path storage in database
- Ensures consistent naming convention
- Simplifies model versioning

#### Prediction Storage Strategy
Predictions are stored in two places:

1. **Database (prediction table)**:
   - Stores only the **latest** prediction per document per field
   - Contains: document_id, field_id, class_id, model_version, confidence
   - Unique constraint on (document_id, field_id)
   - No model_id column - version number is sufficient

2. **Disk (JSONL files)**:
   - **Pattern**: `STORAGE_PATH/{project-id}/predictions/{field-id}/predictions_v{version}.jsonl`
   - Stores complete prediction scores for all documents for each model version
   - Allows historical analysis and comparison across versions
   - Each file contains predictions from one specific model version
   - One field can have multiple prediction files (one per version)

When predictions are run:
- New predictions overwrite existing predictions in the database
- Complete scores are appended to versioned JSONL files on disk
- Database always reflects the most recent prediction for quick access

## Development Workflow

### Setting Up Local Environment

1. **Clone all repositories**
   ```bash
   git clone <lexiclass-core-repo>
   git clone <lexiclass-repo>
   git clone <lexiclass-api-repo>
   git clone <lexiclass-worker-repo>
   ```

2. **Install dependencies**
   - Start with Core (foundation)
   - Then ML library
   - Finally API and Worker

3. **Set up infrastructure**
   - PostgreSQL database
   - Redis instance
   - Configure environment variables

4. **Start services**
   - API server
   - Worker process(es)

### Making Changes

**When modifying Core**:
- Update both API and Worker if schema changes
- Run migrations for database changes
- Update all dependent repositories

**When modifying ML Library**:
- Run unit tests in isolation
- Test integration with Worker
- Update API documentation if interfaces change

**When modifying API**:
- Update OpenAPI documentation
- Test with Worker integration
- Update client SDKs if available

**When modifying Worker**:
- Test with actual ML tasks
- Verify database persistence
- Check error handling and retries

## Key Design Decisions

### Why Microservices?

- **Scalability**: Workers can scale independently
- **Separation of concerns**: ML logic isolated from API
- **Flexibility**: Easy to swap implementations
- **Fault tolerance**: API can continue if workers are down

### Why Celery + Redis?

- **Async processing**: Long-running ML tasks don't block API
- **Reliability**: Task retry and failure handling
- **Monitoring**: Built-in task monitoring capabilities
- **Scalability**: Easy to add more workers

### Why SVM?

- **Accuracy**: Good performance for text classification
- **Efficiency**: Fast training and prediction
- **Interpretability**: Feature weights provide insight
- **Proven**: Well-established algorithm

## Common Operations

### Adding a New ML Algorithm

1. Extend Lexiclass library with new algorithm
2. Update Core schemas if new parameters needed
3. Add new task in Worker
4. Add API endpoint for triggering
5. Update documentation

### Adding a New API Endpoint

1. Define Pydantic schemas in Core
2. Create endpoint in API
3. Implement business logic
4. Add tests
5. Update OpenAPI documentation

### Database Migration

1. Update models in Core
2. Generate migration script
3. Test migration on development database
4. Apply to production with rollback plan
5. Update dependent code in API and Worker

## Testing Strategy

| Component | Test Types | Focus Areas |
|-----------|-----------|-------------|
| **Core** | Unit tests | Model validation, schema serialization |
| **ML Library** | Unit + integration | Algorithm accuracy, tokenization |
| **API** | Unit + integration + E2E | Endpoints, validation, auth |
| **Worker** | Integration tests | Task execution, error handling |

## Monitoring & Observability

### Key Metrics

- API response times
- Worker task processing times
- Model training duration
- Prediction accuracy
- Queue depth (Redis)
- Database connection pool usage

### Logging

- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs for request tracing
- Separate logs for API and Worker

## Security Considerations

- API authentication and authorization
- Input validation using Pydantic
- SQL injection prevention via ORM
- File upload size limits
- Rate limiting on API endpoints
- Secure storage of trained models

## Deployment

### Container Strategy

Each component runs in separate container:
- `lexiclass-api:latest`
- `lexiclass-worker:latest`
- `postgres:14`
- `redis:7`

### Environment Configuration

- Development: Local setup with minimal data
- Staging: Production-like with synthetic data
- Production: Full scale with monitoring

## Troubleshooting

### Common Issues

**Worker not processing tasks**:
- Check Redis connection
- Verify Celery configuration
- Check worker logs for errors

**API errors**:
- Verify database connection
- Check Redis availability
- Review request validation errors

**Model training failures**:
- Verify sufficient training data
- Check disk space for model storage
- Review ML library logs

## Resources

### Documentation

- API documentation: `/docs` (Swagger UI)
- Core models: See SQLAlchemy definitions
- ML library: See docstrings in source code

### Repository Structure

```
Lexiclass/              # ML Library
Lexiclass-Core/         # Shared infrastructure
Lexiclass-API/          # FastAPI service
Lexiclass-Worker/       # Celery workers
```

## Contributing

When contributing to any component:

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Consider impact on dependent components
5. Run full integration tests before PR

## Version Compatibility

Maintain compatibility matrix between components:
- Core version X requires ML Library >= Y
- API version A requires Core >= B
- Worker version M requires Core >= N and ML Library >= O

## File Structure on Disk

```
STORAGE_PATH/
├── {project-id}/
│   ├── documents/
│   │   ├── {document-id}.txt
│   │   └── ...
│   ├── models/
│   │   ├── {field-id}/
│   │   │   ├── v1/
│   │   │   │   ├── model.pkl
│   │   │   │   └── vectorizer.pkl
│   │   │   ├── v2/
│   │   │   │   ├── model.pkl
│   │   │   │   └── vectorizer.pkl
│   │   │   └── ...
│   │   └── ...
│   └── predictions/
│       ├── {field-id}/
│       │   ├── predictions_v1.jsonl
│       │   ├── predictions_v2.jsonl
│       │   └── ...
│       └── ...
└── ...
```

Each JSONL prediction file contains entries like:
```json
{"document_id": 123, "predicted_class": "positive", "class_id": 1, "confidence": 0.95, "model_version": 1}
{"document_id": 456, "predicted_class": "negative", "class_id": 2, "confidence": 0.87, "model_version": 1}
```

---

**Last Updated**: 2025-10-30
**Maintained By**: Development Team
**Current Version**: See individual component versions