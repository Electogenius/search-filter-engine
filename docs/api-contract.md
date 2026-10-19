# API Contract Specification

This document defines the REST API contract for the **Search and Filter Engine for E-Commerce Application**. It serves as the single source of truth for communication between the frontend client and the FastAPI backend service.

---

## 1. System Overview

- **Base URL**: `http://localhost:8000`
- **Prefix**: `/api`
- **Content Type**: `application/json`
- **Status Codes**:
  - `200 OK`: Request succeeded.
  - `400 Bad Request`: Validation failure on input parameters.
  - `404 Not Found`: Target resource does not exist.
  - `501 Not Implemented`: Endpoint designated in scaffold, pending algorithm implementation.

---

## 2. Endpoints

### 2.1 Health Check

Returns the operational status of the backend engine.

- **Method**: `GET`
- **Path**: `/api/health`
- **Authentication**: None
- **Request Parameters**: None

#### Response `200 OK`
```json
{
  "status": "ok",
  "service": "search-filter-engine",
  "version": "0.1.0"
}
```

---

### 2.2 Product Search & Multi-Criteria Filtering

Searches the in-memory catalogue using full-text indexing, fuzzy spelling correction, multi-attribute filtering, and relevance ranking.

- **Method**: `GET`
- **Path**: `/api/search`
- **Request Query Parameters**:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | `string` | No | `""` | Free-text search query (supports typos via Levenshtein matching) |
| `category` | `string` | No | `null` | Exact category filter (e.g., `Computers`, `Audio`, `Electronics`) |
| `min_price` | `number` | No | `null` | Minimum price filter (inclusive, $\ge 0$) |
| `max_price` | `number` | No | `null` | Maximum price filter (inclusive, $\ge 0$) |
| `min_rating` | `number` | No | `null` | Minimum customer rating threshold ($0.0 - 5.0$) |
| `available` | `boolean` | No | `null` | When `true`, filters only in-stock items |
| `sort_by` | `string` | No | `"relevance"` | Sort ordering: `relevance`, `price_asc`, `price_desc`, `rating_desc` |
| `limit` | `integer` | No | `10` | Maximum results to return (top-k threshold, $1 \le k \le 50$) |
| `offset` | `integer` | No | `0` | Pagination start index ($\ge 0$) |

#### Response `200 OK`
```json
{
  "query": "wireles keybrd",
  "corrected_query": "wireless keyboard",
  "total": 2,
  "limit": 10,
  "offset": 0,
  "results": [
    {
      "id": "prod-001",
      "title": "Wireless Mechanical Keyboard",
      "description": "Compact mechanical keyboard with hot-swappable switches, RGB backlighting...",
      "category": "Computers",
      "price": 89.99,
      "rating": 4.7,
      "available": true,
      "score": 3.842
    },
    {
      "id": "prod-017",
      "title": "RGB Mechanical Gaming Keyboard",
      "description": "Linear mechanical switches with per-key RGB illumination...",
      "category": "Computers",
      "price": 109.99,
      "rating": 4.6,
      "available": true,
      "score": 2.115
    }
  ]
}
```

#### Response `400 Bad Request`
```json
{
  "detail": "Invalid parameter: min_price cannot be greater than max_price."
}
```

---

### 2.3 Prefix Autocomplete Suggestions

Provides real-time search suggestions as the user types into the search box, powered by a Trie (Prefix Tree).

- **Method**: `GET`
- **Path**: `/api/suggest`
- **Request Query Parameters**:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `prefix` | `string` | Yes | - | The query prefix typed by the user (min length: 1) |
| `limit` | `integer` | No | `5` | Maximum number of suggestions to return ($1 \le \text{limit} \le 20$) |

#### Response `200 OK`
```json
{
  "prefix": "wire",
  "suggestions": [
    "wireless mechanical keyboard",
    "wireless ergonomic mouse",
    "wireless noise-cancelling headphones"
  ]
}
```

#### Response `400 Bad Request`
```json
{
  "detail": "Query parameter 'prefix' must not be empty."
}
```

---

### 2.4 Related Product Recommendations

Recommends products frequently purchased or bundled together with the target product using market basket co-occurrence statistics.

- **Method**: `GET`
- **Path**: `/api/products/{id}/related`
- **Request Path Parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | Unique product identifier (e.g., `prod-001`) |

- **Request Query Parameters**:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `limit` | `integer` | No | `4` | Maximum number of recommendations to return ($1 \le \text{limit} \le 10$) |

#### Response `200 OK`
```json
{
  "product_id": "prod-001",
  "recommendations": [
    {
      "id": "prod-002",
      "title": "Wireless Ergonomic Mouse",
      "category": "Computers",
      "price": 45.5,
      "rating": 4.5,
      "available": true,
      "co_occurrence_count": 2
    },
    {
      "id": "prod-010",
      "title": "USB-C Multiport Adapter Hub 8-in-1",
      "category": "Accessories",
      "price": 34.99,
      "rating": 4.4,
      "available": true,
      "co_occurrence_count": 2
    }
  ]
}
```

#### Response `404 Not Found`
```json
{
  "detail": "Product with id 'prod-999' not found."
}
```

---

## 3. Data Types & Entity Models

### Product Schema
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "category": "string",
  "price": "float",
  "rating": "float",
  "available": "boolean",
  "score": "float (optional, relevance score in search results)"
}
```

### Basket Schema
```json
{
  "basket_id": "string",
  "items": ["string (product_ids)"]
}
```

