# CodeAtlas

Deep Research & Architecture Intelligence for Complex Codebases. A **Tree of Thought (ToT)** research chatbot that autonomously explores any Git repository using BFS-guided tool calls, evaluates findings with a hybrid scorer, and synthesizes a cited answer - all over WebSocket.

Built with **LangGraph** (state machine), **FastAPI**, **Next.js**, and **GitHub Models** (gpt-4o-mini, free tier).


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
| **evaluate_batch** | Hybrid scorer - calls LLM for relevance (0–1) + evidence strength (0–1) + rationale per thought, then computes source diversity from unique files. Weighted overall = 0.5×relevance + 0.3×evidence + 0.2×diversity. All evaluations run in parallel via `evaluation_workers`. |
| **prune_expand** | Drops scores < 0.4 (→ `rejected_ids`), keeps top-`keep_top_k` by score. For the best branches, generates child thoughts (up to `max_children`). If no branches survive but `depth < max_depth`, `decide_loop` routes back to `generate_thoughts` for fresh angles. If ≥70% of best branches have `ready_to_synthesize=true` (and depth ≥ 2), routes to `synthesize` early. |
| **synthesize** | Collects evidence from best branches, generates a Mermaid architecture diagram from the code graph, and produces a final answer with numbered citations, rejected-branch summary, and uncertainties. |


### Configurable Settings

All via env vars (defaults in `app/core/settings.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | - | Classic PAT for GitHub Models API |
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
