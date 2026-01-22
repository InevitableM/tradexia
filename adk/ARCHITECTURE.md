# Tradexia ADK - Multi-Agent System Architecture

## Agent2Agent (A2A) Protocol Implementation

This project implements a multi-agent system using Google's Agent2Agent (A2A) protocol for seamless agent communication.

## Architecture Overview

```
┌─────────────────────────────────────────┐
│      Orchestrator Agent (Master)        │
│  - Routes queries to specialized agents │
│  - Synthesizes multi-agent responses    │
│  - Maintains conversation context       │
└──────────────┬──────────────────────────┘
               │
               ├──────────────┬──────────────┬──────────────┐
               ↓              ↓              ↓              ↓
         ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
         │   News   │   │Fundamen- │   │  Index   │   │Synthesis │
         │  Agent   │   │tal Agent │   │  Agent   │   │  Agent   │
         └──────────┘   └──────────┘   └──────────┘   └──────────┘
              ↓              ↓              ↓              ↓
         News & Sen-    Financial      Index          Combined
         timent Data    Metrics &      Composition    Analysis
                        Growth         & Performance
```

## Agents

### 1. **Orchestrator Agent**
- **Role**: Master coordinator
- **Skills**: Route queries, orchestrate multi-agent analysis
- **Tools**: `route_to_agent`

### 2. **News Intelligence Agent**
- **Role**: News analysis and sentiment
- **Skills**: 
  - Analyze stock news
  - Sentiment analysis
- **Tools**:
  - `get_stock_news`: Fetch latest news
  - `analyze_sentiment`: Sentiment scoring

### 3. **Fundamental Analysis Agent**
- **Role**: Financial metrics and growth analysis
- **Skills**:
  - Financial metrics analysis (P/E, ROE, etc.)
  - Sales growth analysis
  - Strategic planning evaluation
- **Tools**:
  - `get_financial_metrics`
  - `analyze_growth_trends`
  - `evaluate_company_plans`

### 4. **Index Composition Agent**
- **Role**: Index structure and performance
- **Skills**:
  - Index composition analysis
  - Performance tracking
  - Sector-wise analysis
- **Tools**:
  - `get_index_composition`
  - `analyze_index_performance`
  - `get_sector_analysis`

### 5. **Synthesis Agent**
- **Role**: Multi-source intelligence synthesis
- **Skills**:
  - Combine insights from all agents
  - Generate comprehensive reports
- **Tools**:
  - `synthesize_analysis`
  - `generate_report`

## A2A Protocol Components

Each agent consists of:

1. **AgentCard**: Metadata describing agent capabilities
2. **LlmAgent**: Google ADK agent with model, tools, and instructions
3. **AgentExecutor**: Handles task execution using ADK Runner

## Communication Flow

```python
User Query → Orchestrator → Identify Intent
                ↓
         Route to Agent(s)
                ↓
    Agent 1 → Tool Call → Response
    Agent 2 → Tool Call → Response
    Agent 3 → Tool Call → Response
                ↓
         Synthesis Agent
                ↓
    Comprehensive Response
```

## Benefits of A2A Architecture

1. **Seamless Communication**: Agents communicate via standard protocol
2. **Modularity**: Easy to add/remove specialized agents
3. **Scalability**: Each agent can be deployed independently
4. **Fast**: In-memory session management + Redis caching
5. **Extensible**: Add new skills/tools without affecting other agents

## Data Flow

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       ↓
┌─────────────┐
│ Redis Cache │ ← Check cache first (ultra-fast)
└──────┬──────┘
       ↓ (cache miss)
┌─────────────┐
│  Backend    │ ← Fetch from APIs/Database
│    API      │
└──────┬──────┘
       ↓
┌─────────────┐
│   Agents    │ ← Process with AI
└──────┬──────┘
       ↓
┌─────────────┐
│  Response   │
└─────────────┘
```

## Next Steps

1. ✅ Set up A2A protocol infrastructure
2. ✅ Create specialized agents with skills
3. 🔄 Implement agent-to-agent messaging
4. ⏳ Build backend integration
5. ⏳ Set up Redis caching layer
6. ⏳ Deploy and test
