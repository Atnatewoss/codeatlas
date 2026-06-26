<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+"/>
  <img src="https://img.shields.io/badge/node-18%2B-brightgreen" alt="Node 18+"/>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT"/>
</p>

<h1 align="center">CodeAtlas</h1>
<p align="center"><strong>Build a mental model of any codebase in minutes.</strong></p>

---

Every day, engineers waste hours onboarding onto unfamiliar repositories - tracing data flow, finding entry points, untangling architecture decisions buried across hundreds of files. Code search tools (ripgrep, GitHub search) return *matches*, not *understanding*. Documentation is perpetually out of date.

**CodeAtlas is an autonomous codebase intelligence engine.** It first builds a rich **code graph** (via [graphify](https://github.com/anomalyco/graphify), AST-derived, with nodes for every symbol and edges for calls, imports, and inheritance) that represents the full structure of the repository. This graph then drives a LangGraph-powered Tree-of-Thought workflow - exploring the codebase, reasoning about architecture, and synthesizing everything into a coherent mental model with call graphs, data flow diagrams, and cited evidence. It works on repos of any size, language, or framework.

---

## Features

- **Code Graph** - Builds an AST-derived graph (via [graphify](https://github.com/anomalyco/graphify)) of every symbol, call relationship, import, and inheritance edge across the entire repository - the backbone that powers all analysis tools.
- **Autonomous Exploration** - LLM-driven agent generates hypotheses, selects tools (`grep`, `glob`, `read_file`, `lookup_symbol`, `get_callers`, `get_callees`, `graph_stats`), executes them in parallel, and iterates - no human in the loop.
- **BFS + Beam Search Hybrid** - Broad exploration at each depth level combined with beam-style pruning that keeps only the top-K scoring thoughts, focusing compute on the most promising reasoning branches.
- **Hybrid Scorer** - Each thought is scored on relevance (0-1), evidence strength (0-1), and source diversity. Weighted overall: `0.5×relevance + 0.3×evidence + 0.2×diversity`.
- **Traced Citations** - Every claim in the synthesis links back to specific files and lines (`file.py:42`) so you can verify and explore the source directly.
- **Architecture Diagrams** - Auto-generated Mermaid diagrams showing module relationships, call graphs, and data flow.
- **Real-Time Streaming** - WebSocket-based communication so you see research progress as it happens.

---

## How It Works

CodeAtlas first builds a **code graph** (via [graphify](https://github.com/anomalyco/graphify)) - a complete AST-derived graph of every symbol, function, class, call relationship, import, and inheritance edge in the repository. This graph is the backbone of the exploration: all tools (lookup_symbol, get_callers, get_callees, graph_stats) query against it directly.

On top of this graph, CodeAtlas runs a **BFS + Beam Search** hybrid - BFS governs the depth-limited exploration while beam search prunes low-value branches at each level, keeping only the top-K scoring thoughts.

```
generate_thoughts → execute_batch → evaluate_batch → beam_prune_expand ──→ synthesize
                                                                  │
                                                                  ├──→ execute_batch (normal loop)
                                                                  └──→ generate_thoughts (re-generate when beam empty)
```

| Node | Description |
|------|-------------|
| **generate_thoughts** | LLM proposes 2–3 hypotheses with tool selections. On re-generation, avoids previously explored angles. |
| **execute_batch** | Runs each pending thought's tool against the repo in parallel (`ThreadPoolExecutor`). Collects outcomes and file paths. |
| **evaluate_batch** | Hybrid scorer: LLM evaluates relevance + evidence strength, computes source diversity from unique files touched. All evaluations run in parallel. |
| **beam_prune_expand** | Beam step - drops scores < 0.4, keeps top-K (`keep_top_k`), generates child thoughts (up to `max_children`). If beam empties before `max_depth`, routes back for fresh angles. Early-exits to synthesis when ≥70% of beam candidates are ready. |
| **synthesize** | Collects evidence from best branches, generates a Mermaid architecture diagram, produces a final answer with numbered citations (file:line), rejected-branch summary, and uncertainties. |

The state machine is built with **LangGraph**. The stack: **FastAPI** (backend), **Next.js** (frontend), **GitHub Models** (LLM, free tier).

---

## Quick Start

```bash
# 1. Install dependencies
make setup                          # macOS / Linux
.\dev.ps1 setup                     # Windows

# 2. Configure your API key
cp apps/api/.env.example apps/api/.env
# Edit .env → set GITHUB_TOKEN=ghp_your_token_here

# 3. Run (API + Web in parallel)
make dev                            # macOS / Linux
.\dev.ps1 dev                       # Windows
```

- **API**: http://localhost:8000
- **Web**: http://localhost:3000

```bash
# Run tests
make test                           # macOS / Linux
.\dev.ps1 test                      # Windows
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | - | GitHub PAT for API access |
| `GENERATION_LLM_MODEL` | `gpt-4o-mini` | Model for hypothesis generation |
| `EVALUATION_LLM_MODEL` | `gpt-4o-mini` | Model for scoring |
| `SYNTHESIS_LLM_MODEL` | `gpt-4o-mini` | Model for final synthesis |
| `MAX_DEPTH` | `3` | BFS depth limit |
| `MAX_CHILDREN` | `2` | Max child thoughts per parent |
| `KEEP_TOP_K` | `5` | Beam width |
| `EXECUTION_WORKERS` | `4` | Parallel tool call workers |
| `EVALUATION_WORKERS` | `2` | Parallel LLM evaluation workers |

---

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for planned work including **CLI**, **BYOK** (bring your own LLM key), **Slack/Discord bots**, **VS Code extension**, **GitHub Action**, and more.
