"""
CrimeSense by DevWithData
Intelligent Conversational AI & Crime Analytics Platform for the KSP Crime Database
Datathon 2026 — Karnataka State Police  |  Problem Statement: Intelligent
Conversational AI for KSP Crime Database

Run locally:   streamlit run app/app.py
"""
import os, sys, datetime
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from nl_engine import NLEngine, SAMPLE_QUESTIONS
from network import build_cooffender_graph, detect_clusters, key_players
from pdf_export import conversation_to_pdf
import i18n

DB = os.environ.get("CRIMESENSE_DB",
                    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "crimesense.db"))

st.set_page_config(page_title="CrimeSense by DevWithData", page_icon="🛡️", layout="wide")

# ---------- styling ----------
st.markdown("""
<style>
  .main {background:#0f172a;}
  .stApp {background:#0f172a; color:#e2e8f0;}
  h1,h2,h3,h4 {color:#f1f5f9;}
  .brand {font-size:13px; color:#64748b; letter-spacing:1px;}
  .pill {display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:14px;
         padding:3px 10px;margin:2px;font-size:12px;color:#cbd5e1;}
  .answer {background:#11203a;border-left:4px solid #2563eb;padding:12px 16px;border-radius:8px;margin:6px 0;}
  .ev {background:#0b1626;border:1px solid #1e293b;border-radius:8px;padding:10px;font-size:13px;color:#94a3b8;}
  [data-testid="stMetricValue"] {color:#60a5fa;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    return NLEngine(DB)


@st.cache_data
def load_df(sql):
    import sqlite3
    con = sqlite3.connect(DB)
    df = pd.read_sql_query(sql, con)
    con.close()
    return df


if "history" not in st.session_state:
    st.session_state.history = []


def _plot(df, chart):
    fig, ax = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor("#0f172a"); ax.set_facecolor("#0f172a")
    x, y = chart["x"], chart["y"]
    if chart["kind"] == "line":
        ax.plot(df[x], df[y], marker="o", color="#60a5fa")
    elif chart["kind"] == "pie":
        ax.pie(df[y], labels=df[x], autopct="%1.0f%%", textprops={"color": "#e2e8f0", "fontsize": 8})
    else:
        ax.bar(df[x].astype(str), df[y], color="#2563eb")
        plt.xticks(rotation=40, ha="right", fontsize=7)
    ax.tick_params(colors="#94a3b8")
    for s in ax.spines.values(): s.set_color("#334155")
    ax.set_xlabel(x, color="#94a3b8"); ax.set_ylabel(y, color="#94a3b8")
    plt.tight_layout()
    st.pyplot(fig); plt.close(fig)

# ---------- sidebar ----------
with st.sidebar:
    st.markdown("### 🛡️ CrimeSense")
    st.markdown('<span class="brand">by DevWithData · devwithdata.in</span>', unsafe_allow_html=True)
    st.caption("Conversational Crime Intelligence for KSP")
    lang = st.radio("Language / ಭಾಷೆ", ["English", "ಕನ್ನಡ"], horizontal=True)
    L = i18n.STRINGS["kn" if lang == "ಕನ್ನಡ" else "en"]
    st.divider()
    role = st.selectbox("👤 Role-based access", ["Investigator", "Analyst", "Supervisor", "Policymaker"])
    st.caption(f"Signed in as **{role}** · audit-logged")
    st.divider()
    st.markdown("**Modules**")
    st.markdown('<span class="pill">💬 Conversational AI</span>'
                '<span class="pill">🕸️ Network Analysis</span>'
                '<span class="pill">📈 Pattern Analytics</span>'
                '<span class="pill">🎯 Offender Profiling</span>'
                '<span class="pill">💰 Financial Trails</span>'
                '<span class="pill">🔎 Explainable AI</span>', unsafe_allow_html=True)
    st.divider()
    if not os.path.exists(DB):
        st.error("Database not found. Run: python data/generate_data.py")

eng = get_engine()

st.markdown("## 🛡️ CrimeSense — Intelligent Conversational AI for KSP Crime Database")
st.caption("Datathon 2026 · Karnataka State Police  ·  *Demo runs on fully synthetic, NCRB/KSP-structured data*")

tabs = st.tabs(["💬 Conversational AI", "📈 Crime Patterns", "🕸️ Criminal Network",
                "🎯 Offender Profiling", "💰 Financial Trails", "ℹ️ About"])

# ============================================================ CONVERSATIONAL AI
with tabs[0]:
    c1, c2 = st.columns([3, 1])
    with c2:
        st.markdown("**" + L["samples"] + "**")
        picked = None
        for s in SAMPLE_QUESTIONS:
            if st.button(s, key="s_" + s, use_container_width=True):
                picked = s
        st.caption("🎙️ Voice input: supported via browser Web Speech API in the deployed build.")
    with c1:
        with st.form("ask_form", clear_on_submit=True):
            q = st.text_input(L["ask"], value=picked or "", key="qbox")
            submitted = st.form_submit_button(L["send"], type="primary")
        if (submitted and q) or picked:
            question = q or picked
            res = eng.ask(i18n.normalize_query(question))
            st.session_state.history.append({
                "q": question, "answer": res.answer, "sql": res.sql,
                "reasoning": res.reasoning, "ts": datetime.datetime.now().isoformat()})

        # render conversation (latest first)
        for turn_idx, turn in enumerate(reversed(st.session_state.history)):
            st.markdown(f"**🧑 {turn['q']}**")
            st.markdown(f'<div class="answer">🤖 {turn["answer"]}</div>', unsafe_allow_html=True)
            # re-run to show table/chart for the latest answer
            res = eng.ask(i18n.normalize_query(turn["q"]))
            if res.rows:
                df = pd.DataFrame(res.rows)
                st.dataframe(df, use_container_width=True, hide_index=True)
                if res.chart and len(df) > 1:
                    _plot(df, res.chart)
            with st.expander("🔎 " + L["evidence"]):
                for r in turn["reasoning"]:
                    st.markdown(f"- {r}")
                st.code(turn["sql"], language="sql")
            st.divider()

        if st.session_state.history:
            pdf = conversation_to_pdf(st.session_state.history)
            st.download_button("📄 " + L["export_pdf"], pdf,
                               file_name=f"CrimeSense_conversation_{datetime.date.today()}.pdf",
                               mime="application/pdf")
            if st.button("🗑️ Clear conversation"):
                st.session_state.history = []
                st.rerun()


# ============================================================ CRIME PATTERNS
with tabs[1]:
    st.markdown("### 📈 Crime Pattern & Trend Analytics")
    total = load_df("SELECT COUNT(*) c FROM fir")["c"][0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total FIRs", f"{total:,}")
    m2.metric("Districts", load_df("SELECT COUNT(DISTINCT district) c FROM fir")["c"][0])
    m3.metric("Accused", load_df("SELECT COUNT(*) c FROM accused")["c"][0])
    m4.metric("Active gangs", load_df("SELECT COUNT(DISTINCT gang) c FROM fir WHERE gang IS NOT NULL")["c"][0])

    cdist = load_df("SELECT district, COUNT(*) cases FROM fir GROUP BY district ORDER BY cases DESC")
    cyear = load_df("SELECT year, COUNT(*) cases FROM fir GROUP BY year ORDER BY year")
    ctype = load_df("SELECT crime_type, COUNT(*) cases FROM fir GROUP BY crime_type ORDER BY cases DESC LIMIT 12")
    cmonth = load_df("SELECT month, COUNT(*) cases FROM fir GROUP BY month ORDER BY month")

    a, b = st.columns(2)
    with a:
        st.markdown("**Hotspots — FIRs by district**")
        st.bar_chart(cdist.set_index("district"))
    with b:
        st.markdown("**Yearly trend**")
        st.line_chart(cyear.set_index("year"))
    c, d = st.columns(2)
    with c:
        st.markdown("**Top crime types**")
        st.bar_chart(ctype.set_index("crime_type"))
    with d:
        st.markdown("**Seasonality (by month)** — note festival-season property-crime uptick")
        st.line_chart(cmonth.set_index("month"))

# ============================================================ NETWORK
with tabs[2]:
    st.markdown("### 🕸️ Criminal Network & Relationship Analysis")
    st.caption("Co-offending graph: nodes = accused, edges = shared FIRs. Communities ≈ organised-crime cells.")
    G, names, gangmap = build_cooffender_graph(DB)
    clusters = detect_clusters(G)
    kp = key_players(G)
    m1, m2, m3 = st.columns(3)
    m1.metric("Linked offenders", G.number_of_nodes())
    m2.metric("Relationships", G.number_of_edges())
    m3.metric("Detected cells", len(clusters))

    if G.number_of_edges() > 0:
        fig, ax = plt.subplots(figsize=(9, 6))
        fig.patch.set_facecolor("#0f172a"); ax.set_facecolor("#0f172a")
        pos = nx.spring_layout(G, k=0.5, seed=42)
        gangs = sorted({gangmap.get(n) for n in G.nodes if gangmap.get(n)})
        palette = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#a855f7"]
        cmap = {g: palette[i % len(palette)] for i, g in enumerate(gangs)}
        colors_n = [cmap.get(gangmap.get(n), "#64748b") for n in G.nodes]
        sizes = [200 + 600 * c for n, c in nx.betweenness_centrality(G).items()]
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#334155", width=0.6, alpha=0.6)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colors_n, node_size=sizes, alpha=0.9)
        ax.axis("off")
        st.pyplot(fig); plt.close(fig)
        st.markdown("**Key players (betweenness centrality — likely kingpins/connectors):**")
        st.dataframe(pd.DataFrame([{"Accused": names.get(n, n), "ID": n, "Centrality": s} for n, s in kp]),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No co-offending edges in current sample.")

# ============================================================ OFFENDER PROFILING
with tabs[3]:
    st.markdown("### 🎯 Criminology-Based Offender Profiling & Risk Scoring")
    off = load_df("""SELECT a.accused_id, a.name, a.age, a.gender, a.district, a.occupation,
                     a.education, COUNT(af.fir_id) linked_cases, a.prior_cases
                     FROM accused a JOIN accused_fir af ON a.accused_id=af.accused_id
                     GROUP BY a.accused_id ORDER BY linked_cases DESC LIMIT 25""")
    off["risk_score"] = (off["linked_cases"] * 12 + off["prior_cases"] * 6).clip(upper=100)
    off["risk_band"] = pd.cut(off["risk_score"], [-1, 30, 60, 200],
                              labels=["🟢 Low", "🟡 Medium", "🔴 High"])
    st.caption("Risk score = 12 × linked cases + 6 × prior cases (capped at 100). Transparent & explainable.")
    st.dataframe(off[["name", "age", "gender", "district", "occupation", "education",
                      "linked_cases", "prior_cases", "risk_score", "risk_band"]],
                 use_container_width=True, hide_index=True)
    st.markdown("**Socio-demographic insight**")
    a, b = st.columns(2)
    with a:
        st.markdown("Accused by age band")
        ages = load_df("""SELECT CASE WHEN age<25 THEN '18-24' WHEN age<35 THEN '25-34'
                          WHEN age<45 THEN '35-44' ELSE '45+' END band, COUNT(*) n
                          FROM accused GROUP BY band ORDER BY band""")
        st.bar_chart(ages.set_index("band"))
    with b:
        st.markdown("Accused by education")
        edu = load_df("SELECT education, COUNT(*) n FROM accused GROUP BY education ORDER BY n DESC")
        st.bar_chart(edu.set_index("education"))

# ============================================================ FINANCIAL
with tabs[4]:
    st.markdown("### 💰 Financial Crime & Transaction Link Analysis")
    fin = load_df("""SELECT t.fir_id, f.crime_type, f.district, COUNT(*) hops,
                     SUM(t.amount) total_amount, SUM(t.flagged) flagged
                     FROM transactions t JOIN fir f ON t.fir_id=f.fir_id
                     GROUP BY t.fir_id ORDER BY total_amount DESC LIMIT 15""")
    m1, m2 = st.columns(2)
    m1.metric("Tracked transactions", load_df("SELECT COUNT(*) c FROM transactions")["c"][0])
    m2.metric("Flagged (suspicious)", load_df("SELECT COUNT(*) c FROM transactions WHERE flagged=1")["c"][0])
    st.markdown("**Top money-trail cases (multi-hop transfers)**")
    st.dataframe(fin, use_container_width=True, hide_index=True)
    pick = st.selectbox("Trace money trail for FIR", fin["fir_id"].tolist())
    trail = load_df(f"SELECT from_account, to_account, amount, channel, flagged FROM transactions WHERE fir_id='{pick}'")
    st.markdown(f"**Transaction chain for {pick}**")
    st.dataframe(trail, use_container_width=True, hide_index=True)
    Gt = nx.DiGraph()
    for _, r in trail.iterrows():
        Gt.add_edge(r["from_account"], r["to_account"], amount=r["amount"])
    if Gt.number_of_edges():
        fig, ax = plt.subplots(figsize=(8, 2.6))
        fig.patch.set_facecolor("#0f172a"); ax.set_facecolor("#0f172a")
        pos = nx.spring_layout(Gt, seed=1)
        nx.draw_networkx(Gt, pos, ax=ax, node_color="#f59e0b", edge_color="#ef4444",
                         font_size=7, node_size=700, font_color="#0f172a")
        ax.axis("off"); st.pyplot(fig); plt.close(fig)

# ============================================================ ABOUT
with tabs[5]:
    st.markdown("""
### About CrimeSense
**CrimeSense by DevWithData** is an Intelligent Conversational AI & Crime Analytics platform
built for the **Karnataka State Police Datathon 2026**.

It lets investigators, analysts and policymakers **query the crime database in plain English or
Kannada** and get answers backed by a transparent **evidence trail** (the exact SQL + reasoning),
plus advanced analytics for **crime patterns, criminal networks, offender risk-scoring and
financial money-trails**.

**Explainable by design** — every AI answer shows the data references and reasoning path used.
**Privacy-first** — this prototype runs on **fully synthetic, NCRB/KSP-structured data**; no real
personal records are used. Role-based access and audit logging are built into the access model.

Deployable on **Catalyst by Zoho** (AppSail Python runtime + Data Store + QuickML for forecasting).

*Built by Shashikant · devwithdata.in*
""")
