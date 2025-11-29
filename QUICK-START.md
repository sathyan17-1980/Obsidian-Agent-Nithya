# Quick Start Guide - Nithya Obsidian AI Agent

Get up and running in 5 minutes!

## Prerequisites

- Python 3.12+
- Docker (for PostgreSQL)
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Installation

```bash
# 1. Navigate to project directory
cd /home/user/Obsidian-Agent-Nithya

# 2. Install dependencies
uv sync

# 3. Start PostgreSQL
docker-compose up -d

# 4. Create .env file (update with your API key)
cp .env.example .env
# Edit .env and set:
# - ANTHROPIC_API_KEY=your_key_here
# - VAULT_PATH=/tmp/test-vault (or your vault path)

# 5. Run migrations
uv run alembic upgrade head

# 6. Start the server
uv run uvicorn app.main:app --reload --port 8123
```

## First Test

Open another terminal and try:

```bash
# Health check
curl http://localhost:8123/agent/health

# Chat with the agent
curl -X POST http://localhost:8123/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all notes in my vault"
  }'
```

## Using the API

### Search for Notes

```bash
curl -X POST http://localhost:8123/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Search for notes about FastAPI"
  }'
```

### Create a Note

```bash
curl -X POST http://localhost:8123/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a new note called Meeting Notes with content: Discussed AI agent implementation"
  }'
```

### Get Daily Note

```bash
curl -X POST http://localhost:8123/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Get today'\''s daily note"
  }'
```

## Interactive API Docs

Once the server is running, visit:

- **Swagger UI:** http://localhost:8123/docs
- **ReDoc:** http://localhost:8123/redoc

## Test Vault

A test vault is created at `/tmp/test-vault` with sample notes. Use this for initial testing.

To use your own Obsidian vault, update `VAULT_PATH` in `.env` to point to your vault directory.

## Common Issues

### "Vault path does not exist"

Make sure `VAULT_PATH` in `.env` points to a valid directory.

### "Agent interaction failed"

Check that `ANTHROPIC_API_KEY` is set correctly in `.env`.

### Database connection error

Ensure PostgreSQL is running: `docker-compose up -d`

## Next Steps

1. Read `MVP-IMPLEMENTATION-SUMMARY.md` for detailed information
2. Check `mvp-tool-designs.md` for tool specifications
3. Review `CLAUDE.md` for development guidelines
4. Explore the API at http://localhost:8123/docs

## Support

For issues or questions, check the project documentation or create an issue on GitHub.

Happy coding! 🚀
