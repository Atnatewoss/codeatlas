from app.services.graph.state import ToTChatState, ToTThought


def generate_thoughts_prompt(state: ToTChatState) -> str:
    has_existing = bool(state.get("thoughts"))
    if has_existing:
        thoughts_raw = state.get("thoughts", {})
        existing_lines = []
        for raw in thoughts_raw.values():
            t = ToTThought(**raw) if isinstance(raw, dict) else raw
            existing_lines.append(f"  - {t.angle} (hypothesis: {t.hypothesis[:80]})")
        existing_block = (
            "Previous exploration angles that were tried and did not yield conclusive results:\n"
            + "\n".join(existing_lines)
            + "\n\nThese approaches did not sufficiently answer the query. "
            "Suggest COMPLETELY DIFFERENT angles that haven't been explored yet.\n\n"
        )
    else:
        existing_block = ""

    body = (
        f"Repository: {state['repo_path']}\n"
        f"User query: {state['user_query']}\n\n"
        "You are starting a Tree of Thought exploration of this codebase.\n"
        "Generate 2-3 initial exploration steps. For EACH step provide:\n"
        "  - angle: A unique perspective or angle being explored\n"
        "  - hypothesis: An explicit, testable hypothesis about what you expect to find\n"
        "  - tool: One of: grep, glob, read_file, lookup_symbol, get_callers, get_callees, graph_stats\n"
        "  - target: The actual regex, glob pattern, filepath, symbol name, or function name\n"
        "  - expected_evidence: What specific code patterns would validate this hypothesis\n\n"
        "Available tools (choose EXACTLY one tool name — no extra words, no descriptions):\n"
        "- grep: regex pattern. Searches file contents.\n"
        "- glob: glob pattern. Finds files by name.\n"
        "- read_file: file path. Reads the file.\n"
        "- lookup_symbol: symbol name. Finds class/function definitions.\n"
        "- get_callers: function name. Finds what calls it.\n"
        "- get_callees: function name. Finds what it calls.\n"
        "- graph_stats: (target ignored). Code graph statistics.\n\n"
        "CRITICAL: tool must be EXACTLY one word from the list above. "
        "Do NOT write 'grep <regex>' — write just 'grep'. "
        "Do NOT invent tools like 'documentation review', 'search examples', "
        "'community forums', 'online tutorials', 'read documentation'. "
        "Those are not valid tools. Stick to the seven listed.\n\n"
        "Examples for query 'What packages are used?':\n"
        "  angle: Dependency declaration files\n"
        "  hypothesis: The project declares dependencies in requirements.txt or pyproject.toml\n"
        "  tool: glob\n"
        "  target: requirements*.txt\n"
        "  expected_evidence: Lines like package==version or similar pinned dependencies\n"
        "  angle: Import analysis\n"
        "  hypothesis: Python source files import external packages at the top\n"
        "  tool: grep\n"
        "  target: ^import |^from \n"
        "  expected_evidence: Lines starting with 'import' or 'from' showing package names"
    )

    return existing_block + body


def evaluate_thought_prompt(query: str, thought: ToTThought) -> str:
    return (
        f"User query: {query}\n\n"
        f"Exploration angle: {thought.angle}\n"
        f"Hypothesis: {thought.hypothesis}\n"
        f"Tool used: {thought.tool} ('{thought.target}')\n"
        f"Expected evidence: {thought.expected_evidence}\n\n"
        f"Actual results:\n{thought.outcome[:2000]}\n\n"
        "Evaluate this thought on two criteria (0-100 scale):\n"
        "1. relevance: How relevant is this result to answering the user query?\n"
        "2. evidence_strength: How strong/clear is the evidence found?\n\n"
        "If the result is partially informative, suggest 1-2 follow-up exploration steps.\n"
        "A follow-up should have its own angle, hypothesis, tool, target, and expected evidence.\n"
        "If you have enough evidence to form a complete answer, set ready_to_synthesize=true.\n"
        "Note any uncertainties or missing evidence that should be highlighted."
    )


def synthesize_prompt(
    query: str,
    evidence_text: str,
    rejected_text: str,
    uncertainty_text: str,
    mermaid_text: str,
) -> str:
    return (
        f"User query: {query}\n\n"
        f"Evidence from codebase exploration:\n{evidence_text[:5000]}\n\n"
        f"{rejected_text}{uncertainty_text}"
        f"{mermaid_text}\n\n"
        "Synthesize a thorough, professional answer based on this evidence.\n"
        "Your response must include:\n"
        "1. answer: A well-structured, concise answer suitable for senior software engineers. "
        "Cite specific files, packages, and code patterns found using numbered inline "
        "references like [1], [2] that correspond to the citations list. "
        "The answer should be purely the analysis and findings — do NOT include "
        "'Rejected Branches Summary' or 'Uncertainties' sections in the answer text; "
        "those go in their dedicated fields below.\n"
        "   If a Mermaid architecture diagram is provided above, reference relevant parts "
        "of it in your answer (e.g., 'the auth module calls UserService as shown in the diagram').\n"
        "2. citations: List of cited file paths with line numbers. "
        "The first citation [1] should correspond to the first marker in the answer, etc.\n"
        "3. rejected_branches_summary: Which exploration paths were pruned and why\n"
        "4. uncertainties: Any unresolved assumptions or missing evidence\n\n"
        "If the evidence does not fully answer the query, say so clearly."
    )


FALLBACK_ANSWER_TEMPLATE = (
    "I explored the codebase but couldn't find specific information about '{query}'.\n"
    "The exploration ran into an issue during analysis. Please try rephrasing your query."
)


def fallback_answer(query: str) -> str:
    return FALLBACK_ANSWER_TEMPLATE.format(query=query)
