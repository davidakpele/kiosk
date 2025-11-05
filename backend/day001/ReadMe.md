# 📋 Medical Kiosk Project - Week 1 Commands Reference
## 🏗️ Project Setup & Environment

## Alembic Migrations
# Initialize Alembic
alembic init alembic

# Generate migration (after fixing database URL)
alembic revision --autogenerate -m "Create doctors table"

# Apply migration
alembic upgrade head

# Check migration status
alembic current

# View migration history
alembic history


## ACHEIVED 

## Available Endpoints

### Health & Info
- `GET /` - API information
- `GET /health` - Health check

### Doctors
- `GET /doctors/` - List all doctors (with optional filtering)
- `GET /doctors/{id}` - Get specific doctor by ID
- `GET /doctors/specialty/{specialty}` - Filter doctors by specialty

### Query Parameters
- `skip` - Number of records to skip (pagination)
- `limit` - Maximum number of records to return
- `specialty` - Filter by specialty
- `city` - Filter by city