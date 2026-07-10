---
name: test-writer
description: "Write effective tests following testing best practices and patterns."
metadata:
  trigger-keywords: "test, testing, pytest, unit test, integration test"
  trigger-patterns: "^test, ^write test, ^add test, ^pytest"
---

# Test Writer Skill

Write effective, maintainable tests following best practices and project patterns.

---

## When to Use

- Adding tests for new features
- Writing regression tests for bugs
- Setting up test infrastructure
- Improving test coverage

**Do NOT use when:**
- Just fixing existing tests (edit directly)
- Writing one-off debug scripts (use notebooks)

---

## Inputs

### Required
- What to test: Function, class, endpoint
- Test type: Unit, integration, e2e
- Scope: Happy path and edge cases

### Optional
- Mock requirements: External dependencies
- Test data: Fixtures needed
- Coverage target: Minimum coverage %

---

## Steps

### Step 1: Choose Test Type

**What to do:**
Determine appropriate test type based on scope.

**Test Types:**

| Type | Scope | Speed | Location |
|------|-------|-------|----------|
| Unit | Single function/class | Fast | `tests/unit/` |
| Integration | Multiple components | Medium | `tests/integration/` |
| API | HTTP endpoints | Medium | `tests/api/` |
| E2E | Full user flow | Slow | `tests/e2e/` |

**Guidelines:**
- Unit tests: 70%+ of test suite
- Integration: Complex business logic
- API: All endpoints
- E2E: Critical user flows only

### Step 2: Set Up Test Structure

**What to do:**
Create test file with proper structure.

**Code Pattern:**
```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.user import create_user, get_user
from src.models.user import User


class TestCreateUser:
    """Test cases for create_user() function."""
    
    def test_create_user_success(self, db_session):
        """Test successful user creation with valid data."""
        # Arrange
        user_data = {"email": "test@example.com", "name": "Test User"}
        
        # Act
        user = create_user(db_session, user_data)
        
        # Assert
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.id is not None
        assert user.created_at is not None
    
    def test_create_user_duplicate_email(self, db_session):
        """Test that duplicate email raises error."""
        # Arrange
        existing = User(email="dup@example.com", name="Existing")
        db_session.add(existing)
        db_session.commit()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already exists"):
            create_user(db_session, {"email": "dup@example.com", "name": "New"})
    
    def test_create_user_invalid_email(self, db_session):
        """Test that invalid email format raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid email format"):
            create_user(db_session, {"email": "not-an-email", "name": "Test"})


class TestGetUser:
    """Test cases for get_user() function."""
    
    def test_get_user_by_id_success(self, db_session):
        """Test retrieving user by ID."""
        # Arrange
        user = User(email="get@example.com", name="Get Test")
        db_session.add(user)
        db_session.commit()
        
        # Act
        result = get_user(db_session, user.id)
        
        # Assert
        assert result is not None
        assert result.email == "get@example.com"
    
    def test_get_user_not_found(self, db_session):
        """Test that non-existent ID returns None."""
        # Act
        result = get_user(db_session, 99999)
        
        # Assert
        assert result is None
```

### Step 3: Use Fixtures

**What to do:**
Create reusable test fixtures.

**Code Pattern:**
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Create fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(email="sample@example.com", name="Sample User")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def mock_external_api():
    """Mock external API calls."""
    with patch("src.services.external.requests.get") as mock:
        mock.return_value.json.return_value = {"status": "ok"}
        mock.return_value.status_code = 200
        yield mock
```

### Step 4: Write Integration Tests

**What to do:**
Test component interactions.

**Code Pattern:**
```python
# tests/integration/test_user_workflow.py
class TestUserRegistrationWorkflow:
    """Test complete user registration flow."""
    
    def test_full_registration_flow(self, db_session, client):
        """Test user can register, verify email, and login."""
        # Step 1: Register
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User"
        })
        assert response.status_code == 201
        user_id = response.json()["id"]
        
        # Step 2: Check email was "sent" (mock)
        # Verify email service called
        
        # Step 3: Verify email
        response = client.post(f"/auth/verify/{user_id}")
        assert response.status_code == 200
        
        # Step 4: Login
        response = client.post("/auth/login", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 200
        assert "token" in response.json()
```

### Step 5: Write API Tests

**What to do:**
Test HTTP endpoints.

**Code Pattern:**
```python
# tests/api/test_users_endpoint.py
from fastapi.testclient import TestClient

class TestUserEndpoints:
    """Test user API endpoints."""
    
    def test_create_user(self, client: TestClient):
        """Test POST /users creates user."""
        response = client.post("/users", json={
            "email": "api@test.com",
            "name": "API Test"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "api@test.com"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_user_validation_error(self, client: TestClient):
        """Test validation errors return 422."""
        response = client.post("/users", json={
            "email": "invalid-email"
        })
        
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_get_user_not_found(self, client: TestClient):
        """Test 404 for non-existent user."""
        response = client.get("/users/99999")
        
        assert response.status_code == 404
```

### Step 6: Add Parametrized Tests

**What to do:**
Test multiple scenarios efficiently.

**Code Pattern:**
```python
@pytest.mark.parametrize("email,expected_error", [
    ("", "Email is required"),
    ("not-an-email", "Invalid email format"),
    ("a" * 256 + "@test.com", "Email too long"),
    ("test@", "Invalid email format"),
])
def test_email_validation(email, expected_error, db_session):
    """Test various invalid email formats."""
    with pytest.raises(ValueError, match=expected_error):
        create_user(db_session, {"email": email, "name": "Test"})
```

---

## Validation

### Success Criteria
- [ ] Tests are isolated (no shared state)
- [ ] Fixtures used for common setup
- [ ] Both happy path and error cases covered
- [ ] Mocks for external dependencies
- [ ] Descriptive test names
- [ ] Tests run fast (< 100ms per unit test)

### Verification Commands
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test
uv run pytest tests/unit/test_user_service.py::TestCreateUser::test_create_user_success -v

# Run last failed tests
uv run pytest --lf

# Run with debugging
uv run pytest -vv -s
```

---

## Rollback

### If Tests Break

```bash
# Skip broken tests temporarily
@pytest.mark.skip(reason="Needs fix")
def test_broken():
    pass

# Or use xfail for expected failures
@pytest.mark.xfail(reason="Known issue #123")
def test_known_issue():
    pass
```

---

## Common Mistakes

1. **No test isolation**: Tests depend on each other
2. **Testing implementation**: Test behavior, not internals
3. **No assertions**: Tests that don't verify anything
4. **Slow tests**: Not using mocks for external calls
5. **Brittle tests**: Testing exact error messages
6. **Missing edge cases**: Only testing happy path

---

## Related Skills

- **API Endpoint**: For testing API routes
- **Database Migration**: For testing migrations
- **Data Ingestion**: For testing data pipelines

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **Testing Standards**: `docs/development_standards.md`
- **Pytest Docs**: https://docs.pytest.org/

---

## Examples

### Example 1: Testing with Mocks

**Scenario:** Testing service that calls external API.

```python
def test_service_with_mock(mock_external_api, db_session):
    """Test service handles API response correctly."""
    mock_external_api.return_value.json.return_value = {
        "data": "test"
    }
    
    result = my_service(db_session)
    
    assert result == "processed test"
    mock_external_api.assert_called_once()
```

### Example 2: Testing Exceptions

**Scenario:** Testing error handling.

```python
def test_service_handles_timeout(mock_external_api, db_session):
    """Test service handles API timeout gracefully."""
    from requests.exceptions import Timeout
    mock_external_api.side_effect = Timeout()
    
    with pytest.raises(ServiceError, match="External service unavailable"):
        my_service(db_session)
```

---

**Remember: Tests are documentation - make them readable!**
