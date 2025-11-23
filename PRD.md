# Product Requirements Document: Nithya - Obsidian AI Agent

**Version:** 1.0
**Last Updated:** 2025-01-23
**Status:** Ready for Development

---

## Executive Summary

**Nithya** is an AI-powered agent that enables natural language interaction with Obsidian vaults. Built with FastAPI and Pydantic AI, Nithya provides a conversational interface for vault management, eliminating manual note organization and enabling semantic discovery of knowledge.

**Key Value Proposition:**
- Interact with your Obsidian vault using plain English instead of manual searching and organizing
- Intelligent vault operations powered by LLMs with tool-calling capabilities
- Fast, cost-efficient, and runs locally with Docker

**Core Capabilities (MVP):**
- Natural language search and discovery across notes
- Create, read, update, and manage notes conversationally
- Bulk operations for vault organization (tag management, folder organization)
- Support for multiple LLM providers (Anthropic Claude, OpenAI, local models)

---

## Mission & Vision

### Mission
Eliminate the friction of manual vault management by enabling users to interact with their Obsidian knowledge base through natural, conversational AI.

### Vision
Transform Obsidian from a passive note storage system into an intelligent, conversational knowledge partner that understands context, discovers connections, and proactively assists with information management.

### User Story
> "As an Obsidian vault user, I want to interact with my vault using natural language so that I can easily manage my notes and tasks without manual searching, tagging, and organizing."

---

## Target Users

### Primary User
**Personal use** - Individual knowledge worker managing personal Obsidian vault

**User Profile:**
- Active Obsidian user with 100+ notes
- Comfortable with technical tools (can run Docker, configure .env files)
- Cost-conscious (prefers local models or efficient API usage)
- Values natural language interaction over manual organization

### Use Cases
1. **Daily Knowledge Work** - "Find my notes about FastAPI and create a summary"
2. **Vault Organization** - "Tag all my draft notes with #review and move them to Archive"
3. **Discovery** - "What notes are related to my API design doc?"
4. **Quick Capture** - "Create a daily note and add these meeting takeaways"

---

## Problem Statement

### Current Pain Points
1. **Manual search is limited** - Keyword search misses conceptual matches
2. **Organization overhead** - Manual tagging, linking, and folder management is time-consuming
3. **Discovery friction** - Hard to find related notes or see knowledge connections
4. **Repetitive operations** - Bulk tagging, moving, and organizing requires tedious manual work
5. **Context switching** - Switching between writing, searching, and organizing breaks flow

### Impact
- **Time wasted** on manual vault maintenance instead of knowledge work
- **Knowledge silos** - Related notes remain disconnected due to manual linking overhead
- **Cognitive load** - Mental energy spent on organization instead of creative thinking

---

## Solution Overview

**Nithya** is a Dockerized FastAPI backend that exposes an OpenAI-compatible API endpoint, enabling the Copilot for Obsidian plugin to interact with an AI agent that has direct vault access through volume mounting.

### Architecture at a Glance

```
┌─────────────────────────────────────────────┐
│  Obsidian Desktop App                       │
│  ┌───────────────────────────────────────┐  │
│  │ Copilot Plugin (Frontend)             │  │
│  │ - Chat UI                             │  │
│  │ - Conversation history (client-side)  │  │
│  │ - Custom endpoint config              │  │
│  └───────────────────────────────────────┘  │
└──────────────────┬──────────────────────────┘
                   │ HTTP POST /v1/chat/completions
                   │ (OpenAI-compatible API)
                   ▼
┌─────────────────────────────────────────────┐
│  Docker Container: nithya-agent             │
│  ┌───────────────────────────────────────┐  │
│  │ FastAPI Backend                       │  │
│  │ ┌─────────────────────────────────┐   │  │
│  │ │ Pydantic AI Agent (Nithya)      │   │  │
│  │ │ - LLM provider abstraction      │   │  │
│  │ │ - 3 core tools                  │   │  │
│  │ │ - Stateless processing          │   │  │
│  │ └─────────────────────────────────┘   │  │
│  └───────────────────────────────────────┘  │
│                   │                          │
│  Volume Mount: /vault (read-write)          │
└───────────────────┼──────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│  Host Filesystem                            │
│  ${OBSIDIAN_VAULT_PATH}                     │
│  - Markdown files                           │
│  - YAML frontmatter                         │
│  - .obsidian/ config                        │
└─────────────────────────────────────────────┘
```

### How It Works
1. User types natural language query in Copilot plugin chat interface
2. Plugin sends request to FastAPI endpoint with conversation history
3. Nithya agent processes request, calls appropriate tools
4. Tools operate directly on vault files via volume mount
5. Agent returns response, plugin displays to user
6. Changes are immediately visible in both Obsidian and future agent operations

---

## MVP Scope

### In Scope (MVP)

#### **Core Agent: Nithya**
**Powered by:** Pydantic AI with multi-provider support
- Anthropic Claude (Claude Sonnet 4)
- OpenAI (GPT-4, GPT-3.5)
- Local models via Ollama

#### **Tool 1: `obsidian_query_vault`**
**Discovery and search operations**
- `search` - Full-text search with tag/folder filters
- `list` - List notes by folder or tag
- `find_related` - Discover connected notes via backlinks and shared tags

#### **Tool 2: `obsidian_manage_notes`**
**Individual note CRUD operations**
- `create` - Create notes with frontmatter (auto-creates folders)
- `read` - Read note content
- `update` - Replace or append to notes
- `delete` - Delete notes (with confirmation)
- `get_daily_note` - Get or create daily notes
- `manage_tags` - Add/remove tags from frontmatter

#### **Tool 3: `obsidian_manage_vault`**
**Vault organization and bulk operations**
- `create_folder` - Create folder hierarchies
- `list_folders` - List all folders with note counts
- `bulk_tag` - Add/remove tags from multiple notes
- `bulk_move` - Move multiple notes to different folder
- `bulk_delete` - Delete multiple notes (with confirmation)

#### **Frontend Integration**
- Copilot for Obsidian plugin configured with custom endpoint
- OpenAI-compatible API endpoint (`/v1/chat/completions`)
- Client-side conversation history management

#### **Deployment**
- Docker container with volume mounting
- Environment-based configuration (.env)
- Support for multiple vault paths via configuration

#### **Technical Features**
- Response format control (detailed vs concise) for token efficiency
- Dry-run pattern for safe bulk operations
- Instructive error messages that teach correct usage
- Auto-folder creation on note creation
- Bulk operations with internal search (offload from agent)

### Out of Scope (MVP2)

**Advanced Features (Phase 2):**
- Semantic search with vector embeddings
- Task management (TODO parsing and tracking)
- Template system integration
- MOC (Map of Content) auto-generation
- Graph analytics and visualization
- Broken link detection
- Real-time sync notifications
- Multi-user support
- Cloud deployment
- Web interface
- Mobile app integration

**Integrations (Phase 2):**
- Dataview plugin integration
- Templater plugin integration
- Calendar plugin integration
- External tool webhooks

---

## Core Patterns & Principles

### Design Patterns

#### **1. Vertical Slice Architecture (VSA)**
```
app/
├── core/           # Agent initialization, config, dependencies
├── shared/         # Vault utilities, schemas, exceptions
└── features/       # Each tool as a complete feature slice
    ├── search/     # obsidian_query_vault
    ├── notes/      # obsidian_manage_notes
    └── vault/      # obsidian_manage_vault
```

#### **2. Anthropic Tool Design Principles**
- **Consolidation over fragmentation** - Group frequently-chained operations
- **Token efficiency** - `response_format` parameter (3-5x token difference)
- **Instructive errors** - Errors teach agents better strategies
- **Semantic clarity** - Explicit parameter names, comprehensive descriptions
- **Offload computation** - Tools handle multi-step workflows (e.g., bulk ops include search)

#### **3. Pydantic AI Agent Pattern**
- **Single agent** with multiple tools (not multi-agent)
- **Dependency injection** via `RunContext[VaultDeps]`
- **Type-safe** tool definitions with automatic schema generation
- **Stateless agent** - conversation history managed client-side

#### **4. FastAPI REST Pattern**
- OpenAI-compatible endpoint structure
- Async request handling
- CORS configuration for Obsidian plugin
- Environment-based configuration

### Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| Package Management | UV (Astral) | Fast, modern Python package/venv management |
| Backend Framework | FastAPI | High-performance async API framework |
| AI Agent Framework | Pydantic AI | Type-safe agent with tool calling |
| LLM Providers | Anthropic, OpenAI, Ollama | Multi-provider support for cost optimization |
| Vault Operations | obsidiantools, custom parsers | Markdown parsing, metadata extraction |
| Deployment | Docker | Containerization with volume mounting |
| Frontend | Copilot for Obsidian | Chat interface in Obsidian |

---

## Technical Architecture

### Deployment Model

**Docker Container with Volume Mounting:**
```bash
# Configuration in .env
OBSIDIAN_VAULT_PATH=/path/to/your/vault

# Docker run command
docker run \
  -v ${OBSIDIAN_VAULT_PATH}:/vault:rw \
  -e OBSIDIAN_VAULT_PATH=/vault \
  -p 8000:8000 \
  nithya-agent
```

**Volume Mounting Strategy:**
- Host vault directory mounted as `/vault` in container
- Read-write (`:rw`) permissions for bidirectional sync
- Container sandboxed to only access vault directory
- Real-time changes visible to both Obsidian and Nithya

**Security Benefits:**
- Container cannot access host filesystem outside vault
- Vault path configurable per deployment
- No persistent state in container (stateless)

### Configuration Pattern

**Environment Variables (.env):**
```bash
# Vault Configuration
OBSIDIAN_VAULT_PATH=/vault  # Inside container (mapped from host)

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=app://obsidian.md

# LLM Provider (choose one or configure multiple)
AI_PROVIDER=anthropic  # anthropic | openai | ollama
AI_MODEL=claude-sonnet-4-0

# API Keys (only needed for cloud providers)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Local Model Configuration (if using Ollama)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama2
```

**Multiple Vault Support:**
Users can switch vaults by:
1. Stopping container
2. Updating `OBSIDIAN_VAULT_PATH` in .env
3. Restarting container

Or run multiple containers on different ports for simultaneous multi-vault access.

### API Contract

**Endpoint:** `POST /v1/chat/completions`

**Request (OpenAI-compatible):**
```json
{
  "model": "nithya",
  "messages": [
    {"role": "user", "content": "Find notes about FastAPI"},
    {"role": "assistant", "content": "Found 5 notes..."},
    {"role": "user", "content": "Create a summary note"}
  ],
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "nithya",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Created note 'FastAPI Summary' at Projects/FastAPI Summary.md"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 25,
    "total_tokens": 175
  }
}
```

### State Management

**Stateless Backend:**
- No session storage in FastAPI
- No conversation history persistence
- Each request is independent

**Client-Side History (Copilot Plugin):**
- Plugin maintains conversation context
- Sends full message history with each request
- Decides what context to include (cost control)

**Benefits:**
- Simpler backend architecture
- No state cleanup required
- Lower cost (no cumulative server-side context)
- Standard OpenAI-compatible pattern

---

## Success Criteria

### Functional Requirements
- ✅ All 3 tools implemented with all operations functional
- ✅ Copilot plugin successfully connects to FastAPI endpoint
- ✅ Natural language queries map to correct tool calls
- ✅ Changes to vault visible immediately in Obsidian
- ✅ Support for multiple LLM providers (Anthropic, OpenAI, Ollama)
- ✅ Docker deployment works with volume mounting
- ✅ Multiple vault support via configuration

### Performance Requirements
- ✅ Single note operations: <100ms
- ✅ Search on 1,000 notes: <1s
- ✅ Bulk operations preview: <2s
- ✅ Complex queries acceptable delay (5-10s)
- ✅ Response format token difference: 3-5x measured improvement

### Quality Requirements
- ✅ Instructive error messages guide correct usage
- ✅ No false positives on destructive operations (delete requires confirmation)
- ✅ Dry-run pattern prevents accidental bulk changes
- ✅ Auto-folder creation works seamlessly
- ✅ Basic console logging for debugging

### User Experience Requirements
- ✅ Conversational queries feel natural
- ✅ Agent chooses appropriate response_format automatically
- ✅ Bulk operations preview before execution
- ✅ Clear confirmations for all modifications
- ✅ Error messages explain what went wrong and how to fix

### Cost Efficiency Requirements
- ✅ Response format optimization reduces token usage (detailed vs concise)
- ✅ Support for local models (Ollama) for zero API cost
- ✅ Efficient tool descriptions minimize context overhead
- ✅ Client-side history allows selective context inclusion

---

## Non-Goals (Explicit)

### Not in MVP
- ❌ Semantic search with embeddings (Phase 2)
- ❌ Task management and TODO parsing (Phase 2)
- ❌ Template system integration (Phase 2)
- ❌ MOC auto-generation (Phase 2)
- ❌ Graph visualization (Phase 2)
- ❌ Multi-user support (Phase 2)
- ❌ Cloud deployment (Phase 2)
- ❌ Web interface (Phase 2)
- ❌ Mobile app (Phase 2)
- ❌ Real-time collaboration (out of scope)
- ❌ Version control integration (out of scope)
- ❌ Plugin development (using existing Copilot plugin)

### Assumptions & Constraints
- Single user (personal use)
- Standard Obsidian vault structure (no custom plugins required)
- User has Docker installed and configured
- User comfortable with .env configuration
- Obsidian desktop app (not mobile)
- Copilot plugin installed and configured

---

## Development Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Core infrastructure and first tool

**Deliverables:**
- ✅ Project scaffold with UV package management
- ✅ Docker container with volume mounting
- ✅ FastAPI OpenAI-compatible endpoint
- ✅ Pydantic AI agent initialization
- ✅ VaultDeps dependency injection
- ✅ `obsidian_query_vault` tool fully implemented
- ✅ Basic console logging
- ✅ .env configuration working

**Success Metric:** Can search vault via natural language query through Copilot plugin

### Phase 2: Note Management (Week 2-3)
**Goal:** Complete CRUD operations

**Deliverables:**
- ✅ `obsidian_manage_notes` tool fully implemented
- ✅ All operations: create, read, update, delete, get_daily_note, manage_tags
- ✅ Auto-folder creation on note creation
- ✅ Instructive error handling
- ✅ Response format control implemented

**Success Metric:** Can perform full note lifecycle via conversation

### Phase 3: Vault Organization (Week 3-4)
**Goal:** Bulk operations and vault structure

**Deliverables:**
- ✅ `obsidian_manage_vault` tool fully implemented
- ✅ Folder operations (create, list)
- ✅ Bulk operations with internal search (tag, move, delete)
- ✅ Dry-run pattern for safety
- ✅ Confirmation requirements for destructive operations

**Success Metric:** Can organize vault at scale via bulk operations

### Phase 4: Multi-Provider & Polish (Week 4)
**Goal:** Production readiness

**Deliverables:**
- ✅ Multiple LLM provider support (Anthropic, OpenAI, Ollama)
- ✅ Provider switching via configuration
- ✅ Token usage optimization verified
- ✅ Error handling comprehensive
- ✅ Documentation complete (README, setup guide)
- ✅ Example workflows tested

**Success Metric:** MVP works end-to-end with all providers, cost-efficient

---

## Technical Constraints

### Cost Optimization
- **Requirement:** Minimize API token usage
- **Solutions:**
  - `response_format` parameter (3-5x token reduction)
  - Support for local models (Ollama) - zero cost
  - Efficient tool descriptions
  - Client-side history management (selective context)
  - Concise default responses

### Latency Expectations
- **Simple queries:** <2s acceptable
- **Complex queries:** 5-10s acceptable
- **Bulk operations:** Preview <2s, execution may take longer
- **No real-time requirement** - thoughtful responses valued over speed

### Security Model
**MVP Simplicity:**
- API keys in .env (not exposed externally)
- Container sandboxing (vault directory only)
- No user authentication (single user, localhost)
- No network exposure (local only)

**Phase 2 Considerations:**
- JWT authentication for multi-user
- HTTPS for cloud deployment
- API key rotation
- Rate limiting

### Platform Support
- **Docker required** - primary deployment method
- **Host OS:** Linux, macOS, Windows (via Docker)
- **Obsidian:** Desktop app (v1.0+)
- **Python:** 3.11+ (managed by Docker)

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Vault corruption from agent errors** | High | Low | Dry-run pattern, confirmation for destructive ops, comprehensive testing |
| **High API costs** | Medium | Medium | Local model support, token optimization, response format control |
| **LLM hallucination (wrong tool calls)** | Medium | Medium | Excellent tool descriptions, evaluation-driven optimization, instructive errors |
| **Performance degradation on large vaults** | Medium | Low | Limit parameters, pagination, indexed search (Phase 2) |
| **Docker setup complexity** | Low | Medium | Clear documentation, example docker-compose, troubleshooting guide |
| **Copilot plugin compatibility issues** | Medium | Low | OpenAI-compatible standard, version pinning, testing |
| **Concurrent access conflicts** | Low | Low | File locking, atomic operations, clear error messages |

---

## Monitoring & Observability (MVP)

### Logging Strategy
**Basic console logging:**
- Request/response logging (FastAPI access logs)
- Tool call logging (which tools called, parameters)
- Error logging (stack traces, error context)
- Performance logging (response times)

**Log Format:**
```
[2025-01-23 10:30:45] INFO: Request to /v1/chat/completions
[2025-01-23 10:30:45] INFO: Tool called: obsidian_query_vault(operation=search, query="FastAPI")
[2025-01-23 10:30:46] INFO: Response: Found 5 notes (350 tokens)
```

### Metrics (Phase 2)
- Token usage per request
- Tool call frequency distribution
- Response time percentiles
- Error rates by tool
- Cost tracking (API spend)

---

## Dependencies

### Core Dependencies
```toml
[project]
name = "nithya-obsidian-agent"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "pydantic-ai>=0.1.0",
    "pydantic-settings>=2.1.0",
    "obsidiantools>=0.10.0",
    "httpx>=0.26.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]
```

### External Services
- **Anthropic API** (optional - for Claude models)
- **OpenAI API** (optional - for GPT models)
- **Ollama** (optional - for local models)

---

## Documentation Requirements

### MVP Documentation
1. **README.md** - Quick start guide
2. **SETUP.md** - Detailed installation and configuration
3. **USAGE.md** - Example queries and workflows
4. **TROUBLESHOOTING.md** - Common issues and solutions
5. **API.md** - API endpoint documentation
6. **Code comments** - Inline documentation for complex logic

### User Guides
- Docker setup walkthrough
- Copilot plugin configuration
- LLM provider setup (Anthropic, OpenAI, Ollama)
- Multi-vault configuration
- Example conversation flows

---

## Appendix

### Glossary
- **Nithya:** The AI agent that manages Obsidian vaults
- **Vault:** An Obsidian vault (directory of markdown files)
- **Tool:** A function that the agent can call (e.g., search, create note)
- **Frontmatter:** YAML metadata at the top of markdown files
- **Wikilinks:** Obsidian's internal linking format `[[Note Title]]`
- **MOC:** Map of Content - index note linking to related notes
- **VSA:** Vertical Slice Architecture - organizing code by feature

### References
- **Tool Design:** See `mvp-tool-designs.md`
- **Anthropic Guide:** https://www.anthropic.com/engineering/writing-tools-for-agents
- **Pydantic AI:** https://ai.pydantic.dev/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Copilot Plugin:** https://www.obsidiancopilot.com/en
- **Obsidian API:** https://docs.obsidian.md/

---

**Document Owner:** User
**Status:** Approved for Development
**Next Steps:** Begin Phase 1 - Foundation implementation
