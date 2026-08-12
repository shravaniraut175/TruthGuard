# TruthGuard Streamlit Frontend
"""Streamlit frontend for TruthGuard hallucination detection."""

import streamlit as st
import requests
from typing import Optional


# Page configuration
st.set_page_config(
    page_title="TruthGuard - AI Hallucination Detection",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .risk-banner {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .risk-low { background-color: #d4edda; color: #155724; }
    .risk-medium { background-color: #fff3cd; color: #856404; }
    .risk-high { background-color: #f8d7da; color: #721c24; }
    .risk-critical { background-color: #721c24; color: #ffffff; }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #007bff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)


def get_risk_class(risk_level: str) -> str:
    """Get CSS class for risk level."""
    return f"risk-{risk_level.lower()}"


def format_score(score: float) -> str:
    """Format score as percentage."""
    return f"{score * 100:.1f}%"


def main():
    """Main Streamlit application."""
    
    # Sidebar configuration
    with st.sidebar:
        st.image("https://img.shields.io/badge/TruthGuard-v1.0.0-blue", use_container_width=True)
        st.markdown("---")
        
        # Backend URL configuration
        backend_url = st.text_input(
            "Backend URL",
            value="http://localhost:8000",
            help="URL of the FastAPI backend"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        TruthGuard is an AI hallucination detection framework that verifies 
        LLM responses before presenting them to users.
        
        **Features:**
        - Multi-detector ensemble
        - External search grounding
        - Confidence-based regeneration
        - Heterogeneous model support
        """)
    
    # Main title
    st.title("🛡️ TruthGuard")
    st.markdown("AI Hallucination Detection Framework")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Verify Existing Response", "Generate and Verify"])
    
    # Tab 1: Verify Existing Response
    with tab1:
        st.header("Verify Existing Response")
        
        col1, col2 = st.columns(2)
        with col1:
            prompt = st.text_area(
                "User Prompt",
                placeholder="Enter the original user prompt...",
                height=150,
                key="verify_prompt"
            )
        
        with col2:
            response = st.text_area(
                "LLM Response to Verify",
                placeholder="Enter the LLM-generated response...",
                height=150,
                key="verify_response"
            )
        
        regenerate = st.checkbox(
            "Enable automatic regeneration if hallucination probability is high",
            value=False,
            key="verify_regenerate"
        )
        
        if st.button("Verify Response", type="primary", key="verify_btn"):
            if not prompt or not response:
                st.error("Please enter both prompt and response.")
            else:
                verify_existing_response(backend_url, prompt, response, regenerate)
    
    # Tab 2: Generate and Verify
    with tab2:
        st.header("Generate and Verify")
        
        prompt = st.text_area(
            "User Prompt",
            placeholder="Enter your question or prompt...",
            height=150,
            key="gen_prompt"
        )
        
        regenerate = st.checkbox(
            "Enable automatic regeneration if hallucination probability is high",
            value=True,
            key="gen_regenerate"
        )
        
        if st.button("Generate and Verify", type="primary", key="gen_btn"):
            if not prompt:
                st.error("Please enter a prompt.")
            else:
                generate_and_verify(backend_url, prompt, regenerate)


def verify_existing_response(
    backend_url: str,
    prompt: str,
    response: str,
    regenerate: bool
):
    """Verify an existing response."""
    
    url = f"{backend_url.rstrip('/')}/verify"
    
    payload = {
        "prompt": prompt,
        "response": response,
        "regenerate": regenerate
    }
    
    with st.spinner("Verifying response..."):
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            display_verification_result(result)
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to backend at {backend_url}. Is the server running?")
        except requests.exceptions.Timeout:
            st.error("Request timed out. The verification took too long.")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def generate_and_verify(backend_url: str, prompt: str, regenerate: bool):
    """Generate a response and verify it."""
    
    url = f"{backend_url.rstrip('/')}/generate-and-verify"
    
    payload = {
        "prompt": prompt,
        "regenerate": regenerate
    }
    
    with st.spinner("Generating and verifying response..."):
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            
            # Show generated response first
            st.subheader("Generated Response")
            st.write(result.get("generated_response", "N/A"))
            
            st.markdown("---")
            
            # Display verification result
            display_verification_result(result)
            
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to backend at {backend_url}. Is the server running?")
        except requests.exceptions.Timeout:
            st.error("Request timed out. The generation/verification took too long.")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def display_verification_result(result: dict):
    """Display verification results."""
    
    st.subheader("Verification Results")
    
    # Risk level banner
    risk_level = result.get("risk_level", "unknown")
    risk_class = get_risk_class(risk_level)
    st.markdown(
        f'<div class="risk-banner {risk_class}">Risk Level: {risk_level.upper()}</div>',
        unsafe_allow_html=True
    )
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        truth_score = result.get("truth_score", 0)
        st.metric(
            label="Truth Score",
            value=format_score(truth_score),
            delta=None
        )
    
    with col2:
        confidence_score = result.get("confidence_score", 0)
        st.metric(
            label="Confidence Score",
            value=format_score(confidence_score),
            delta=None
        )
    
    with col3:
        hallu_prob = result.get("hallucination_probability", 0)
        st.metric(
            label="Hallucination Probability",
            value=format_score(hallu_prob),
            delta="-lower is better" if hallu_prob < 0.3 else None
        )
    
    # Explanation
    st.markdown("### Analysis")
    st.write(result.get("explanation", "No explanation available."))
    
    # Grounding explanation
    grounding_exp = result.get("grounding_explanation", "")
    if grounding_exp:
        st.info(grounding_exp)
    
    # Module scores in expanders
    st.markdown("### Module Scores")
    
    module_scores = result.get("module_scores", {})
    
    with st.expander("Black-box Consistency Score"):
        bb_score = module_scores.get("blackbox")
        if bb_score is not None:
            st.progress(bb_score)
            st.write(f"Score: {format_score(bb_score)}")
        else:
            st.write("Not available")
    
    with st.expander("White-box Token Confidence"):
        wb_score = module_scores.get("whitebox")
        if wb_score is not None:
            st.progress(wb_score)
            st.write(f"Score: {format_score(wb_score)}")
        else:
            st.write("Disabled or unavailable")
    
    with st.expander("LLM-as-a-Judge Score"):
        judge_score = module_scores.get("judge")
        if judge_score is not None:
            st.progress(judge_score)
            st.write(f"Score: {format_score(judge_score)}")
        else:
            st.write("Not available")
    
    with st.expander("External Grounding Score"):
        ground_score = module_scores.get("grounding")
        if ground_score is not None:
            st.progress(ground_score)
            st.write(f"Score: {format_score(ground_score)}")
        else:
            st.write("Not available")
    
    # Veto information
    if result.get("veto_applied", False):
        st.warning(f"**Veto Applied:** {result.get('veto_reason', 'Unknown reason')}")
    
    # External evidence
    evidence = result.get("evidence", [])
    sources = result.get("sources", [])
    
    if evidence:
        st.markdown("### External Evidence")
        
        for i, ev in enumerate(evidence, 1):
            with st.expander(f"Evidence {i}: {ev.get('title', 'Untitled')}"):
                st.write(f"**Source:** {ev.get('source', 'Unknown')}")
                st.write(f"**Snippet:** {ev.get('snippet', 'No snippet')}")
                if ev.get('url'):
                    st.markdown(f"[View Source]({ev.get('url')})")
    
    # Source links
    if sources:
        st.markdown("### Sources")
        for i, src in enumerate(sources, 1):
            st.markdown(f"{i}. [{src.get('title', 'Untitled')}]({src.get('url', '#')})")
    
    # Regenerated response
    if result.get("regeneration_triggered", False):
        st.markdown("### 🔄 Regenerated Safer Response")
        regenerated = result.get("regenerated_response", "")
        if regenerated:
            st.write(regenerated)
        
        regen_exp = result.get("regeneration_explanation", "")
        if regen_exp:
            st.info(regen_exp)


if __name__ == "__main__":
    main()
