from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agents.state import ResearchState, Evidence
from agents.tools import PROMPTS, AnalysisOutput
import os

# Initialize LLM
# In production, ensure OPENAI_API_KEY is set in the environment.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
structured_llm = llm.with_structured_output(AnalysisOutput)

def build_research_graph():
    """
    Builds the Tree of Thought (ToT) exploration graph.
    """
    workflow = StateGraph(ResearchState)
    
    def _run_analysis_node(state: ResearchState, node_name: str) -> dict:
        """Helper to run a specific analysis branch."""
        # 1. Get the prompt for this branch
        prompt = PROMPTS[node_name].format(repo_url=state.repo_url)
        
        # 2. Invoke the LLM
        # If API key is missing during dev, we fallback to a mock response to prevent crashes
        if not os.environ.get("OPENAI_API_KEY"):
            output = AnalysisOutput(
                findings=[f"Mock finding for {node_name}"],
                evidence=[{"filepath": "src/mock.py", "snippet": "def mock(): pass", "explanation": "Mock explanation"}]
            )
        else:
            output = structured_llm.invoke(prompt)
            
        # 3. Format evidence
        parsed_evidence = [
            Evidence(
                filepath=e.get("filepath", "unknown"),
                snippet=e.get("snippet", ""),
                explanation=e.get("explanation", "")
            ) for e in output.evidence
        ]
        
        # 4. Return state update
        return {
            "status": "done",
            "findings": output.findings,
            "evidence": parsed_evidence
        }

    def analyze_structure(state: ResearchState) -> ResearchState:
        res = _run_analysis_node(state, "structure")
        state.structure_analysis.status = res["status"]
        state.structure_analysis.findings = res["findings"]
        state.structure_analysis.evidence = res["evidence"]
        return state

    def analyze_runtime(state: ResearchState) -> ResearchState:
        res = _run_analysis_node(state, "runtime")
        state.runtime_analysis.status = res["status"]
        state.runtime_analysis.findings = res["findings"]
        state.runtime_analysis.evidence = res["evidence"]
        return state

    def analyze_design(state: ResearchState) -> ResearchState:
        res = _run_analysis_node(state, "design")
        state.design_reasoning.status = res["status"]
        state.design_reasoning.findings = res["findings"]
        state.design_reasoning.evidence = res["evidence"]
        return state

    def analyze_onboarding(state: ResearchState) -> ResearchState:
        res = _run_analysis_node(state, "onboarding")
        state.developer_onboarding.status = res["status"]
        state.developer_onboarding.findings = res["findings"]
        state.developer_onboarding.evidence = res["evidence"]
        return state

    def analyze_risks(state: ResearchState) -> ResearchState:
        res = _run_analysis_node(state, "risk")
        state.risk_assessment.status = res["status"]
        state.risk_assessment.findings = res["findings"]
        state.risk_assessment.evidence = res["evidence"]
        return state

    # Add Nodes
    workflow.add_node("structure", analyze_structure)
    workflow.add_node("runtime", analyze_runtime)
    workflow.add_node("design", analyze_design)
    workflow.add_node("onboarding", analyze_onboarding)
    workflow.add_node("risk", analyze_risks)

    # Sequence execution (ToT branches could be executed in parallel using Fan-out)
    workflow.set_entry_point("structure")
    workflow.add_edge("structure", "runtime")
    workflow.add_edge("runtime", "design")
    workflow.add_edge("design", "onboarding")
    workflow.add_edge("onboarding", "risk")
    workflow.add_edge("risk", END)

    return workflow.compile()
