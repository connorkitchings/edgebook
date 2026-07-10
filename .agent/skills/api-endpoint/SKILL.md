---
name: api-endpoint
description: "Create new API endpoint with proper validation, error handling, and tests."
metadata:
  trigger-keywords: "api, endpoint, route, fastapi, flask"
  trigger-patterns: "^api endpoint, ^new route, ^add endpoint"
---

# API Endpoint Skill

Create new REST API endpoints with proper validation, error handling, authentication, and tests.

---

## When to Use

- Adding new REST API endpoint
- Creating CRUD operations
- Implementing search/filter endpoints
- Adding authentication routes

**Do NOT use when:**
- Just modifying existing endpoint (edit directly)
- Creating GraphQL (use different skill)
- Adding WebSocket (use different skill)

---

## Inputs

### Required
- HTTP method: GET, POST, PUT, DELETE, etc.
- Path: URL pattern
- Purpose: What does this endpoint do?
- Schema: Request/response models

### Optional
- Auth: Authentication requirements
- Rate limiting: Public vs private
- Pagination: For list endpoints

---

## Steps

### Step 1: Define Schema

**What to do:**
Create Pydantic models for request/response.

**Code Pattern:**
```python
# src/api/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    """Request model for creating user."""
    email: str = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe"
            }
        }

class UserResponse(BaseModel):
    """Response model for user."""
    id: int
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy models

class UserListResponse(BaseModel):
    """Response model for user list."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
```

**Validation:**
- [ ] Request model validates input
- [ ] Response model excludes sensitive fields
- [ ] Examples provided in schema
- [ ] Types are correct

### Step 2: Create Endpoint

**What to do:**
Implement route handler with business logic.

**Code Pattern:**
```python
# src/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.api.schemas import UserCreate, UserResponse, UserListResponse
from src.api.deps import get_db, get_current_user
from src.models.user import User
from src.services.user import create_user, get_user, list_users

router = APIRouter(prefix="/users", tags=["users"])

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="Create a new user account with email and name."
)
async def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # If auth required
):
    """
    Create a new user.
    
    - **email**: Valid email address (unique)
    - **name**: Display name (1-100 chars)
    
    Returns created user with ID.
    """
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = create_user(db, user_data)
    return user

@router.get(
    "",
    response_model=UserListResponse,
    summary="List users",
    description="Get paginated list of users."
)
async def list_users_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """
    List users with pagination and optional search.
    
    - **page**: Page number (1-indexed)
    - **page_size**: Results per page (1-100)
    - **search**: Filter by name (optional)
    """
    users, total = list_users(db, page=page, page_size=page_size, search=search)
    
    return UserListResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    responses={
        404: {"description": "User not found"}
    }
)
async def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user details by ID."""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user"
)
async def update_user_endpoint(
    user_id: int,
    user_data: UserCreate,  # Or UserUpdate for partial updates
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user details."""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Authorization check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    updated_user = update_user(db, user_id, user_data)
    return updated_user

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user"
)
async def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user account."""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    delete_user(db, user_id)
    return None
```

**Validation:**
- [ ] Router has prefix and tags
- [ ] All CRUD operations implemented
- [ ] HTTP status codes correct
- [ ] Error handling complete
- [ ] Auth checks in place

### Step 3: Register Router

**What to do:**
Add router to main API application.

**Code Pattern:**
```python
# src/api/main.py
from fastapi import FastAPI
from src.api.endpoints import users, items, auth

app = FastAPI(
    title="My API",
    description="API description",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Validation:**
- [ ] Router imported and included
- [ ] Order correct (auth before protected routes)
- [ ] No path conflicts

### Step 4: Add Tests

**What to do:**
Write comprehensive tests for endpoint.

**Code Pattern:**
```python
# tests/api/test_users.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestCreateUser:
    """Tests for POST /users"""
    
    def test_create_user_success(self, db_session):
        """Test successful user creation."""
        response = client.post(
            "/users",
            json={"email": "test@example.com", "name": "Test User"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
    
    def test_create_user_duplicate_email(self, db_session):
        """Test error on duplicate email."""
        # Create first user
        client.post("/users", json={"email": "dup@example.com", "name": "User 1"})
        
        # Try to create second with same email
        response = client.post("/users", json={"email": "dup@example.com", "name": "User 2"})
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]
    
    def test_create_user_invalid_email(self):
        """Test validation of email format."""
        response = client.post("/users", json={"email": "not-an-email", "name": "Test"})
        assert response.status_code == 422  # Validation error

class TestListUsers:
    """Tests for GET /users"""
    
    def test_list_users_pagination(self, db_session):
        """Test pagination works correctly."""
        # Create test users
        for i in range(25):
            client.post("/users", json={"email": f"user{i}@test.com", "name": f"User {i}"})
        
        # Get first page
        response = client.get("/users?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1

class TestGetUser:
    """Tests for GET /users/{id}"""
    
    def test_get_user_success(self, db_session):
        """Test getting existing user."""
        # Create user
        create_response = client.post("/users", json={"email": "get@test.com", "name": "Get Test"})
        user_id = create_response.json()["id"]
        
        # Get user
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["email"] == "get@test.com"
    
    def test_get_user_not_found(self):
        """Test 404 for non-existent user."""
        response = client.get("/users/99999")
        assert response.status_code == 404
```

---

## Validation

### Success Criteria
- [ ] Schema models created and validated
- [ ] Endpoint implements full CRUD
- [ ] Error handling comprehensive
- [ ] Auth checks where needed
- [ ] Tests cover happy path and edge cases
- [ ] Documentation in docstrings

### Verification Commands
```bash
# Run tests
uv run pytest tests/api/test_users.py -v

# Check coverage
uv run pytest --cov=src/api/endpoints/users --cov-report=term-missing

# Test API manually
uv run uvicorn src.api.main:app --reload
# Visit http://localhost:8000/docs
```

---

## Rollback

### If Endpoint Has Issues

```python
# Temporarily disable endpoint
@router.post("", include_in_schema=False)  # Hide from docs
async def create_user_endpoint(...):
    raise HTTPException(status_code=503, detail="Temporarily unavailable")
    # Or return old behavior
```

### Remove Endpoint

1. Remove router registration from main.py
2. Delete endpoint file
3. Remove tests
4. Update API documentation

---

## Common Mistakes

1. **No input validation**: Always use Pydantic models
2. **Missing auth checks**: Check permissions on every endpoint
3. **No pagination**: List endpoints must be paginated
4. **Wrong status codes**: 201 for create, 204 for delete, etc.
5. **Exposing internal errors**: Don't return stack traces
6. **No rate limiting**: Add rate limits for public endpoints

---

## Related Skills

- **Database Migration**: If endpoint needs new tables
- **Test Writer**: For comprehensive test patterns
- **Doc Writer**: For API documentation

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **API Docs**: `docs/api/`
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

## Examples

### Example 1: Search Endpoint

**Pattern:** Complex filtering with query parameters

```python
@router.get("/search", response_model=ItemListResponse)
async def search_items(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("created_at", regex="^(created_at|price|name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Search items with filters."""
    pass
```

### Example 2: File Upload

**Pattern:** Handle multipart/form-data

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process file."""
    contents = await file.read()
    # Process file
    return {"filename": file.filename, "size": len(contents)}
```

---

**Remember: Document your endpoints well - they are your API contract!**
