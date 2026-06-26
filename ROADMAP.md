# Roadmap

## Near Term

### CLI
A first-class command-line interface for running CodeAtlas without the web UI. Target usage:

```bash
codeatlas explore <repo-path-or-url> --depth 5 --format markdown
codeatlas ask <repo-path-or-url> "how does authentication work?"
```

The CLI will stream research progress to stdout and output the final synthesis as markdown, JSON, or plain text. Useful for CI/CD, scripting, and users who prefer the terminal.

### Agentic Apps
Rethink the application surface to position CodeAtlas as more than a single chat interface:

- **Per-repo agents** — persist research state per repository so users can ask follow-ups without re-exploring
- **Slack / Discord bots** — drop a repo link and get an architectural summary back
- **GitHub Action** — auto-generate architecture docs on PRs or releases
- **VS Code extension** — explore the workspace you already have open

### BYOK (Bring Your Own Key)
Support for user-provided LLM API keys beyond GitHub Models:

| Provider | Status |
|----------|--------|
| OpenAI | Planned |
| Anthropic | Planned |
| Azure OpenAI | Planned |
| Ollama (local) | Planned |
| GitHub Models | Existing |

This unlocks private repositories, higher rate limits, and custom model selection per task (e.g., Gemini for synthesis, Claude for evaluation).

---

## Medium Term

### Deep Memory & Persistence
- Store research artifacts (thought trees, evidence, diagrams) in a local database
- Incremental re-exploration — detect what changed since last analysis and only re-explore affected areas
- Cross-repo comparisons — compare architecture between multiple repos

### Multi-Repository Workspaces
Analyze monorepo structures, microservice ecosystems, and dependency chains across multiple repositories in a single session.

### Custom Tool Plugins
Allow users to register custom analysis tools (e.g., security scanners, license checkers, custom lint rules) into the research pipeline.

---

## Long Term

### Self-Hosted SaaS
One-click deploy (Docker Compose / Helm chart) with team workspaces, shared research state, and usage analytics.

### Continuous Learning
Fine-tune scorers on user feedback to improve branch-pruning decisions over time, adapting to each team's codebase patterns.

---

*This roadmap is a living document. Priorities shift based on feedback — open an issue to suggest or vote on items.*
