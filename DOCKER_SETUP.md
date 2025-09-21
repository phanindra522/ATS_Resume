# Docker Installation and Local Testing Guide

## Prerequisites

### 1. Install Docker Desktop
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Install Docker Desktop for Windows
3. Start Docker Desktop and wait for it to fully initialize
4. Verify installation:
   ```bash
   docker --version
   docker compose --version
   ```

### 2. Environment Setup
1. Create a `.env` file in the root directory with your environment variables:
   ```bash
   # Copy from backend/.env and add any additional variables
   OPENAI_API_KEY=your-openai-api-key
   SECRET_KEY=your-secret-key-here
   ```

## Local Testing with Docker

### 1. Build and Start Services
```bash
# Build all services
docker compose build

# Start all services in background
docker compose up -d

# View logs
docker compose logs -f
```

### 2. Access the Application
- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Useful Docker Commands
```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs backend
docker compose logs frontend

# Restart a service
docker compose restart backend

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Rebuild specific service
docker compose build backend
docker compose up -d backend
```

### 4. Troubleshooting
```bash
# Check if ports are available
netstat -an | findstr :80
netstat -an | findstr :8000

# Free up ports if needed
docker compose down
taskkill /F /PID <process-id-using-port>

# View container details
docker ps -a
docker inspect <container-name>

# Access container shell
docker exec -it ats-backend bash
docker exec -it ats-frontend sh
```

## Production Considerations

### Database Migration
- The current setup uses SQLite for development
- For production, consider using PostgreSQL or MySQL
- Update the `DATABASE_URL` environment variable accordingly

### Security
- Use strong, unique values for `SECRET_KEY`
- Secure your OpenAI API key
- Consider using Docker secrets for sensitive data

### Monitoring
- Health checks are configured for both services
- Consider adding logging aggregation (ELK stack)
- Monitor resource usage and scaling needs