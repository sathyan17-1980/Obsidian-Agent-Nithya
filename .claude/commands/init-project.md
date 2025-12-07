Initialize and validate the Obsidian-Agent-Nithya project from scratch.

This command provides step-by-step instructions for setting up the development environment, configuring services, and running comprehensive validation.

---

## Prerequisites Check

First, verify you have the required tools installed:

```bash
# Check Python version (requires 3.12+)
python3 --version

# Check uv installation
uv --version

# Check Docker
docker --version
docker-compose --version

# Check Git
git --version
```

**Expected:** All commands should return version numbers. If any are missing, install them first.

---

## Phase 1: Project Setup

### 1. Clone/Navigate to Project

```bash
cd /home/user/Obsidian-Agent-Nithya
```

### 2. Install Dependencies

```bash
uv sync
```

**Expected:** Dependencies installed successfully from `pyproject.toml`

### 3. Create Environment File

```bash
cp .env.example .env
```

**Expected:** `.env` file created with default configuration

**Optional:** Edit `.env` if you need custom database credentials or port changes:

```bash
# View current configuration
cat .env | grep -E "(DATABASE_URL|PORT|APP_NAME)"
```

---

## Phase 2: Database Setup

### 4. Start PostgreSQL Container

```bash
docker-compose up -d db
```

**Expected:** PostgreSQL container starts on port 5433

### 5. Wait for Database Ready

```bash
sleep 5
```

### 6. Verify Database Health

```bash
docker-compose ps
```

**Expected:** `db` service shows "Up (healthy)"

```bash
docker-compose exec db pg_isready -U postgres
```

**Expected:** "accepting connections"

### 7. Run Database Migrations

```bash
uv run alembic upgrade head
```

**Expected:** "Running upgrade -> e4a05b88d90b, initial"

### 8. Verify Migration Status

```bash
uv run alembic current
```

**Expected:** Shows current revision (e4a05b88d90b)

---

## Phase 3: Validation Suite

### 9. Run Test Suite

```bash
uv run pytest -v
```

**Expected:** All 34 tests pass, execution time < 1 second

### 10. Type Checking - MyPy

```bash
uv run mypy app/
```

**Expected:** "Success: no issues found in X source files"

### 11. Type Checking - Pyright

```bash
uv run pyright app/
```

**Expected:** "0 errors, 0 warnings, 0 informations"

### 12. Linting Check

```bash
uv run ruff check .
```

**Expected:** "All checks passed!" or no output (success)

### 13. Code Formatting

```bash
uv run ruff format .
```

**Expected:** Files formatted (or "X files left unchanged")

---

## Phase 4: Local Server Test

### 14. Start Development Server

```bash
uv run uvicorn app.main:app --reload --port 8123
```

**Expected:** Server starts with message "Application startup complete"

**Keep this running and open a NEW terminal for the following tests:**

### 15. Test Root Endpoint

```bash
curl -s http://localhost:8123/ | python3 -m json.tool
```

**Expected:** JSON response with app name, version, and documentation links

### 16. Test Health Endpoints

```bash
# Basic health check
curl -s http://localhost:8123/health

# Database health check
curl -s http://localhost:8123/health/db

# Readiness check
curl -s http://localhost:8123/health/ready
```

**Expected:** All return JSON with `"status": "healthy"`

### 17. Test Headers

```bash
curl -s -i http://localhost:8123/ | head -10
```

**Expected:** Response includes `x-request-id` header and `HTTP/1.1 200 OK`

### 18. Access Swagger UI

```bash
# In browser, visit:
http://localhost:8123/docs
```

**Expected:** Interactive API documentation loads

### 19. Stop Development Server

Press `Ctrl+C` in the terminal running uvicorn

---

## Phase 5: Docker Deployment Test

### 20. Build and Start All Services

```bash
docker-compose up -d --build
```

**Expected:** Both `db` and `app` containers build and start successfully

### 21. Wait for Startup

```bash
sleep 5
```

### 22. Verify Container Status

```bash
docker-compose ps
```

**Expected:** Both containers show "Up"

### 23. Test Docker Endpoints

```bash
# Root endpoint
curl -s http://localhost:8123/ | python3 -m json.tool

# Health check
curl -s http://localhost:8123/health

# Database health
curl -s http://localhost:8123/health/db
```

**Expected:** Same responses as local server tests

### 24. Check Structured Logs

```bash
docker-compose logs app | tail -20
```

**Expected:** JSON-formatted logs with `request_id`, structured events

### 25. View Live Logs (Optional)

```bash
docker-compose logs -f app
```

**Expected:** Real-time log stream (press `Ctrl+C` to stop)

### 26. Stop Docker Services

```bash
docker-compose down
```

**Expected:** Containers stopped and removed (volumes persist)

---

## Phase 6: Database Inspection (Optional)

### 27. Start Services Again

```bash
docker-compose up -d
```

### 28. Connect to PostgreSQL

```bash
docker-compose exec db psql -U postgres -d obsidian_db
```

**Inside psql, run:**

```sql
-- List all tables
\dt

-- Describe alembic version table
\d alembic_version

-- Check migration version
SELECT * FROM alembic_version;

-- Quit
\q
```

### 29. Create Database Backup (Optional)

```bash
docker-compose exec db pg_dump -U postgres obsidian_db > backup_$(date +%Y%m%d).sql
```

**Expected:** Backup file created with timestamp

---

## Phase 7: Git Status Check

### 30. Check Repository Status

```bash
git status
```

**Expected:** Shows current branch and any uncommitted changes

### 31. View Commit History

```bash
git log --oneline --graph --all
```

**Expected:** Shows commit history tree

### 32. Check Current Branch

```bash
git branch
```

**Expected:** Shows current branch (likely `claude/nithya-ai-agent-continue-*`)

---

## Quick Validation Checklist

Run this sequence for a fast health check:

```bash
# 1. Check services
docker-compose ps

# 2. Run tests
uv run pytest -v

# 3. Type check
uv run mypy app/ && uv run pyright app/

# 4. Lint check
uv run ruff check .

# 5. Test API
curl -s http://localhost:8123/health/db | python3 -m json.tool
```

**All commands should succeed with no errors.**

---

## Troubleshooting

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db | tail -50
```

### Port Conflicts

```bash
# Check what's using port 5433 (database)
lsof -i :5433

# Check what's using port 8123 (API)
lsof -i :8123

# Kill processes if needed
lsof -ti:8123 | xargs kill -9
```

### Migration Errors

```bash
# Check current migration status
uv run alembic current

# View migration history
uv run alembic history

# Rollback one migration
uv run alembic downgrade -1

# Re-apply migrations
uv run alembic upgrade head
```

### Dependency Issues

```bash
# Reinstall all dependencies
uv sync --reinstall

# Clear cache and reinstall
rm -rf .venv
uv sync
```

### Docker Issues

```bash
# Remove all containers and volumes (CAREFUL - deletes data)
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build --force-recreate
```

---

## Success Criteria

✅ **All tests pass** (34 tests in < 1 second)
✅ **Type checking passes** (MyPy and Pyright report 0 errors)
✅ **Linting passes** (Ruff check shows no issues)
✅ **Database connected** (PostgreSQL healthy on port 5433)
✅ **Migrations applied** (Alembic shows current revision)
✅ **API responds** (Health endpoints return 200 OK)
✅ **Docker works** (Both containers running, logs show structured JSON)
✅ **Documentation accessible** (Swagger UI loads at /docs)

---

## Next Steps

After successful initialization:

1. **Start Development:**
   ```bash
   uv run uvicorn app.main:app --reload --port 8123
   ```

2. **Implement Features:** Create new feature slices in `app/features/`

3. **Run Tests Continuously:**
   ```bash
   uv run pytest -v --watch
   ```

4. **Use Slash Commands:**
   - `/commit` - Create atomic commits
   - `/validate` - Run full validation suite
   - `/check-ignore-comments` - Analyze type suppressions

5. **Access Documentation:**
   - Read `CLAUDE.md` for development guidelines
   - Read `PRD.md` for project requirements
   - Read `mvp-tool-designs.md` for tool specifications

---

**Estimated Time:** 5-10 minutes for full initialization and validation

**Last Updated:** 2025-01-29
