# PFSense APIv2 Documentation

## Base Client Implementation

The base client provides a robust foundation with:

- Authentication via API Key (`PFSENSE_API_KEY` environment variable)
- Configurable base URL (default: https://pf.ypgoc.com)
- SSL verification control (`PFSENSE_VERIFY_SSL` environment variable)
- Comprehensive error handling with specific exception types
- Query parameter support (filtering, sorting, pagination)
- Automatic response validation

### Error Handling

All API responses are automatically validated and appropriate exceptions are raised:

| Status Code | Exception Type            | Description                |
| ----------- | ------------------------- | -------------------------- |
| 400         | BadRequestError           | Input validation errors    |
| 401         | UnauthorizedError         | Authentication failure     |
| 403         | ForbiddenError            | Insufficient privileges    |
| 404         | NotFoundError             | Resource not found         |
| 405         | MethodNotAllowedError     | HTTP method not supported  |
| 406         | NotAcceptableError        | Unsupported content format |
| 409         | ConflictError             | Request conflicts          |
| 415         | UnsupportedMediaTypeError | Unsupported content-type   |
| 422         | UnprocessableEntityError  | Missing dependency         |
| 424         | FailedDependencyError     | Missing dependency         |
| 500         | InternalServerError       | Server error               |
| 503         | ServiceUnavailableError   | Service unavailable        |

### Query Parameters

The API supports standard query parameters:

- `limit`: Number of items to return
- `offset`: Starting point in dataset
- `sort_by`: Fields to sort by
- `sort_order`: Sort order (SORT_ASC or SORT_DESC)
- `filter`: Complex filtering conditions

## DHCP Server API

Base endpoint: `/api/v2/services/dhcp_server`

### Methods

#### 1. List DHCP Servers (GET /api/v2/services/dhcp_server)

```python
def get_dhcp_servers(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_by: Optional[List[str]] = None,
    sort_order: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

#### 2. Get Single Server (GET /api/v2/services/dhcp_server/{server_id})

```python
def get_dhcp_server(server_id: str) -> Dict[str, Any]
```

#### 3. Create Server (POST /api/v2/services/dhcp_server)

```python
def create_dhcp_server(server_data: Dict[str, Any]) -> Dict[str, Any]
```

#### 4. Update Server (PUT /api/v2/services/dhcp_server/{server_id})

```python
def update_dhcp_server(server_id: str, server_data: Dict[str, Any]) -> Dict[str, Any]
```

#### 5. Delete Server (DELETE /api/v2/services/dhcp_server/{server_id})

```python
def delete_dhcp_server(server_id: str) -> Dict[str, Any]
```

#### 6. Apply Changes (POST /api/v2/services/dhcp_server/apply)

```python
def apply_dhcp_changes() -> Dict[str, Any]
```

### Implementation Status

All core CRUD operations implemented  
 Comprehensive error handling  
 Query parameter support  
 Pagination support  
 Sorting capabilities  
 Filtering support

### Response Format

All responses follow the standard format:

```json
{
  "code": 200,
  "status": "ok",
  "response_id": "string",
  "message": "string",
  "data": {
    // Response data here
  },
  "_links": {
    // HATEOAS links here
  }
}
```
