import json
import html
import requests
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="TruthGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
.stApp { 
    background: linear-gradient(135deg, #0f0e1a 0%, #1a1028 50%, #0f0e1a 100%);
    color: #e0e7ff;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
.block-container { 
    max-width: 1200px; 
    padding-top: 2rem; 
    padding-bottom: 3rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

/* TOPBAR & BRANDING */
.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.1);
}
.brand {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.logo {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    font-size: 28px;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}
.brand-title {
    color: #f1f5f9;
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: -0.5px;
}
.brand-subtitle {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-top: 0.25rem;
    font-weight: 500;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    color: #4ade80;
    border-radius: 999px;
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* HERO SECTION */
.hero {
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    background: linear-gradient(135deg, 
        rgba(99, 102, 241, 0.08) 0%,
        rgba(168, 85, 247, 0.05) 50%,
        rgba(59, 130, 246, 0.08) 100%
    );
    backdrop-filter: blur(10px);
    margin-bottom: 2.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.15), transparent);
    border-radius: 50%;
    pointer-events: none;
}
.hero-kicker {
    color: #a78bfa;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 800;
    display: inline-block;
    padding: 0.5rem 1rem;
    background: rgba(168, 85, 247, 0.1);
    border-radius: 999px;
    border: 1px solid rgba(168, 85, 247, 0.3);
}
.hero-title {
    color: #ffffff;
    font-size: 2.8rem;
    line-height: 1.1;
    font-weight: 900;
    letter-spacing: -1px;
    margin-top: 1rem;
    background: linear-gradient(120deg, #ffffff, #e0e7ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-text {
    color: #b4c7e7;
    font-size: 1.1rem;
    line-height: 1.8;
    max-width: 800px;
    margin-top: 1rem;
    font-weight: 500;
}

/* SECTIONS */
.section-title {
    color: #f1f5f9;
    font-size: 1.3rem;
    font-weight: 900;
    margin-top: 2rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-text {
    color: #94a3b8;
    font-size: 0.9rem;
    margin-bottom: 1.25rem;
    font-weight: 500;
}

/* INPUTS */
div[data-testid="stTextArea"] textarea {
    background: rgba(15, 14, 26, 0.8) !important;
    border: 1.5px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 14px !important;
    color: #e0e7ff !important;
    font-size: 0.95rem !important;
    font-family: 'Segoe UI', sans-serif !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stTextArea"] textarea::placeholder {
    color: #64748b !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    background: rgba(15, 14, 26, 1) !important;
}

/* BUTTONS */
div.stButton > button, div.stLinkButton > a {
    border-radius: 12px !important;
    min-height: 48px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.3px !important;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #a855f7) !important;
    border: 0 !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
}
div.stButton > button[kind="secondary"] {
    border: 1.5px solid rgba(99, 102, 241, 0.3) !important;
    color: #e0e7ff !important;
    background: transparent !important;
}

/* PIPELINE */
.pipeline-box {
    background: rgba(15, 14, 26, 0.6);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 20px;
    padding: 2rem;
    margin: 1.5rem 0 2rem;
    backdrop-filter: blur(10px);
}
.pipeline-heading {
    color: #f1f5f9;
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.stage {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 12px;
    border: 1px solid rgba(99, 102, 241, 0.1);
    background: rgba(30, 27, 45, 0.8);
    transition: all 0.2s ease;
}
.stage:hover {
    background: rgba(30, 27, 45, 1);
    border-color: rgba(99, 102, 241, 0.2);
}
.stage-icon {
    width: 36px;
    height: 36px;
    min-width: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.85rem;
}
.done .stage-icon {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
}
.active .stage-icon {
    background: rgba(99, 102, 241, 0.3);
    color: #818cf8;
    animation: pulse 1.5s infinite;
}
.waiting .stage-icon {
    background: rgba(71, 85, 105, 0.2);
    color: #94a3b8;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}
.stage-body { flex: 1; }
.stage-name {
    color: #e0e7ff;
    font-size: 0.95rem;
    font-weight: 700;
}
.stage-message {
    color: #94a3b8;
    font-size: 0.8rem;
    margin-top: 0.35rem;
    font-weight: 500;
}
.stage-status {
    color: #64748b;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* METRICS */
.metric {
    background: rgba(30, 27, 45, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 1.75rem;
    min-height: 130px;
    transition: all 0.2s ease;
}
.metric:hover {
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(30, 27, 45, 1);
}
.metric-label {
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.75rem;
    font-weight: 800;
}
.metric-value {
    color: #f8fafc;
    font-size: 2.2rem;
    font-weight: 900;
    margin-top: 0.75rem;
}
.metric-help {
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 0.5rem;
}

/* RISK LEVEL */
.risk {
    border-radius: 16px;
    padding: 1.5rem 2rem;
    text-align: center;
    font-weight: 800;
    letter-spacing: 0.5px;
    margin: 1.5rem 0;
    border: 2px solid;
    font-size: 1.1rem;
}
.low {
    color: #4ade80;
    background: rgba(34, 197, 94, 0.12);
    border-color: rgba(34, 197, 94, 0.3);
}
.medium {
    color: #fbbf24;
    background: rgba(245, 158, 11, 0.12);
    border-color: rgba(245, 158, 11, 0.3);
}
.high {
    color: #fb7185;
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.3);
}
.critical {
    color: #fca5a5;
    background: rgba(220, 38, 38, 0.12);
    border-color: rgba(220, 38, 38, 0.3);
}
.unknown {
    color: #cbd5e1;
    background: rgba(100, 116, 139, 0.12);
    border-color: rgba(100, 116, 139, 0.3);
}

/* CONTENT CARDS */
.content-card {
    background: rgba(30, 27, 45, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 1.75rem;
    color: #cbd5e1;
    line-height: 1.8;
    font-size: 0.95rem;
}

/* MODULES */
.module {
    background: rgba(30, 27, 45, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px;
    padding: 1.25rem;
    margin: 0.75rem 0;
    color: #e0e7ff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.2s ease;
}
.module:hover {
    border-color: rgba(99, 102, 241, 0.3);
}
.module-score {
    color: #a78bfa;
    font-weight: 800;
    font-size: 1rem;
}

/* EVIDENCE */
.evidence {
    background: rgba(30, 27, 45, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 14px;
    padding: 1.5rem;
    margin: 1rem 0;
    transition: all 0.2s ease;
}
.evidence:hover {
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(30, 27, 45, 1);
}
.evidence-title {
    color: #e7edf5;
    font-weight: 800;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.evidence-meta {
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.evidence-text {
    color: #cbd5e1;
    font-size: 0.9rem;
    line-height: 1.7;
    margin-top: 0.75rem;
}

/* FOOTER */
.footer {
    color: #64748b;
    text-align: center;
    font-size: 0.85rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(99, 102, 241, 0.1);
    font-weight: 500;
}

/* TABS */
button[data-baseweb="tab"] {
    color: #94a3b8 !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 8px 8px 0 0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom-color: #6366f1 !important;
}

/* EXPANDER */
.streamlit-expanderHeader {
    background: transparent !important;
}
div[data-testid="stExpander"] {
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 12px !important;
    background: rgba(30, 27, 45, 0.8) !important;
}

/* PROGRESS BAR */
.stProgress > div > div {
    background: linear-gradient(90deg, #6366f1, #a855f7) !important;
}
</style>
""", unsafe_allow_html=True)

STAGES=[
("generation","Response Generation"),("blackbox","Black-box Consistency"),
("whitebox","White-box Confidence"),("grounding","External Grounding"),
("judge","LLM-as-a-Judge"),("fusion","Score Fusion"),
("regeneration","Safe Regeneration"),("complete","Final Assessment")
]

def esc(v): return html.escape(str(v or ""))
def score(v):
    try:return max(0,min(1,float(v)))
    except:return None
def pct(v):
    v=score(v)
    return f"{v*100:.1f}%" if v is not None else "N/A"

def metric(label,value,note):
    st.markdown(f'<div class="metric"><div class="metric-label">{esc(label)}</div><div class="metric-value">{esc(value)}</div><div class="metric-help">{esc(note)}</div></div>',unsafe_allow_html=True)

def render_header():
    st.markdown('<div class="topbar"><div class="brand"><div class="logo">🛡️</div><div><div class="brand-title">TruthGuard</div><div class="brand-subtitle">AI response verification & hallucination detection</div></div></div><div class="status-badge">🟢 System Ready</div></div>',unsafe_allow_html=True)

def render_pipeline(statuses,current=None,p=0,message=""):
    order={k:i for i,(k,_) in enumerate(STAGES)}; ci=order.get(current,-1); rows=[]
    for i,(key,name) in enumerate(STAGES):
        if current=="complete": state,icon,status="done","✓","Completed"; msg=statuses.get(key,"Completed.")
        elif i<ci: state,icon,status="done","✓","Completed"; msg=statuses.get(key,"Stage completed.")
        elif i==ci: state,icon,status="active","⟳","Running"; msg=message or statuses.get(key,"Processing...")
        else: state,icon,status="waiting","○","Waiting"; msg="Waiting for previous stage."
        rows.append(f'<div class="stage {state}"><div class="stage-icon">{icon}</div><div class="stage-body"><div class="stage-name">{esc(name)}</div><div class="stage-message">{esc(msg)}</div></div><div class="stage-status">{status}</div></div>')
    st.markdown(f'<div class="pipeline-box"><div class="pipeline-heading">🛡️ Verification Pipeline</div>{"".join(rows)}</div>',unsafe_allow_html=True)
    st.progress(max(0,min(100,int(p)))/100)

def render_results(r):
    st.markdown('<div class="section-title">📊 Verification Result</div>',unsafe_allow_html=True)
    risk=str(r.get("risk_level","unknown")).lower()
    if risk not in {"low","medium","high","critical"}: risk="unknown"
    risk_icons = {"low": "✓", "medium": "⚡", "high": "⚠", "critical": "🚨", "unknown": "❓"}
    st.markdown(f'<div class="risk {risk}">{risk_icons.get(risk, "?")} {risk.upper()} HALLUCINATION RISK</div>',unsafe_allow_html=True)
    
    col1,col2,col3=st.columns(3)
    with col1: metric("Truth Score",pct(r.get("truth_score")),"Higher indicates more truthfulness")
    with col2: metric("Confidence",pct(r.get("confidence_score")),"Combined module confidence")
    with col3: metric("Hallucination Risk",pct(r.get("hallucination_probability")),"Lower is safer")
    
    response=r.get("response") or r.get("generated_response","")
    st.markdown('<div class="section-title">💬 AI Response</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="content-card">{esc(response).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">🔍 Analysis & Explanation</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="content-card">{esc(r.get("explanation","No explanation available.")).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    if r.get("grounding_explanation"): 
        st.markdown(f'<div style="background:rgba(34,197,94,.1);border-left:4px solid #4ade80;border-radius:8px;padding:1rem;margin:1rem 0;color:#cbd5e1">{esc(r["grounding_explanation"]).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">🧠 Detection Modules</div>',unsafe_allow_html=True)
    for name,key in [("Black-box Consistency","blackbox"),("White-box Token Confidence","whitebox"),("LLM-as-a-Judge","judge"),("External Grounding","grounding")]:
        v=score((r.get("module_scores") or {}).get(key))
        if v is None: 
            st.markdown(f'<div class="module"><span>{name}</span><span class="module-score">Unavailable</span></div>',unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="module"><span>{name}</span><span class="module-score">{v*100:.1f}%</span></div>',unsafe_allow_html=True)
            st.progress(v)
    
    if r.get("veto_applied"): 
        st.markdown(f'<div style="background:rgba(239,68,68,.1);border-left:4px solid #fb7185;border-radius:8px;padding:1rem;margin:1rem 0;color:#fca5a5;font-weight:700">🛑 Safety Veto Applied: {r.get("veto_reason","Unknown reason")}</div>',unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📚 Evidence & Sources</div>',unsafe_allow_html=True)
    evidence=r.get("evidence") or []; sources=r.get("sources") or []
    for i,e in enumerate(evidence,1):
        st.markdown(f'<div class="evidence"><div class="evidence-title">📖 {esc(e.get("title","Untitled source"))}</div><div class="evidence-meta">Source: {esc(e.get("source","Unknown"))}</div><div class="evidence-text">{esc(e.get("snippet","No snippet available."))}</div></div>',unsafe_allow_html=True)
        if e.get("url"): st.link_button("View Source ↗",e["url"], use_container_width=True)
    
    for i,s in enumerate(sources,1):
        if s.get("url"): st.link_button(f'📌 Source {i}: {s.get("title","Source")}',s["url"], use_container_width=True)
    
    if not evidence and not sources: 
        st.markdown('<div style="text-align:center;color:#64748b;padding:2rem">📋 No external sources were retrieved for this verification.</div>',unsafe_allow_html=True)
    
    if r.get("regeneration_triggered"):
        st.markdown('<div class="section-title">✨ Regenerated Safer Response</div>',unsafe_allow_html=True)
        if r.get("regenerated_response"): 
            st.markdown(f'<div class="content-card">{esc(r["regenerated_response"]).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
        if r.get("regeneration_explanation"): 
            st.markdown(f'<div style="background:rgba(168,85,247,.1);border-left:4px solid #a78bfa;border-radius:8px;padding:1rem;margin:1rem 0;color:#cbd5e1">{esc(r["regeneration_explanation"]).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)

def stream_verify(backend,prompt,regenerate):
    area=st.empty(); statuses={}; current=None; msg="Starting verification..."; p=0; final=None
    try:
        with requests.post(f"{backend.rstrip('/')}/generate-and-verify-stream",json={"prompt":prompt,"regenerate":regenerate},stream=True,timeout=300) as resp:
            if resp.status_code==404:
                st.error("Streaming endpoint not found. Add /generate-and-verify-stream to api/main.py and restart FastAPI."); return
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line: continue
                try:event=json.loads(line)
                except:continue
                if event.get("type")=="progress":
                    current=event.get("stage",current); msg=event.get("message",""); p=int(event.get("progress",p)); statuses[current]=msg
                    with area.container(): render_pipeline(statuses,current,p,msg)
                elif event.get("type")=="complete":
                    final=event.get("result"); current="complete"; p=100
                    with area.container(): render_pipeline(statuses,current,p,"All verification stages completed.")
                elif event.get("type")=="error":
                    st.error(f'Pipeline error: {event.get("message","Unknown error")}'); return
        if final: render_results(final)
    except requests.exceptions.ConnectionError: st.error(f"Cannot connect to {backend}. Start FastAPI first.")
    except requests.exceptions.Timeout: st.error("Request timed out. Check model availability or provider quota.")
    except requests.exceptions.HTTPError as e: st.error(f"Backend HTTP error: {e}")
    except Exception as e: st.error(f"Unexpected error: {e}")

def verify_existing(backend,prompt,response,regenerate):
    try:
        with st.spinner("Running TruthGuard verification..."):
            r=requests.post(f"{backend.rstrip('/')}/verify",json={"prompt":prompt,"response":response,"regenerate":regenerate},timeout=300)
        r.raise_for_status(); render_results(r.json())
    except requests.exceptions.ConnectionError: st.error(f"Cannot connect to {backend}.")
    except requests.exceptions.Timeout: st.error("Verification timed out.")
    except requests.exceptions.HTTPError as e: st.error(f"Backend error: {e}")
    except Exception as e: st.error(f"Unexpected error: {e}")

def main():
    render_header()
    st.markdown('<div class="hero"><div class="hero-kicker">AI Trust & Verification</div><div class="hero-title">Verify before you trust.</div><div class="hero-text">TruthGuard checks AI-generated responses using consistency analysis, external evidence, independent judging and score fusion. See exactly what happens at every stage.</div></div>',unsafe_allow_html=True)

    backend="http://localhost:8000"
    
    st.markdown('<div class="section-title">Choose how you want to verify</div>',unsafe_allow_html=True)
    t1,t2=st.tabs(["🔍 Verify an Existing AI Response","✨ Generate & Verify"])

    with t1:
        st.markdown('<div class="section-text">Paste a question and an AI-generated answer to evaluate its reliability.</div>',unsafe_allow_html=True)
        a,b=st.columns(2)
        with a: prompt=st.text_area("Original question",placeholder="Example: Who was the first person to walk on the Moon?",height=210,key="existing_prompt")
        with b: response=st.text_area("AI-generated response",placeholder="Paste the response you want TruthGuard to check...",height=210,key="existing_response")
        regen=st.checkbox("Regenerate automatically if hallucination risk is high",key="existing_regenerate")
        if st.button("🔍 Verify Response",type="primary",width="stretch"):
            if not prompt.strip(): st.warning("Please enter the original question.")
            elif not response.strip(): st.warning("Please paste an AI-generated response.")
            else: verify_existing(backend,prompt,response,regen)

    with t2:
        st.markdown('<div class="section-text">Gemini generates the answer first, then TruthGuard verifies it through the complete pipeline.</div>',unsafe_allow_html=True)
        prompt=st.text_area("Your question",placeholder="Example: Explain the difference between supervised and unsupervised learning.",height=190,key="generate_prompt")
        regen=st.checkbox("Regenerate automatically if hallucination risk is high",value=False,key="generate_regenerate")
        if st.button("✨ Generate & Verify",type="primary",width="stretch"):
            if not prompt.strip(): st.warning("Please enter a question.")
            else: stream_verify(backend,prompt,regen)

    st.markdown('<div class="footer">🛡️ TruthGuard · Multi-signal AI hallucination detection<br>Transparent · Evidence-aware · Explainable</div>',unsafe_allow_html=True)

if __name__=="__main__":
    main()