# API Documentation

## Overview

CarScout AI provides several API endpoints for different purposes:
- **Public API** (`/v1/*`) - External access to listing data
- **Internal API** (`/internal/*`) - Service-to-service communication
- **Admin API** (`/admin/*`) - Administrative operations
- **Telegram Webhook** (`/telegram/*`) - Bot update handling

## Authentication

### Public API
Uses API keys passed in the `X-API-Key` header.

### Admin API
Requires authentication token in the `Authorization: Bearer <token>` header.

### Telegram Webhook
Validates the `X-Telegram-Bot-Api-Secret-Token` header.

## Endpoints

### Public API

#### GET /v1/listings/{listing_id}
Get details of a specific car listing.

**Response:**
```json
{
  "listing_id": "uuid",
  "brand": "BMW",
  "model": "X5",
  "year": 2018,
  "mileage_km": 120000,
  "price_bgn": 32000,
  "score": 8.5,
  "url": "https://..."
}
```

#### POST /v1/users/link-telegram
Link a Telegram account to user profile.

---

### Internal API

#### POST /internal/filter-rank
Filter and rank listings based on criteria.

**Request:**
```json
{
  "filters": {
    "brand_id": "bmw",
    "year": {"gte": 2016},
    "price_bgn": {"lte": 25000}
  },
  "top_k": 100,
  "dedupe": true
}
```

#### POST /internal/approve-for-channel
Approve a listing for channel posting.

**Request:**
```json
{
  "listing_id": "uuid"
}
```

---

### Admin API

#### POST /admin/rescrape
Trigger a rescrape for a specific source.

**Request:**
```json
{
  "source_id": "mobile_bg",
  "url": "optional_specific_url",
  "count": 100
}
```

#### POST /admin/re-evaluate
Re-evaluate listings through the AI pipeline.

**Request:**
```json
{
  "listing_ids": ["uuid1", "uuid2"]
}
```

#### POST /admin/blacklist/seller
Blacklist a seller by phone hash or seller ID.

**Request:**
```json
{
  "phone_hash": "hash_value"
}
```

#### GET /admin/brand-models
Get all brand-model mappings.

#### POST /admin/brand-models
Create or update brand-model mapping.

---

### Health Checks

#### GET /healthz
Basic health check.

**Response:**
```json
{
  "status": "healthy"
}
```

#### GET /readiness
Readiness check with dependency validation.

**Response:**
```json
{
  "status": "ready"
}
```

---

### Metrics

#### GET /metrics
Prometheus metrics endpoint.

Returns metrics in Prometheus format for monitoring.

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

- Public API: 100 requests per minute per API key
- Admin API: 1000 requests per minute
- Telegram Webhook: No limit (validated by secret token)
