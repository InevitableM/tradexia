# Tradexia ADK - Agent Layer

Google ADK-powered multi-agent system for analyzing Indian stock indices (Nifty50, Bank Nifty) and their constituent stocks.

## Architecture

This folder contains the **Agent Layer** with:
- Multi-agent system using Google ADK
- Specialized agents (News, Fundamental, Index, Synthesis)
- Redis cache client for ultra-fast data access
- Tools for API calls and analysis

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
copy .env.example .env
# Edit .env with your API keys
```

4. Run the orchestrator:
```bash
python -m src.main
```

## Project Structure

```
adk/
├── src/
│   ├── agents/          # Google ADK agents
│   ├── tools/           # Agent tools (API callers, analyzers)
│   ├── config/          # Configuration management
│   ├── cache/           # Redis cache client
│   └── main.py          # Entry point
├── tests/               # Unit tests
├── requirements.txt     # Dependencies
└── .env.example         # Environment template
```

## Agents

- **Orchestrator**: Routes queries and synthesizes responses
- **News Agent**: Analyzes news and sentiment
- **Fundamental Agent**: Evaluates financial metrics
- **Index Agent**: Analyzes index composition
- **Synthesis Agent**: Combines multi-agent insights
