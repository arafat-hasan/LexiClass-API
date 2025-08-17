"""OpenAPI documentation configuration."""

description = """
# LexiClass API

LexiClass API is a powerful text classification service that provides RESTful endpoints for managing document classification projects, training models, and making predictions.

## Authentication

All API endpoints are protected and require authentication. To authenticate:

1. Get your API token from the authentication endpoint
2. Include the token in the Authorization header:
   ```
   Authorization: Bearer your-token-here
   ```

## Rate Limiting

API endpoints have rate limits to ensure fair usage:
- 100 requests per minute for most endpoints
- 1000 documents per request for batch operations
- 10 concurrent training jobs per project

## Error Handling

The API uses standard HTTP status codes and returns error responses in the following format:
```json
{
    "detail": "Error message here",
    "error_code": "ERROR_CODE",
    "params": {}
}
```

## Pagination

List endpoints support pagination with the following query parameters:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100, max: 1000)

Response format:
```json
{
    "items": [],
    "total": 0,
    "skip": 0,
    "limit": 100
}
```
"""

tags_metadata = [
    {
        "name": "system",
        "description": "System-level operations like health checks and version info",
    },
    {
        "name": "projects",
        "description": "Operations with classification projects",
    },
    {
        "name": "documents",
        "description": "Document management within projects",
    },
    {
        "name": "indexing",
        "description": "Document indexing operations",
    },
    {
        "name": "training",
        "description": "Model training operations",
    },
    {
        "name": "prediction",
        "description": "Making predictions with trained models",
    },
    {
        "name": "tasks",
        "description": "Long-running task management",
    },
]

contact = {
    "name": "API Support",
    "url": "https://github.com/yourusername/lexiclass-api/issues",
    "email": "support@example.com",
}

license_info = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}

terms_of_service = "https://example.com/terms/"
