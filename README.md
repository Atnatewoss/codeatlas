<div align="center">
  <h1>CodeAtlas</h1>
  <p>
    <a href="https://github.com/Atnatewoss/codeatlas/stargazers">
      <img src="https://shieldcn.dev/github/stars/Atnatewoss/codeatlas.svg" alt="GitHub stars" />
    </a>
    <a href="https://github.com/Atnatewoss/codeatlas/network/members">
      <img src="https://shieldcn.dev/github/forks/Atnatewoss/codeatlas.svg" alt="GitHub forks" />
    </a>
    <a href="https://github.com/Atnatewoss/codeatlas/issues">
      <img src="https://shieldcn.dev/github/issues/Atnatewoss/codeatlas.svg" alt="GitHub issues" />
    </a>
    <a href="https://github.com/Atnatewoss/codeatlas/blob/main/LICENSE">
      <img src="https://shieldcn.dev/github/license/Atnatewoss/codeatlas.svg" alt="License" />
    </a>
  </p>

  <p><strong>Deep Research & Architecture Intelligence for Complex Codebases</strong></p>
</div>

<br />

CodeAtlas autonomously analyzes any git repository using **Tree of Thought** reasoning over 5 parallel architectural perspectives, evaluates findings for contradictions, investigates low-confidence areas, and synthesizes a unified research report.

## Architecture

```
codeatlas/
├── apps/api/              # FastAPI server (thin orchestration)
├── packages/
│   ├── graphify/          # Code intelligence engine (Graphify wrapper, 36+ languages)
│   └── research/          # Tree of Thought reasoning engine
├── data/
│   └── graphify-cache/    # Generated graph data (gitignored)
└── docs/
```

## Tree of Thought Workflow

```
repo → build_knowledge_graph → 5 parallel branches → evaluate
  → [investigate → evaluate] × N → synthesize → report
```

### 5 Analysis Branches

| Branch      | Focus                                           |
|-------------|-------------------------------------------------|
| Structure   | Module layout, dependency graph, config files   |
| Runtime     | Entry points, execution flow, call graphs       |
| Design      | Abstractions, patterns, interfaces              |
| Onboarding  | Documentation, learning path, key files         |
| Risk        | Complexity hotspots, single points of failure   |

### Evaluation & Investigation Loop

Branches feed into an LLM-based evaluator that detects **contradictions** across perspectives. When contradictions or low-confidence findings exist, a ReAct investigation agent re-examines the codebase and the loop repeats (up to `MAX_INVESTIGATION_ROUNDS`). The loop is bounded to prevent runaway costs.

### Synthesis

A final LLM pass produces a unified report: summary, architecture overview, key insights, learning path, and risk summary.

## Engineering Best Practices

- **Typed state models** (`ResearchState`, `Finding`, `EvaluationResult`) instead of raw dicts
- **Separation of concerns**: graph orchestration, state, tools, and code parsing in independent modules
- **Deterministic graph routing** via `_decide_next()` rather than LLM-controlled flow
- **Bounded investigation** with configurable depth limits + LangGraph recursion limit
- **Graceful degradation**: LLM evaluation falls back to heuristic keyword matching when API is unavailable
- **Integration tests** validating the full contradiction→investigation→synthesis pipeline
- **Configurable execution** via environment variables

## Quickstart

### Prerequisites

- Python 3.12+
- Tree-sitter grammars (installed via graphifyy)

### Setup

```bash
# Clone the repo
git clone https://github.com/Atnatewoss/codeatlas.git
cd codeatlas

# Install packages in editable mode
pip install -e packages/graphify -e packages/research

# Install API dependencies
pip install -r apps/api/requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and set at least one LLM provider:

```env
# At least one of:
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# Optional model overrides (pinned defaults below)
OPENAI_MODEL=gpt-4o-mini
GOOGLE_MODEL=gemini-2.0-flash
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Research engine
MAX_INVESTIGATION_ROUNDS=2
```

### Run

```bash
# Start the API server
cd apps/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# Run integration tests
python packages/research/tests/test_tot_workflow.py
```

### API Endpoints

| Method | Path                          | Description                          |
|--------|-------------------------------|--------------------------------------|
| GET    | `/health`                     | Health check                         |
| POST   | `/api/research/start`         | Start a new research session         |
| GET    | `/api/research/status/{id}`   | Poll session status                  |
| GET    | `/api/research/stream/{id}`   | SSE stream for real-time progress    |
| DELETE | `/api/research/{id}`          | Cancel a running session             |

## Project Status

Active development. Core ToT engine is functional with 2 passing integration tests. LLM-backed contradiction detection and synthesis run when an API key is configured; heuristic fallback operates when none is available.

## Contributing

See [Contributing Guide](CONTRIBUTING.md).
