# HaloLight API - Python/FastAPI

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-ISC-blue.svg)](LICENSE)

HaloLight Backend API implementation using Python, FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Features

- **FastAPI 0.115+** - Modern, fast web framework with automatic OpenAPI documentation
- **SQLAlchemy 2.0** - Powerful ORM with type hints support
- **Alembic** - Database migration management
- **Pydantic v2** - Data validation using Python type annotations
- **JWT Authentication** - Secure token-based authentication
- **Password Hashing** - bcrypt password hashing
- **CORS Support** - Cross-Origin Resource Sharing enabled
- **Docker Support** - Containerized deployment with Docker Compose
- **PostgreSQL** - Production-ready relational database

## Tech Stack

- **Framework**: FastAPI 0.115+
- **ORM**: SQLAlchemy 2.0.36+
- **Database**: PostgreSQL 16
- **Migrations**: Alembic 1.14+
- **Validation**: Pydantic v2
- **Authentication**: python-jose (JWT)
- **Password Hashing**: passlib + bcrypt
- **Server**: Uvicorn with uvloop

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 16 or higher
- pip or poetry for dependency management

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/halolight/halolight-api-python.git
cd halolight-api-python
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and update the following:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/halolight
JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

### 5. Run database migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 6. Start the server

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/api/redoc

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL + API)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Using Docker only

```bash
# Build image
docker build -t halolight-api .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/halolight \
  -e JWT_SECRET_KEY=your-secret-key \
  halolight-api
```

## API Endpoints

### Health & Info

- `GET /` - API information
- `GET /health` - Health check

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user (placeholder)

### Users

- `GET /api/users/me` - Get current user profile (authenticated)
- `GET /api/users` - List all users with pagination (admin only)
- `GET /api/users/{user_id}` - Get user by ID (admin only)
- `POST /api/users` - Create user (admin only)
- `PATCH /api/users/{user_id}` - Update user (admin only)
- `DELETE /api/users/{user_id}` - Delete user (admin only)

## API Usage Examples

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Get Current User Profile

```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### List Users (Admin only)

```bash
curl -X GET "http://localhost:8000/api/users?page=1&page_size=10" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

## Database Schema

### User Model

```python
class User:
    id: str              # Primary key (auto-generated)
    email: str           # Unique email address
    name: str | None     # Optional display name
    password: str        # Hashed password
    role: UserRole       # USER or ADMIN
    avatar: str | None   # Optional avatar URL
    status: str          # Account status (default: "active")
    created_at: datetime # Creation timestamp
    updated_at: datetime # Last update timestamp
```

## Development

### Project Structure

```
halolight-api-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── users.py         # User routes
│   │   └── deps.py          # Dependency injection
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py          # SQLAlchemy User model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py          # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py  # Business logic
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration settings
│   │   ├── security.py      # Security utilities
│   │   └── database.py      # Database connection
│   └── utils/
│       └── __init__.py
├── alembic/                 # Database migrations
│   ├── versions/
│   └── env.py
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests with pytest
pytest

# Run tests with coverage
pytest --cov=app tests/
```

### Code Quality

```bash
# Format code with Black
black app tests

# Lint with Ruff
ruff check app tests

# Type check with mypy
mypy app
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `HaloLight API` |
| `APP_VERSION` | Application version | `1.0.0` |
| `DEBUG` | Enable debug mode | `false` |
| `ENVIRONMENT` | Environment (development/production/test) | `development` |
| `API_PREFIX` | API prefix path | `/api` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `DATABASE_URL` | PostgreSQL connection URL | **Required** |
| `DATABASE_ECHO` | Echo SQL queries | `false` |
| `JWT_SECRET_KEY` | JWT secret key | **Required** |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `10080` (7 days) |
| `PASSWORD_MIN_LENGTH` | Minimum password length | `6` |

## Security

- Passwords are hashed using bcrypt
- JWT tokens are used for authentication
- CORS is configured to allow specific origins
- SQL injection protection via SQLAlchemy ORM
- Input validation via Pydantic schemas

## Architecture

This API follows a layered architecture:

1. **Routes** (`api/`) - Handle HTTP requests and responses
2. **Services** (`services/`) - Business logic and data manipulation
3. **Models** (`models/`) - Database models and ORM mappings
4. **Schemas** (`schemas/`) - Request/response validation and serialization
5. **Core** (`core/`) - Configuration, security, and database setup

## Performance

- Async/await support for non-blocking I/O
- Connection pooling with SQLAlchemy
- JWT stateless authentication (no database lookups per request)
- Efficient pagination for list endpoints

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## Related Projects

- [halolight](https://github.com/halolight/halolight) - Next.js reference implementation
- [halolight-vue](https://github.com/halolight/halolight-vue) - Vue 3 reference implementation
- [halolight-api-node](https://github.com/halolight/halolight-api-node) - Node.js/Express API
- [docs](https://github.com/halolight/docs) - Documentation and specifications

## Documentation

📚 Complete Documentation: https://halolight.docs.h7ml.cn/

## License

ISC

## Support

For issues and questions, please open an issue on [GitHub](https://github.com/halolight/halolight-api-python/issues).
