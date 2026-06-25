# CodeAtlas

Deep Research & Architecture Intelligence for Complex Codebases. A **Tree of Thought (ToT)** research chatbot that autonomously explores any Git repository using BFS-guided tool calls, evaluates findings with a hybrid scorer, and synthesizes a cited answer — all over WebSocket/SSE.

Built with **LangGraph** (state machine), **FastAPI**, **Next.js**, and **GitHub Models** (gpt-4o-mini, free tier).

## Architecture

```
codeatlas/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── .env / .env.example       # GitHub token + optional per-task overrides
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py               # FastAPI app (CORS, routes, health)
│   │       ├── core/
│   │       │   └── settings.py       # All config via env vars (Pydantic Settings)
│   │       ├── routers/
│   │       │   └── chat.py           # POST /research, WebSocket /ws/{id}, GET /status
│   │       ├── schemas/
│   │       │   └── chat.py           # Pydantic request/response models
│   │       └── services/             # Flat — no subdirectories
│   │           ├── state.py          # Pydantic models + ToTChatState TypedDict
│   │           ├── events.py         # In-memory event bus for streaming
│   │           ├── clone.py          # Git clone to hashed cache dir
│   │           ├── code_graph.py     # Wraps graphify + networkx for symbol/call graphs
│   │           ├── prompts.py        # LLM prompt templates (generate, evaluate, synthesize)
│   │           ├── tot_tools.py      # File tools (grep/glob/read_file) + code graph tools + scoring
│   │           ├── tot_nodes.py      # BFS state machine node functions (parallel execution)
│   │           ├── tot_chat.py       # LangGraph StateGraph builder + compile
│   │           └── research.py       # Top-level orchestration (clone → graph → ToT → stream)
│   └── web/                          # Next.js 16 App Router frontend
│       └── src/
│           ├── app/
│           │   ├── page.tsx          # Entry point
│           │   ├── home.tsx          # Landing page
│           │   ├── chat/             # Per-repo chat pages
│           │   └── globals.css       # Theme + scrollbar styles
│           ├── components/
│           │   └── chat/
│           │       ├── chat-panel.tsx      # Main chat layout (messages + thinking + answer)
│           │       ├── composer.tsx         # Textarea (Enter to send, Shift+Enter for newline)
│           │       ├── message.tsx          # Markdown-rendered message bubbles
│           │       ├── thinking-section.tsx # Status header + ToT tree + architecture diagram
│           │       ├── tot-tree.tsx         # BFS tree visualization with per-axis scores
│           │       ├── mermaid-block.tsx    # Mermaid diagram renderer (zoomable)
│           │       └── typewriter-text.tsx  # (unused — kept for reference)
│           └── hooks/
│               └── use-chat-stream.ts  # WebSocket hook (answer_chunk, thought_pruned, etc.)
├── Makefile                         # Dev orchestration (macOS/Linux)
└── dev.ps1                          # Dev orchestration (Windows)
```

## The ToT Loop

The system runs a **BFS state machine** over a tree of "thought" nodes:

```
generate_thoughts → execute_batch → evaluate_batch → prune_expand ──→ synthesize
                                                           │
                                                           ├──→ execute_batch (normal BFS loop)
                                                           └──→ generate_thoughts (re-generate when all pruned)
```

| Node | What it does |
|------|-------------|
| **generate_thoughts** | LLM generates 2–3 angles/hypotheses with tool selections (`grep`, `glob`, `read_file`, `lookup_symbol`, `get_callers`, `get_callees`, `graph_stats`). On re-generation, sees previously tried angles and suggests completely different ones. |
| **execute_batch** | Runs each pending thought's tool against the repo in parallel (`ThreadPoolExecutor`, `execution_workers`). Collects outcomes and accessed file paths. |
| **evaluate_batch** | Hybrid scorer — calls LLM for relevance (0–1) + evidence strength (0–1) + rationale per thought, then computes source diversity from unique files. Weighted overall = 0.5×relevance + 0.3×evidence + 0.2×diversity. All evaluations run in parallel via `evaluation_workers`. |
| **prune_expand** | Drops scores < 0.4 (→ `rejected_ids`), keeps top-`keep_top_k` by score. For the best branches, generates child thoughts (up to `max_children`). If no branches survive but `depth < max_depth`, `decide_loop` routes back to `generate_thoughts` for fresh angles. If ≥70% of best branches have `ready_to_synthesize=true` (and depth ≥ 2), routes to `synthesize` early. |
| **synthesize** | Collects evidence from best branches, generates a Mermaid architecture diagram from the code graph, and produces a final answer with numbered citations, rejected-branch summary, and uncertainties. |

### Thought Anatomy

Each thought carries structured metadata:

- `angle` — exploration perspective
- `hypothesis` — testable claim
- `tool` / `target` — what to search/regex/file
- `expected_evidence` — what patterns validate the hypothesis
- `outcome` — raw tool output
- `accessed_files` — files touched during execution (for diversity scoring)
- `evaluation` — `{relevance, evidence_strength, source_diversity, overall_score, reasoning}`
- `is_pruned` — rejected by pruning threshold (< 0.4)
- `child_ids` — spawned child nodes
- `ready_to_synthesize` — LLM flagged "enough evidence"

### Configurable Settings

All via env vars (defaults in `app/core/settings.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | — | Classic PAT for GitHub Models API |
| `GENERATION_LLM_MODEL` | `gpt-4o-mini` | Model for thought generation |
| `EVALUATION_LLM_MODEL` | `gpt-4o-mini` | Model for thought evaluation |
| `SYNTHESIS_LLM_MODEL` | `gpt-4o-mini` | Model for final synthesis |
| `MAX_DEPTH` | `3` | BFS depth limit |
| `MAX_CHILDREN` | `2` | Max child thoughts per parent |
| `KEEP_TOP_K` | `5` | Active branches kept after pruning |
| `EXECUTION_WORKERS` | `4` | Parallel tool call workers |
| `EVALUATION_WORKERS` | `2` | Parallel LLM evaluation workers |

## Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- A [GitHub classic PAT](https://github.com/settings/tokens) (no scopes needed)

### Install & Run

```bash
# Install dependencies
make setup                          # macOS / Linux
.\dev.ps1 setup                     # Windows

# Configure
cp apps/api/.env.example apps/api/.env
# Edit .env — set GITHUB_TOKEN=ghp_...

# Run (both API + web in parallel)
make dev                            # macOS / Linux
.\dev.ps1 dev                       # Windows
```

- **API**: http://localhost:8000
- **Web**: http://localhost:3000

### Testing

```bash
make test       # macOS / Linux
.\dev.ps1 test  # Windows
```

## API Endpoints

### REST

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/chat/research` | Start ToT research — body: `{ repo_path, query?, max_depth?, max_children?, keep_top_k? }` |
| GET | `/api/chat/status/{session_id}` | Poll for session state and final answer |

### WebSocket

| Path | Description |
|------|-------------|
| `ws://localhost:8000/api/chat/ws/{session_id}` | Real-time event stream |

### Event Types

| Event | When | Data |
|-------|------|------|
| `research_started` | Session created | `query`, `repo_path`, `max_depth`, `max_children`, `keep_top_k` |
| `graph_status` | Code graph building | `status` (building/ready/error) |
| `graph_diagram` | Mermaid diagram ready | `diagram` (Mermaid source) |
| `clone_progress` | During git clone | `message` |
| `thought_generated` | New thought created | `id`, `angle`, `hypothesis`, `tool`, `target`, `expected_evidence` |
| `thought_executing` | Tool started | `id`, `tool`, `target` |
| `thought_result` | Tool completed | `id`, `outcome` (preview) |
| `thought_evaluated` | Thought scored | `id`, `score`, `relevance`, `evidence_strength`, `source_diversity`, `reasoning` `ready_to_synthesize` |
| `thought_pruned` | Pruned during branch selection | `id`, `score`, `threshold`, `reason` |
| `state` | Phase transition | `phase`, `pending`, `best`, `rejected`, `depth` |
| `answer_chunk` | During synthesis | `answer` |
| `citations` | Final citations | `citations` (string array) |
| `rejected_branches` | Pruned branch summary | `summary` |
| `uncertainties` | Unresolved questions | `uncertainties` |
| `complete` | Research done | `answer` |
| `error` | Failure | `message` |

## Frontend

- **Chat view**: Messages rendered with `react-markdown` + `remark-gfm` + `remark-breaks`. User messages: right-aligned `max-w-[75%]` bubble. Assistant messages: full-width with no bubble.
- **Thinking section**: Appears while researching — shows status (pulse dot + phase label), BFS tree visualization with per-axis score breakdown (`R:75% E:70% D:100%`), pruning rationale on rejected nodes, and an always-visible Mermaid architecture diagram.
- **Composer**: `Enter` to send, `Shift+Enter` for newline.
- **Theming**: Near-black base (`#0A0A0F`), Inter font, thin custom scrollbars.

## Engineering Decisions

- **BFS over DFS**: Per the ToT paper — explore all candidates at a level before deepening.
- **Single free-tier LLM**: GitHub Models gpt-4o-mini. No OpenAI/Anthropic/Ollama providers.
- **Hybrid scoring**: 50% LLM relevance + 30% LLM evidence strength + 20% deterministic source diversity (unique files / 3.0, capped at 1.0).
- **Prune < 0.4**: Configurable threshold; pruned nodes show rationale in the UI.
- **Configurable beam width**: `max_children` (branching) and `keep_top_k` (active branches) are settable per-request.
- **Parallel execution**: Tool calls and LLM evaluations each use a `ThreadPoolExecutor` with configurable worker counts.
- **Dynamic re-generation**: If all branches get pruned mid-search, the system re-generates fresh angles instead of failing.
- **Early termination**: When ≥70% of top branches have `ready_to_synthesize=true` at depth ≥ 2, the system cuts to synthesis.
- **Persistent clone cache**: Repos clone to `~/.codeatlas/repos/<sha256[:16]>` — cached across sessions.
- **LangGraph + MemorySaver**: In-memory state machine with no external dependencies.
