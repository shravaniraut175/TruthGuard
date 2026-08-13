import json
import html
import requests
import streamlit as st

st.set_page_config(
    page_title="TruthGuard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp{background:#070b12}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1180px;padding-top:1.7rem;padding-bottom:3rem}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem}
.brand{display:flex;align-items:center;gap:13px}
.logo{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#2563eb,#7c3aed);font-size:23px}
.brand-title{color:#f8fafc;font-size:1.55rem;font-weight:800}
.brand-subtitle{color:#718096;font-size:.76rem}
.online{border:1px solid #21412f;background:#0b1711;color:#4ade80;border-radius:999px;padding:7px 12px;font-size:.78rem;font-weight:700}
.hero{border:1px solid #202a3b;border-radius:24px;padding:34px 38px;background:radial-gradient(circle at 82% 15%,rgba(124,58,237,.18),transparent 30%),radial-gradient(circle at 12% 95%,rgba(37,99,235,.13),transparent 34%),#0c121c;margin-bottom:25px}
.hero-kicker{color:#8ea7ff;font-size:.76rem;text-transform:uppercase;letter-spacing:1.4px;font-weight:800}
.hero-title{color:#f8fafc;font-size:2.45rem;line-height:1.1;font-weight:850;letter-spacing:-1.2px;margin-top:8px}
.hero-text{color:#8f9bad;font-size:.98rem;line-height:1.65;max-width:790px;margin-top:12px}
.section-title{color:#eef2f7;font-size:1.18rem;font-weight:800;margin:28px 0 5px}
.section-text{color:#758196;font-size:.84rem;margin-bottom:14px}
div[data-testid="stTextArea"] textarea{background:#0b111a!important;border:1px solid #253146!important;border-radius:13px!important;color:#edf2f7!important}
div[data-testid="stTextArea"] textarea:focus{border-color:#4f72ff!important;box-shadow:0 0 0 1px #4f72ff!important}
div.stButton>button,div.stLinkButton>a{border-radius:11px!important;min-height:44px!important;font-weight:750!important}
div.stButton>button[kind="primary"]{background:linear-gradient(135deg,#2563eb,#6848e8)!important;border:0!important;color:white!important}
.pipeline-box{background:#0b111a;border:1px solid #202a3b;border-radius:20px;padding:20px;margin:18px 0 22px}
.pipeline-heading{color:#f1f5f9;font-size:1rem;font-weight:800;margin-bottom:13px}
.stage{display:flex;align-items:center;gap:13px;padding:11px 12px;margin:6px 0;border-radius:12px;border:1px solid #1c2636;background:#0e141f}
.stage-icon{width:29px;height:29px;min-width:29px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.78rem}
.done .stage-icon{background:rgba(34,197,94,.13);color:#4ade80}
.active .stage-icon{background:rgba(59,130,246,.14);color:#60a5fa}
.waiting .stage-icon{background:#171f2d;color:#59667b}
.stage-body{flex:1}.stage-name{color:#dfe6f0;font-size:.86rem;font-weight:700}.stage-message{color:#6f7c90;font-size:.74rem;margin-top:2px}.stage-status{color:#667388;font-size:.72rem}
.metric{background:#0e141f;border:1px solid #202a3b;border-radius:17px;padding:18px;min-height:112px}
.metric-label{color:#78869a;text-transform:uppercase;letter-spacing:.8px;font-size:.71rem;font-weight:800}
.metric-value{color:#f8fafc;font-size:1.9rem;font-weight:850;margin-top:8px}.metric-help{color:#59667a;font-size:.72rem}
.risk{border-radius:15px;padding:15px 18px;text-align:center;font-weight:850;letter-spacing:.5px;margin:17px 0;border:1px solid}
.low{color:#4ade80;background:rgba(34,197,94,.08);border-color:rgba(34,197,94,.25)}
.medium{color:#fbbf24;background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.25)}
.high{color:#fb7185;background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.25)}
.critical{color:#fca5a5;background:rgba(127,29,29,.18);border-color:rgba(239,68,68,.35)}
.unknown{color:#cbd5e1;background:rgba(100,116,139,.08);border-color:rgba(100,116,139,.22)}
.content-card{background:#0e141f;border:1px solid #202a3b;border-radius:17px;padding:19px 20px;color:#c3cedd;line-height:1.7}
.module{background:#0e141f;border:1px solid #202a3b;border-radius:13px;padding:14px 17px;margin:8px 0;color:#dce3ee}.module-score{float:right;color:#aebbd0;font-weight:750}
.evidence{background:#0e141f;border:1px solid #202a3b;border-radius:15px;padding:16px 18px;margin:9px 0}
.evidence-title{color:#e7edf5;font-weight:750;font-size:.9rem}.evidence-meta{color:#657389;font-size:.72rem;margin:4px 0 9px}.evidence-text{color:#aeb9c9;font-size:.82rem;line-height:1.55}
.footer{color:#4e5b6e;text-align:center;font-size:.72rem;margin-top:42px;padding-top:18px;border-top:1px solid #182131}
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
    a,b=st.columns([4,1])
    with a:
        st.markdown('<div class="topbar"><div class="brand"><div class="logo">🛡️</div><div><div class="brand-title">TruthGuard</div><div class="brand-subtitle">AI response verification & hallucination detection</div></div></div></div>',unsafe_allow_html=True)
    with b: st.markdown('<div style="text-align:right;margin-top:8px"><span class="online">● System Ready</span></div>',unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Verification Result</div>',unsafe_allow_html=True)
    risk=str(r.get("risk_level","unknown")).lower()
    if risk not in {"low","medium","high","critical"}: risk="unknown"
    st.markdown(f'<div class="risk {risk}">{"✓" if risk=="low" else "⚠"} {risk.upper()} HALLUCINATION RISK</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    with a: metric("Truth Score",pct(r.get("truth_score")),"Higher is better")
    with b: metric("Confidence",pct(r.get("confidence_score")),"Combined confidence")
    with c: metric("Hallucination Probability",pct(r.get("hallucination_probability")),"Lower is better")
    response=r.get("response") or r.get("generated_response","")
    st.markdown('<div class="section-title">AI Response</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="content-card">{esc(response).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Why TruthGuard gave this result</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="content-card">{esc(r.get("explanation","No explanation available.")).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
    if r.get("grounding_explanation"): st.info(r["grounding_explanation"])
    st.markdown('<div class="section-title">Detection Modules</div>',unsafe_allow_html=True)
    for name,key in [("Black-box Consistency","blackbox"),("White-box Token Confidence","whitebox"),("LLM-as-a-Judge","judge"),("External Grounding","grounding")]:
        v=score((r.get("module_scores") or {}).get(key))
        if v is None: st.markdown(f'<div class="module">{name}<span class="module-score">Unavailable</span></div>',unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="module">{name}<span class="module-score">{v*100:.1f}%</span></div>',unsafe_allow_html=True); st.progress(v)
    if r.get("veto_applied"): st.warning(f'Safety veto applied: {r.get("veto_reason","Unknown reason")}')
    st.markdown('<div class="section-title">Evidence & Sources</div>',unsafe_allow_html=True)
    evidence=r.get("evidence") or []; sources=r.get("sources") or []
    for i,e in enumerate(evidence,1):
        st.markdown(f'<div class="evidence"><div class="evidence-title">🔎 {i}. {esc(e.get("title","Untitled source"))}</div><div class="evidence-meta">{esc(e.get("source","Unknown source"))}</div><div class="evidence-text">{esc(e.get("snippet","No evidence snippet available."))}</div></div>',unsafe_allow_html=True)
        if e.get("url"): st.link_button("Open source ↗",e["url"])
    for i,s in enumerate(sources,1):
        if s.get("url"): st.link_button(f'{i}. {s.get("title","Source")} ↗',s["url"])
    if not evidence and not sources: st.caption("No external sources were returned.")
    if r.get("regeneration_triggered"):
        st.markdown('<div class="section-title">🔄 Safer Regenerated Response</div>',unsafe_allow_html=True)
        if r.get("regenerated_response"): st.markdown(f'<div class="content-card">{esc(r["regenerated_response"]).replace(chr(10),"<br>")}</div>',unsafe_allow_html=True)
        if r.get("regeneration_explanation"): st.info(r["regeneration_explanation"])

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

    with st.expander("⚙️ Connection settings",expanded=False):
        backend=st.text_input("FastAPI backend URL",value="http://localhost:8000")
        if st.button("Check backend"):
            try:
                h=requests.get(f"{backend.rstrip('/')}/health",timeout=5)
                st.success("TruthGuard backend is online.") if h.ok else st.warning(f"Backend returned HTTP {h.status_code}.")
            except: st.error("Backend is not reachable.")

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