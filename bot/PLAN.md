# LMS Telegram Bot Development Plan

## Overview

This document outlines the development plan for building a Telegram bot that lets users interact with the LMS backend through chat. The bot supports slash commands like `/health` and `/labs`, and uses an LLM to understand plain language questions.

## Architecture

### Layered Design

The bot follows a **layered architecture** with clear separation of concerns:

1. **Transport Layer** (`bot.py`) — Handles Telegram API communication via aiogram
2. **Handler Layer** (`handlers/`) — Command logic as pure functions, testable without Telegram
3. **Service Layer** (`services/`) — External API clients (LMS backend, LLM)
4. **Configuration** (`config.py`) — Environment variable loading from `.env.bot.secret`

### Test Mode

The `--test` flag enables offline testing by calling handlers directly and printing responses to stdout. This allows development and verification without a Telegram connection or bot token.

## Task Breakdown

### Task 1: Plan and Scaffold (Current)

**Goal:** Establish project structure and testable handler architecture.

- Create `bot/` directory with entry point (`bot.py`)
- Implement `--test` mode for offline verification
- Separate handlers into `handlers/` module (no Telegram dependency)
- Add `config.py` for environment variable loading
- Document the approach in `PLAN.md`

**Acceptance:** All placeholder commands (`/start`, `/help`, `/health`, `/labs`, `/scores`) work in test mode.

### Task 2: Backend Integration

**Goal:** Connect handlers to the real LMS backend.

- Create `services/api_client.py` with Bearer token authentication
- Implement `/health` — calls `GET /health` on backend, reports up/down
- Implement `/labs` — calls `GET /items?type=lab`, formats response
- Implement `/scores <lab>` — calls `GET /analytics?lab=<lab>`, shows pass rates
- Add error handling — friendly messages when backend is unreachable

**Pattern:** API client reads `LMS_API_BASE_URL` and `LMS_API_KEY` from environment. All requests include `Authorization: Bearer <key>`.

### Task 3: Intent-Based Natural Language Routing

**Goal:** Enable plain text questions interpreted by an LLM.

- Create `services/llm_client.py` for LLM API communication
- Wrap backend endpoints as **LLM tools** with clear descriptions
- Implement intent router — LLM decides which tool to call based on user input
- Handle multi-step reasoning (e.g., "How am I doing?" → fetch all labs → fetch scores)

**Key Insight:** The LLM reads tool descriptions to decide which to call. Description quality matters more than prompt engineering. Don't use regex or keyword matching — let the LLM route.

### Task 4: Containerize and Deploy

**Goal:** Deploy the bot alongside the backend on the VM.

- Create `Dockerfile` for the bot
- Add bot service to `docker-compose.yml`
- Configure Docker networking (containers use service names, not `localhost`)
- Document deployment steps and troubleshooting

**Docker Networking:** Inside containers, `http://backend:42002` works, not `localhost:42002`.

## Testing Strategy

1. **Unit tests** — Test handlers in isolation (pytest)
2. **Test mode** — Manual verification via `--test` flag
3. **Integration tests** — Test with real backend (requires running backend)
4. **Live testing** — Deploy to VM and test in Telegram

## Git Workflow

For each task:

1. Create issue describing the work
2. Create branch: `task-N-short-description`
3. Implement, test, commit
4. Create PR with `Closes #...` in description
5. Partner review, then merge

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM picks wrong tool | Improve tool descriptions, not code-based routing |
| Backend unreachable | Graceful error messages, not crashes |
| Secrets committed | `.env.bot.secret` in `.gitignore`, use `.env.bot.example` |
| Docker networking issues | Use service names, test with `docker-compose exec` |

## Success Criteria

- User can check system health via `/health`
- User can browse labs via `/labs`
- User can get scores via `/scores lab-04`
- User can ask "what labs are available" in plain text
- Bot is deployed and running on the VM
