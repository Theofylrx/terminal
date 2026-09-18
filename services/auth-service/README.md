# Auth Service

Authentication and authorization service for Terminal Trading System.

## Features

### ✅ User Registration
- Email and username validation
- Password strength requirements (8+ chars, uppercase, lowercase, digit)
- Duplicate email/username detection
- Optional initial capital tracking

### ✅ User Login
- Email + password authentication
- JWT access token (30 min expiration)
- JWT refresh token (7 day expiration)
- Last login tracking

### ✅ Token Management
- Access token refresh using refresh token
- Token validation
- User data extraction from tokens

### ✅ Security
- Bcrypt password hashing
- JWT token signing
- Password strength validation
- Account activation/deactivation
- Email verification support

### ✅ Repository Pattern
- UserRepository extends BaseRepository
- Clean data access layer
- Async/await throughout

## API Endpoints

### Registration
```http
POST /auth/register
Content-Type: application/json

{
  "email": "trader@example.com",
  "username": "trader1",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "initial_capital": 10000.0
}

Response: 201 Created
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "trader@example.com",
  "username": "trader1",
  "is_active": true,
  "is_verified": false,
  "current_capital": 10000.0
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "trader@example.com",
  "password": "SecurePass123"
}

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "trader@example.com",
    "username": "trader1"
  }
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "trader@example.com",
  "username": "trader1",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_verified": true,
  "current_capital": 9500.0,
  "last_login": "2024-01-01T12:00:00Z"
}
```

### Health Check
```http
GET /health

Response: 200 OK
{
  "status": "healthy",
  "service": "auth-service",
  "version": "0.1.0"
}
```

## Architecture

```
API Routes → Service Layer → Repository Layer → Database
(FastAPI)    (Business Logic)  (Data Access)    (PostgreSQL)
```

### Layers

**API Routes** (`api/routes/auth.py`)
- Request validation (Pydantic)
- Response formatting
- Dependency injection

**Service Layer** (`services/auth_service.py`)
- Business logic
- Password hashing/verification
- JWT token creation/validation
- User authentication

**Repository Layer** (`repositories/user_repository.py`)
- Database queries
- Extends BaseRepository
- User-specific queries

**Models** (shared library)
- User model with SQLAlchemy
- Relationships to positions, orders

## Configuration

Environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db

# JWT
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
REFRESH_TOKEN_EXPIRATION_DAYS=7

# Password Requirements
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_DIGITS=true
```

## Running Locally

```bash
cd services/auth-service

# Install dependencies
pip install -r requirements.txt

# Set environment
export DATABASE_URL=postgresql+asyncpg://...
export JWT_SECRET=your_secret

# Run service
python -m uvicorn services.auth_service.main:app --reload --port 8000
```

## Running with Docker

```bash
# Build and start
docker-compose up auth-service

# Access
curl http://localhost:8001/health
```

## Testing

```bash
# Register user
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass123",
    "initial_capital": 10000
  }'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123"
  }'

# Save access_token from response, then:
curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Security Features

- ✅ Bcrypt password hashing (cost factor 12)
- ✅ JWT token with HMAC SHA256 signing
- ✅ Token expiration (30 min access, 7 day refresh)
- ✅ Password strength validation
- ✅ Account activation status
- ✅ Email verification support
- ✅ No plain text passwords stored
- ✅ Non-root Docker container

## Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    initial_capital FLOAT,
    current_capital FLOAT,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

## Error Handling

**400 Bad Request**
- Email already registered
- Username already taken
- Invalid input data

**401 Unauthorized**
- Invalid credentials
- Expired token
- Invalid token

**403 Forbidden**
- User account inactive

**404 Not Found**
- User not found

**422 Unprocessable Entity**
- Validation errors

## Integration with API Gateway

Auth Service is accessed through API Gateway:

```
Client → API Gateway (:8080) → Auth Service (:8001)

Gateway routes:
  /api/v1/auth/* → http://auth-service:8000/auth/*
```

Gateway handles:
- Rate limiting
- CORS
- Request logging
- Metrics

Auth Service handles:
- User management
- Password verification
- Token generation
- User authentication

## Future Enhancements

- [ ] Email verification flow
- [ ] Password reset flow
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, GitHub)
- [ ] Session management
- [ ] User roles and permissions
- [ ] Account lockout after failed attempts
- [ ] Password history

## License

MIT
