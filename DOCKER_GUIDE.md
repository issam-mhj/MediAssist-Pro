# MediAssist-Pro - Docker Setup Guide

## Prerequisites

1. **Docker Desktop** must be installed and running
   - Download: https://www.docker.com/products/docker-desktop/
   - Start Docker Desktop before running commands

## Quick Start

### 1. Start the application

```powershell
# Navigate to project directory
cd c:\Users\issam\OneDrive\Desktop\MediAssist-Pro

# Start Docker Desktop (if not running)
# Then build and start containers
docker-compose up -d --build
```

This will:
- Build the FastAPI backend image
- Start PostgreSQL database container
- Start FastAPI backend container
- Create the database tables automatically

### 2. Check if containers are running

```powershell
docker ps
```

You should see:
- `mediassist_backend` (port 8000)
- `mediassist_db` (port 5432)

### 3. View logs

```powershell
# All containers
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f db
```

### 4. Test the API

#### Option A: Run the test script

```powershell
# Install requests library first
pip install requests

# Run tests
python test_auth.py
```

#### Option B: Use Swagger UI

1. Open browser: http://localhost:8000/docs
2. You'll see the interactive API documentation
3. Try the endpoints:
   - POST /api/auth/register - Register a user
   - POST /api/auth/login - Get a token
   - Click "Authorize" button, enter credentials
   - GET /api/users/me - Get your profile

#### Option C: Manual cURL tests

```powershell
# 1. Register a user
curl -X POST "http://localhost:8000/api/auth/register" `
  -H "Content-Type: application/json" `
  -d '{\"username\": \"john_doe\", \"email\": \"john@example.com\", \"password\": \"SecurePass123!\"}'

# 2. Login
curl -X POST "http://localhost:8000/api/auth/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=john_doe&password=SecurePass123!"

# 3. Get profile (replace TOKEN with the actual token from step 2)
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -X GET "http://localhost:8000/api/users/me" `
  -H "Authorization: Bearer $TOKEN"
```

## Docker Commands

### Start containers

```powershell
docker-compose up -d
```

### Stop containers

```powershell
docker-compose down
```

### Stop and remove volumes (⚠️ deletes data)

```powershell
docker-compose down -v
```

### Restart a specific service

```powershell
docker-compose restart backend
docker-compose restart db
```

### Rebuild after code changes

```powershell
docker-compose up -d --build
```

### View container status

```powershell
docker-compose ps
```

### Execute commands in backend container

```powershell
# Open shell
docker exec -it mediassist_backend bash

# Run Python command
docker exec -it mediassist_backend python -c "print('Hello')"
```

### Execute commands in database

```powershell
# Connect to PostgreSQL
docker exec -it mediassist_db psql -U mediassist_user -d mediassist_db

# Inside psql:
\dt          # List tables
\d users     # Describe users table
SELECT * FROM users;
\q           # Quit
```

## Troubleshooting

### Docker Desktop not running

**Error**: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`

**Solution**: 
1. Start Docker Desktop application
2. Wait for it to fully start (icon in system tray should be solid)
3. Try the command again

### Port already in use

**Error**: `port is already allocated`

**Solution**:
```powershell
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Stop the process or change port in docker-compose.yml
```

### Backend container crashes

```powershell
# View logs
docker-compose logs backend

# Check for Python errors
docker-compose logs backend | Select-String -Pattern "Error"
```

### Database connection issues

```powershell
# Check if database is healthy
docker inspect mediassist_db | Select-String -Pattern "Health"

# Restart database
docker-compose restart db

# Wait a few seconds then restart backend
Start-Sleep -Seconds 5
docker-compose restart backend
```

### Database tables not created

```powershell
# Restart backend (tables are created on startup)
docker-compose restart backend

# Or recreate everything
docker-compose down -v
docker-compose up -d --build
```

## API Endpoints

### Health Check

```
GET http://localhost:8000/
GET http://localhost:8000/health
```

### Authentication

```
POST http://localhost:8000/api/auth/register
POST http://localhost:8000/api/auth/login
```

### Users

```
GET http://localhost:8000/api/users/me (requires authentication)
```

### API Documentation

```
http://localhost:8000/docs         # Swagger UI
http://localhost:8000/redoc        # ReDoc
http://localhost:8000/openapi.json # OpenAPI schema
```

## Environment Variables

Configured in `docker-compose.yml`:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token validity duration
- `APP_NAME`: Application name

## Volumes

- `postgres_data`: PostgreSQL database files (persisted)
- `chroma_data`: ChromaDB vector store (persisted)
- `./backend:/app`: Backend code (live reload)
- `./documents:/app/documents`: PDF manuals

## Network

Containers communicate on internal Docker network:
- Backend can access database at: `db:5432`
- Host can access:
  - Backend: `localhost:8000`
  - Database: `localhost:5432`

## Production Notes

Before deploying to production:

1. Change `SECRET_KEY` to a secure random value
2. Set `DEBUG=False`
3. Use proper HTTPS/TLS
4. Use managed PostgreSQL (not container)
5. Set up proper backups
6. Use environment-specific `.env` files
7. Remove volume mounts for code
8. Use production WSGI server (gunicorn)

## Useful Links

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

**Next Steps**: Once authentication is working, proceed to Phase 4 (RAG Pipeline) to implement document processing, embeddings, and question answering.
