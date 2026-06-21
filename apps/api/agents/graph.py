from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from agents.state import ResearchState, Evidence
from agents.tools import PROMPTS, GET_TOOLS
import os

# Initialize LLM
# In production, ensure OPENAI_API_KEY is set in the environment.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def build_research_graph():
    """
    Builds the Tree of Thought (ToT) exploration graph.
    """
    workflow = StateGraph(ResearchState)
    
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage, HumanMessage
    
    def _run_analysis_node(state: ResearchState, node_name: str) -> dict:
        """Helper to run a specific analysis branch using a ReAct agent."""
        # 1. Get the prompt for this branch
        base_prompt = PROMPTS[node_name].format(repo_url=state.repo_url)
        system_prompt = f"{base_prompt}\n\nYou have access to tools to explore the local repository at '{state.repo_path}'.\nUse `submit_findings` when you are done."
        
        # 2. Invoke the LLM
        if not os.environ.get("OPENAI_API_KEY"):
            return {
                "status": "done",
                "findings": [f"Mock finding for {node_name}"],
                "evidence": [Evidence(filepath="src/mock.py", snippet="def mock(): pass", explanation="Mock explanation")]
            }
            
        # Create an inner ReAct agent to explore
        agent = create_react_agent(llm, GET_TOOLS)
        
        try:
            # We seed it with the system prompt and a human message to start
            result = agent.invoke({
                "messages": [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content="Please begin your exploration and call submit_findings when done.")
                ]
            })
            
            # Extract findings from the tool call to submit_findings
            findings = []
            evidence_list = []
            
            # Look backwards through messages to find the submit_findings call
            for m in reversed(result["messages"]):
                if hasattr(m, 'tool_calls') and m.tool_calls:
                    for tc in m.tool_calls:
                        if tc['name'] == 'submit_findings':
                            args = tc['args']
                            findings = args.get('findings', [])
                            for e in args.get('evidence', []):
                                evidence_list.append(Evidence(
                                    filepath=e.get("filepath", "unknown"),
                                    snippet=e.get("snippet", ""),
                                    explanation=e.get("explanation", "")
                                ))
                            break
                    if findings:
                        break
                        
            # Fallback if agent didn't use submit_findings correctly
            if not findings:
                findings = ["Exploration completed but findings were not formatted correctly."]
                evidence_list = [Evidence(filepath="unknown", snippet="", explanation=result["messages"][-1].content)]
                
            return {
                "status": "done",
                "findings": findings,
                "evidence": evidence_list
            }
        except Exception as e:
            return {
                "status": "failed",
                "findings": [f"Analysis failed: {str(e)}"],
                "evidence": []
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
