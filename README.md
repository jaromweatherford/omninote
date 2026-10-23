# Omninote - Multi-Team Notes Service

A REST API service for team-scoped notes with authentication and authorization.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Start the Service
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

### Run Tests
```bash
docker-compose run --rm app pytest
```

### Seed Sample Data
```bash
docker-compose run --rm app python -m app.cli.seed
```

This creates:
- 3 users: `user1@example.com`, `user2@example.com`, `user3@example.com` (password: `password123`)
- 2 teams: `Engineering`, `Design`
- Memberships and sample notes

## Configuration

Copy `.env.example` to `.env` and adjust:
```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database user | `omninote` |
| `POSTGRES_PASSWORD` | Database password | `omninote` |
| `POSTGRES_DB` | Database name | `omninote` |
| `DATABASE_URL` | SQLAlchemy async URL | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | `dev-secret-change-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Register new user |
| POST | `/v1/auth/token` | Login, get JWT token |
| GET | `/v1/auth/me` | Get current user info |

### Teams
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/teams` | Create team (caller becomes admin) |
| GET | `/v1/teams` | List user's teams |
| GET | `/v1/teams/{team_id}` | Get team details |
| GET | `/v1/teams/{team_id}/members` | List team members |

### Notes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/teams/{team_id}/notes` | Create note |
| GET | `/v1/teams/{team_id}/notes` | List notes (paginated) |
| GET | `/v1/teams/{team_id}/notes/{note_id}` | Get note |
| PATCH | `/v1/teams/{team_id}/notes/{note_id}` | Update note |
| DELETE | `/v1/teams/{team_id}/notes/{note_id}` | Delete note |

## Authentication

Include the JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

Tokens expire after 30 minutes (configurable).

## Authorization Model

- **Team Admin**: Can manage team access, create/delete notes, manage members
- **Team Member**: Can create, read, update notes in the team
- **Non-members**: Cannot access team resources

## Pagination

List endpoints support cursor-based pagination:
```
GET /v1/teams/{team_id}/notes?limit=20&cursor=<cursor>
```

Response includes `next_cursor` for the next page.

## Version Control

Notes use optimistic locking via `version` field:
- Include `version` in PATCH requests
- Returns `409 Conflict` if version is stale
- Version increments on each update

## Error Responses

All errors follow a consistent format:
```json
{
  "detail": "Error description"
}
```

Common status codes:
- `400` - Bad request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not found
- `409` - Conflict (version mismatch)
- `422` - Validation error

## Development

### Local Development (without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://omninote:omninote@localhost:5432/omninote
export SECRET_KEY=dev-secret

# Run migrations
alembic upgrade head

# Seed data
python -m app.cli.seed

# Run server
uvicorn app.main:app --reload
```

### Run Migrations
```bash
# Generate new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Project Structure
```
app/
├── api/           # API routes
│   ├── auth.py    # Authentication endpoints
│   ├── teams.py   # Team endpoints
│   ├── notes.py   # Note endpoints
│   └── deps.py    # FastAPI dependencies
├── core/
│   └── config.py  # Configuration
├── db/
│   └── session.py # Database session
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic schemas
├── services/      # Business logic
│   ├── auth.py    # JWT, password hashing
│   ├── db_service.py # Database operations
│   └── policy.py  # Authorization policy
└── cli/
    └── seed.py    # Seed command
```

## Known Limitations

- Short-lived JWT tokens are not immediately revocable
- No password reset flow
- No email verification
- No rich text, attachments, or search (planned for future phases)
- WebSocket collaboration not yet implemented (Phase 3)

## License

MIT