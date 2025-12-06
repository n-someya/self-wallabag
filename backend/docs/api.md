# Wallabag API Documentation

This document provides comprehensive documentation for the Wallabag API as implemented in the self-hosted Google Cloud Run version.

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints](#api-endpoints)
3. [Entry Management](#entry-management)
4. [Tag Management](#tag-management)
5. [User Management](#user-management)
6. [API Key Management](#api-key-management)
7. [Error Handling](#error-handling)
8. [Pagination](#pagination)
9. [Search](#search)
10. [Examples](#examples)

## Authentication

The API supports two authentication methods:

### 1. API Key Authentication (Recommended)

API key authentication is the recommended method for backend services and integrations.

**Headers:**

```
X-API-Key: your_api_key_here
```

To generate an API key:

```bash
# Using the provided script
./src/auth/generate-api-key.sh --user admin --name "My Integration" --expires 365
```

### 2. OAuth2 Authentication

OAuth2 is supported for web applications and third-party clients.

**Step 1:** Request an access token

```
POST /oauth/v2/token
Content-Type: application/x-www-form-urlencoded

grant_type=password&client_id=CLIENT_ID&client_secret=CLIENT_SECRET&username=USER&password=PASSWORD
```

**Step 2:** Use the token in subsequent requests

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Access tokens expire after 1 hour by default. Use the refresh token to get a new access token.

## API Endpoints

All API endpoints are prefixed with `/api/`.

### Base URL

For Google Cloud Run deployments: `https://YOUR_SERVICE_NAME-HASH.run.app/api/`

### Content Types

- Request: `application/json`
- Response: `application/json`

## Entry Management

Entries are the core resource in Wallabag, representing saved articles.

### Get Entries

```
GET /api/entries
```

Query parameters:
- `page`: Page number (default: 1)
- `perPage`: Items per page (default: 30)
- `archive`: Filter by archive status (0 = unarchived, 1 = archived, all = all entries)
- `starred`: Filter by starred status (0 = unstarred, 1 = starred)
- `sort`: Sort entries (created, updated, archived)
- `order`: Sort order (asc, desc)
- `tags`: Filter by tags (comma-separated list)
- `since`: Get entries since timestamp (Unix timestamp)

Example:

```
GET /api/entries?page=1&perPage=10&archive=0&sort=created&order=desc
```

### Get a Single Entry

```
GET /api/entries/{entry_id}
```

### Create a New Entry

```
POST /api/entries
Content-Type: application/json

{
  "url": "https://example.com/article",
  "title": "Optional title",
  "tags": "tag1,tag2,tag3",
  "starred": 0,
  "archive": 0
}
```

Only the `url` field is required.

### Update an Entry

```
PATCH /api/entries/{entry_id}
Content-Type: application/json

{
  "title": "Updated title",
  "tags": "tag1,tag2",
  "starred": 1,
  "archive": 1
}
```

### Delete an Entry

```
DELETE /api/entries/{entry_id}
```

### Archive/Unarchive an Entry

```
PATCH /api/entries/{entry_id}
Content-Type: application/json

{
  "archive": 1  // 0 to unarchive
}
```

### Star/Unstar an Entry

```
PATCH /api/entries/{entry_id}
Content-Type: application/json

{
  "starred": 1  // 0 to unstar
}
```

## Tag Management

### Get All Tags

```
GET /api/tags
```

### Get Entry Tags

```
GET /api/entries/{entry_id}/tags
```

### Add Tags to an Entry

```
POST /api/entries/{entry_id}/tags
Content-Type: application/json

{
  "tags": "tag1,tag2,tag3"
}
```

### Remove a Tag from an Entry

```
DELETE /api/entries/{entry_id}/tags/{tag_id}
```

### Delete a Tag

```
DELETE /api/tags/{tag_id}
```

## User Management

### Get Current User

```
GET /api/user
```

### Update User Information

```
PATCH /api/user
Content-Type: application/json

{
  "name": "New Name",
  "email": "new.email@example.com"
}
```

### Change Password

```
PUT /api/user/change-password
Content-Type: application/json

{
  "current_password": "current_password",
  "new_password": "new_password"
}
```

## API Key Management

### Get API Keys

```
GET /api/api-keys
```

### Create API Key

```
POST /api/api-keys
Content-Type: application/json

{
  "name": "My Integration",
  "expires_after": 365  // days
}
```

### Delete API Key

```
DELETE /api/api-keys/{key_id}
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Server Error`: Server error

Error responses include details:

```json
{
  "error": {
    "code": 400,
    "message": "Invalid request parameters"
  }
}
```

## Pagination

Paginated responses include metadata:

```json
{
  "page": 1,
  "limit": 10,
  "pages": 5,
  "total": 42,
  "_links": {
    "first": "/api/entries?page=1&perPage=10",
    "last": "/api/entries?page=5&perPage=10",
    "next": "/api/entries?page=2&perPage=10"
  },
  "_embedded": {
    "items": [
      // items here
    ]
  }
}
```

## Search

Search across entries:

```
GET /api/search?term=search+term&page=1&perPage=10
```

Parameters:
- `term`: Search term
- `page`: Page number
- `perPage`: Items per page
- `archive`: Filter by archive status (0, 1, all)
- `starred`: Filter by starred status (0, 1)
- `sort`: Sort field
- `order`: Sort order

## Examples

### Python Example: Save a New Article

```python
import requests

# Configuration
api_url = "https://your-wallabag-instance.run.app/api"
api_key = "your_api_key_here"

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

# Save a new article
data = {
    "url": "https://example.com/interesting-article",
    "tags": "python,api,example"
}

response = requests.post(f"{api_url}/entries", headers=headers, json=data)
if response.status_code == 200:
    entry = response.json()
    print(f"Article saved with ID: {entry['id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### cURL Example: Get All Entries

```bash
curl -X GET "https://your-wallabag-instance.run.app/api/entries?perPage=10" \
     -H "X-API-Key: your_api_key_here"
```

### JavaScript Example: Search Entries

```javascript
const apiUrl = 'https://your-wallabag-instance.run.app/api';
const apiKey = 'your_api_key_here';

fetch(`${apiUrl}/search?term=example&perPage=5`, {
  headers: {
    'X-API-Key': apiKey
  }
})
.then(response => response.json())
.then(data => {
  console.log(`Found ${data.total} results`);
  data._embedded.items.forEach(item => {
    console.log(`- ${item.title}`);
  });
})
.catch(error => console.error('Error:', error));
```

## Rate Limiting

API requests are rate-limited to ensure service stability:

- 60 requests per minute per API key
- 600 requests per hour per API key

Limits can be configured in the application settings.

---

For more detailed information or support, please contact the system administrator.

*Last updated: October 2025*