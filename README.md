# 🛡️ CrimeSense by DevWithData
### Intelligent Conversational AI & Crime Analytics Platform for the KSP Crime Database

> **Datathon 2026 — Karnataka State Police** · Problem Statement: *Intelligent Conversational AI for KSP Crime Database*
> Team: **CrimeSense by DevWithData** · Leader: Shashikant · Size: 1 · [devwithdata.in](https://devwithdata.in)

CrimeSense lets investigators, analysts and policymakers **query the crime database in plain English or Kannada** and get answers backed by a transparent **evidence trail** (the exact SQL + reasoning), plus advanced analytics for crime patterns, criminal networks, offender risk-scoring and financial money-trails.

> ⚠️ **Data disclaimer:** This prototype runs on **fully synthetic data** modelled on NCRB crime heads and KSP FIR structure (Karnataka districts, IPC/special-act sections). **No real personal data is used.**

---

## ✨ Features (mapped to the problem statement)

| # | Module | What it does |
|---|---|---|
| 1 | **Conversational Crime Intelligence** | NL → SQL chatbot over FIRs/accused/victims/locations. Context-aware follow-ups, **English + Kannada**, voice-ready, **export conversation to PDF**. |
| 2 | **Criminal Network Analysis** | Co-offending graph (networkx), community detection for organised-crime cells, betweenness centrality to surface kingpins. |
| 3 | **Crime Pattern & Trend Analytics** | Hotspots by district, yearly trend, seasonality (festival-season uptick), crime-type breakdown. |
| 4 | **Sociological Insights** | Accused distribution by age band, education, occupation. |
| 5 | **Offender Profiling & Risk Scoring** | Repeat-offender detection + transparent risk score `= 12·linked_cases + 6·prior_cases` (capped 100). |
| 6 | **Investigator Decision Support** | Case summaries, investigation status, similar-case retrieval. |
| 7 | **Financial Crime & Money-Trail** | Multi-hop transaction tracing, suspicious-transaction flagging, money-flow graph. |
| 8 | **Crime Forecasting** | Trend/seasonality signals; designed for Catalyst **QuickML** models in production. |
| 9 | **Explainable AI** | Every answer shows the data references, reasoning steps and the SQL executed. |
| 10 | **Secure Role-Based Access** | Investigator / Analyst / Supervisor / Policymaker roles with audit logging. |

---

## 🏗️ Architecture

```
                ┌─────────────────────────────────────────────┐
   User (EN/KN, │   Streamlit Web UI  (Catalyst AppSail)        │
   voice/text)  │   chat · analytics · network · profiling      │
                └───────────────┬─────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────────┐
          ▼                     ▼                         ▼
   NL-to-SQL Engine      Analytics / networkx       PDF Export (reportlab)
   (explainable,         (patterns, graphs,         (conversation history)
    read-only SQL)        risk scoring)
          │                     │                         │
          └─────────────────────┴─────────────────────────┘
                                │
                     Crime Data Store (SQLite → Catalyst Data Store / OLAP)
                     fir · accused · victims · transactions · case_log
```

## 🧰 Tech stack

Python · Streamlit · SQLite (→ Catalyst Data Store in prod) · networkx · matplotlib · pandas · reportlab · Faker.
Deployment: **Catalyst by Zoho** (AppSail Python runtime; Data Store, Functions, QuickML, Auth).

---

## 🚀 Run locally

```bash
# 1. install
pip install -r requirements.txt

# 2. generate the synthetic crime database (creates data/crimesense.db)
python data/generate_data.py

# 3. launch
streamlit run app/app.py
# open http://localhost:9000
```

## ☁️ Deploy on Catalyst (required for evaluation)

```bash
npm install -g zcatalyst-cli
catalyst login
catalyst init            # choose AppSail → Python stack
catalyst deploy          # uses app-config.json / catalyst.json
```
The AppSail start command launches Streamlit on Catalyst's injected port:
```
streamlit run app/app.py --server.port $X_ZOHO_CATALYST_LISTEN_PORT --server.address 0.0.0.0 --server.headless true
```
See `docs/SUBMISSION_GUIDE.md` for the full submission checklist and Catalyst service mapping.

---

## 📁 Project structure

```
.
├── app/
│   ├── app.py            # Streamlit UI (6 modules)
│   ├── nl_engine.py      # explainable NL → SQL engine (offline, read-only)
│   ├── network.py        # criminal-network graph + community/centrality
│   ├── pdf_export.py     # conversation → PDF
│   └── i18n.py           # English / Kannada strings + KN query normalisation
├── data/
│   ├── generate_data.py  # synthetic NCRB/KSP-style data generator
│   └── crimesense.db     # generated SQLite DB
├── assets/               # prototype screenshots (used in the deck)
├── docs/
│   ├── SUBMISSION_GUIDE.md
│   └── make_screens_mpl.py
├── catalyst.json, app-config.json   # Catalyst deployment config
├── requirements.txt
└── README.md
```

## 🔐 Responsible AI
Outputs are investigative **leads, not verdicts** — human-in-the-loop by design. Explainable evidence trails, role-based access and audit logging support law-enforcement accountability. Synthetic data only.

---
_Built by Shashikant · devwithdata.in_
