# Tradexia ADK — Architecture & Agent Reference

## Overview

Tradexia is a **Google ADK multi-agent system** for analyzing Indian stock markets. A master Orchestrator delegates work to specialist sub-agents, coordinates parallel/sequential execution, and synthesizes results into actionable recommendations.

**Runtime:** Python 3.10+ · **Models:** Gemini 2.5 Flash family · **Framework:** Google ADK (Agent Development Kit)

---

## Folder Structure

```
adk/
├── src/
│   ├── agents/          # LlmAgent definitions (one file per agent)
│   ├── core/            # Framework internals (executor, registry, runner, factory)
│   ├── config/          # Pydantic settings loaded from .env
│   ├── cache/           # Optional Redis cache client
│   └── tools/           # Shared HTTP client for backend API
├── tests/               # Unit tests (pytest)
├── ARCHITECTURE.md      # This file
├── README.md
├── adk.yaml             # ADK CLI metadata / default model config
├── pyproject.toml       # Project metadata & dev tooling
└── requirements.txt     # Pip dependencies
```

---

## Folder Details

### `src/agents/`
Contains all five `LlmAgent` definitions. Each file is self-contained: it declares the agent's model, system instructions, tools, and optional `output_key` for writing results into shared session state.

| File | Agent | Role |
|---|---|---|
| `orchestrator.py` | `orchestrator_agent` | Master router & coordinator |
| `news_agent.py` | `news_intelligence_agent` | News fetch & sentiment |
| `fundamental_agent.py` | `fundamental_analysis_agent` | Financial metrics & scraping |
| `index_agent.py` | `index_composition_agent` | Index composition & sector analysis |
| `synthesis_agent.py` | `synthesis_agent` | Final report synthesis |

### `src/core/`

| File | Purpose |
|---|---|
| `agents.py` | Factory functions: `create_llm_agent()`, `create_parallel_agent()`, `create_sequential_agent()` |
| `executor.py` | `AgentExecutor` — runs agents in `parallel` or `sequential` mode; caches wrapper agents to avoid ADK re-parenting errors |
| `registry.py` | Central dict-based registry; `register()`, `get()`, `get_multiple()`, `list_agents()` |
| `runner.py` | `MainRunner` — owns shared `InMemorySessionService`, `InMemoryArtifactService`, `InMemoryMemoryService`; vends `Runner` instances per agent |

### `src/config/`
`settings.py` — Pydantic `BaseSettings` that loads from `.env`:
- `GOOGLE_API_KEY`
- `AGENT_MODEL` (default: `gemini-2.0-flash-exp`)
- `BACKEND_API_URL` (default: `http://localhost:8000`)
- Redis host/port/db
- `LOG_LEVEL`

### `src/cache/`
`redis_client.py` — thin async Redis wrapper. All agents attempt a cache read before any network call and gracefully fall back if Redis is unavailable.

### `src/tools/`
`backend_client.py` — `httpx`-based async HTTP client for the Tradexia backend REST API. Used by agents that need live price data not available via scraping.

---

## Agents

### 1. Orchestrator Agent

| Property | Value |
|---|---|
| **File** | `src/agents/orchestrator.py` |
| **Name** | `orchestrator_agent` |
| **Model** | `gemini-2.5-flash` |
| **Output key** | — (returns final text directly to user) |

**Role:** Master coordinator. Receives user queries, decides which sub-agents to invoke and in what order, then delivers a unified response.

**Tools:**

| Tool | Description |
|---|---|
| `call_agents_parallel(agent_names, query)` | Runs the listed agents concurrently via `AgentExecutor`. Agents share the same session so their `output_key` values land in the same state dict. |
| `call_agents_sequential(agent_names, query)` | Runs the listed agents one-by-one in order, passing the same session so later agents can read earlier results. |

**Internals:**
- Uses `threading.local()` (`_session_context`) to maintain a single `session_id` across all tool calls within one user turn, even across parallel threads.
- Calls `reset_turn_session_id()` after each turn completes.

**Typical execution flow:**
```
User: "Analyze TCS"
  → call_agents_parallel(["news", "fundamental"], query)
      ├─ news_agent       → state["news_result"]
      └─ fundamental_agent → state["fundamental_result"]
  → call_agents_sequential(["synthesis"], query)
      └─ synthesis_agent  reads state["news_result"] + state["fundamental_result"]
                          → final report returned to user
```

---

### 2. News Intelligence Agent

| Property | Value |
|---|---|
| **File** | `src/agents/news_agent.py` |
| **Name** | `news_intelligence_agent` |
| **Model** | `gemini-2.5-flash-lite` |
| **Output key** | `news_result` |

**Role:** Fetches and interprets financial news and market sentiment for a given stock or index (Indian markets focus).

**Tools:**

| Tool | Description |
|---|---|
| `get_stock_news(symbol, limit)` | Fetches articles from Google News RSS feeds. Falls back to Redis cache if a prior result exists. |
| `analyze_sentiment(symbol)` | Placeholder — calls backend sentiment endpoint when available. |

**Data flow:** Result is auto-saved by ADK to `session.state["news_result"]` so the Synthesis agent can read it.

---

### 3. Fundamental Analysis Agent

| Property | Value |
|---|---|
| **File** | `src/agents/fundamental_agent.py` |
| **Name** | `fundamental_analysis_agent` |
| **Model** | `gemini-2.5-flash` |
| **Output key** | `fundamental_result` |

**Role:** Quantitative deep-dive into company financials — ratios, growth trends, balance sheet, cash flow, and strategic plans.

**Tools:**

| Tool | Description |
|---|---|
| `get_screener_data(symbol)` | Web-scrapes [screener.in](https://www.screener.in) for key ratios, quarterly results, P&L, balance sheet, and cash flow. |

**Data flow:** Result auto-saved to `session.state["fundamental_result"]`.

---

### 4. Index Composition Agent

| Property | Value |
|---|---|
| **File** | `src/agents/index_agent.py` |
| **Name** | `index_composition_agent` |
| **Model** | `gemini-2.5-flash` |
| **Output key** | — (not shared via session state) |

**Role:** Analyzes Indian index structure (NIFTY 50, Bank Nifty) — constituents, weightages, sector breakdown, top contributors/detractors, and concentration risk.

**Tools:**

| Tool | Description |
|---|---|
| `get_index_composition(index_name)` | Fetches constituent list and percentage weightages. |
| `analyze_index_performance(index_name)` | Returns top gainers and losers within the index. |
| `get_sector_analysis(index_name)` | Sector-wise performance and rotation signals. |

**Note:** Unlike news and fundamental agents this agent does not write to session state; its output is returned directly via the orchestrator's response.

---

### 5. Synthesis Agent

| Property | Value |
|---|---|
| **File** | `src/agents/synthesis_agent.py` |
| **Name** | `synthesis_agent` |
| **Model** | `gemini-2.5-flash` |
| **Output key** | — (final output, no downstream consumer) |

**Role:** "Senior analyst" that merges outputs from all parallel agents into one coherent, actionable report. Runs last, after parallel agents have populated session state.

**Tools:**

| Tool | Description |
|---|---|
| `synthesize_analysis(tool_context)` | Reads `tool_context.state["news_result"]` and `tool_context.state["fundamental_result"]`; correlates and weighs signals. ADK auto-injects `tool_context`. |
| `generate_report(symbol, tool_context)` | Formats the synthesized analysis into a structured report with ratings and recommendations. |

**Dependency:** Must run after News Agent and Fundamental Agent have written their `output_key` values to session state.

---

## Core Framework

### Execution Engine (`core/executor.py`)

`AgentExecutor` is the bridge between the Orchestrator's tool calls and the actual ADK runners.

**Key design decisions:**

1. **Wrapper agent caching** — ADK raises an error if the same `LlmAgent` instance is parented to two different wrapper agents. `AgentExecutor` caches `ParallelAgent`/`SequentialAgent` wrappers keyed by `"{mode}::{sorted agent names}"` so wrappers are reused rather than re-created.

2. **Session reuse** — The same `session_id` (provided by the orchestrator's thread-local) is passed to every `execute_agents()` call within a single user turn, so state written by parallel agents is visible to sequential agents.

3. **State injection** — `update_session_state()` appends a synthetic event to the ADK session to seed state from outside the agent graph.

### Registry (`core/registry.py`)

Flat key→agent dict. Agents register themselves at module import time. The executor calls `get_multiple(agent_names)` to resolve names before building wrapper agents.

### Shared Runner (`core/runner.py`)

`MainRunner` creates one set of in-memory services (session, artifact, memory) and vends `Runner` instances that all share them. This is what makes `session_id` work as a cross-agent namespace — every runner points at the same `InMemorySessionService`.

---

## Inter-Agent Communication Patterns

### Session State via `output_key`
ADK automatically writes an agent's final text response to `session.state[output_key]`. Downstream agents access it via `tool_context.state[key]`.

### Thread-Local Session ID
The Orchestrator uses `threading.local()` to hold one `session_id` per OS thread. Both `call_agents_parallel` and `call_agents_sequential` tools read from the same thread-local, so they always operate on the same session.

### Tool Context Injection
ADK detects any function parameter named `tool_context: ToolContext` and auto-injects the live context object. Tools read state with `tool_context.state.get(key)` and can write back with `tool_context.state[key] = value`.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API credential |
| `AGENT_MODEL` | `gemini-2.0-flash-exp` | Default model (overridden per-agent in code) |
| `BACKEND_API_URL` | `http://localhost:8000` | Tradexia backend REST API |
| `REDIS_HOST` | `localhost` | Redis cache host |
| `REDIS_PORT` | `6379` | Redis cache port |
| `REDIS_DB` | `0` | Redis database index |
| `LOG_LEVEL` | `INFO` | Loguru log level |

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `google-adk` | Agent orchestration framework (LlmAgent, Runner, ParallelAgent, etc.) |
| `google-genai` | Gemini model API client |
| `httpx` / `aiohttp` | Async HTTP for backend client and RSS fetching |
| `redis` | Optional cache client |
| `beautifulsoup4` | HTML scraping (screener.in) |
| `pydantic` | Settings validation |
| `loguru` | Structured logging |

---

## Running the System

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env        # fill in GOOGLE_API_KEY at minimum

# 4a. Run via ADK web UI (interactive)
adk web

# 4b. Run programmatically
python src/main.py
```

Redis and the backend API are optional — all agents degrade gracefully when they are unavailable.
