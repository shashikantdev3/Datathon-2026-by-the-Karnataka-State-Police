# Datathon 2026 (Karnataka State Police) — Submission Guide & Rules

_Research compiled for **CrimeSense by DevWithData** · Problem Statement: Intelligent Conversational AI for KSP Crime Database._

## 1. What this challenge is

Datathon 2026 is a national innovation challenge run by the **Karnataka State Police (KSP)** with **Hack2skill**, and **powered by Catalyst by Zoho** as the deployment platform. Participants build data-driven, AI solutions that strengthen public safety and law-enforcement decision-making. It is the successor to the earlier KSP Hackathon/Datathon editions (2023, 2024).

## 2. Timeline (as on the roadmap)

| Stage | Window (IST) | Notes |
|---|---|---|
| Registration | 25 May 2026, 4:00 PM → 19 Jul 2026, 11:59 PM | You are registered |
| Team Formation | 25 May 2026 → 19 Jul 2026 | Solo team allowed |
| **Prototype Submissions** | 28 May 2026, 4:00 PM → **26 Jul 2026, 11:59 PM** | Current stage |

> Always re-check the live countdown on the Hack2skill dashboard — deadlines can be extended/shortened by organizers.

## 3. What you must submit (Prototype stage)

Per the official Submission Guidelines, every team submits:

1. **Prototype Brief** — concise overview: problem statement addressed, key features & functionalities, technology stack, proposed impact & use case.
2. **Public GitHub Repository** — complete source code, a proper README, and setup/execution instructions. Must be publicly accessible.
3. **Demo Video Link (≈3 minutes)** — public Google Drive (public access enabled) **or** an unlisted/accessible YouTube link. Must show: problem-statement overview, working prototype demonstration, key functionalities & workflows.
4. **Deployed Solution Link** — a live deployment. **Deployment must be on the Catalyst (by Zoho) platform to qualify for evaluation.**
5. **Official Submission Template** — fill and submit the organizer-provided PPT template (this is the file `KSP Datathon 2026 _ Prototype Submission Template.pptx`). Submissions in other formats may not be considered.

### Completeness rules
- All links must be working and publicly accessible before final submission.
- Incomplete or inaccessible submissions may lead to disqualification.
- Use the official template — non-template submissions may be rejected.

## 4. Catalyst by Zoho — deployment notes (mandatory platform)

Catalyst is a full-stack serverless cloud platform. Relevant services for this solution:

- **AppSail** — serverless app hosting with platform-managed runtimes (Java, **Python**, Node.js) or custom OCI images. We host the Streamlit web app here (Python runtime).
- **Data Store** — serverless relational database with a built-in OLAP engine for analytical queries — natural home for the crime/FIR tables in production.
- **Catalyst Functions (FaaS)** — microservices for the NL-query engine and PDF export.
- **QuickML** — no-code ML pipeline builder (regression/classification) — used for crime forecasting & offender risk-scoring models.
- **Authentication** — for role-based access (investigator / analyst / supervisor / policymaker).
- **Stratus / File Store** — object storage for exported conversation PDFs and case files.

**Deployment quick path (CLI):** install the Catalyst CLI (`npm install -g zcatalyst-cli`), `catalyst login`, `catalyst init` (choose AppSail), point the stack to Python and the start command to launch Streamlit on `$X_ZOHO_CATALYST_LISTEN_PORT`, then `catalyst deploy`. See `catalyst.json` / `app-config.json` in this repo and `README.md` for the exact command.

> Sign up for Catalyst and explore QuickML + AppSail early — first-time deployment always has environment quirks. The free developer tier is sufficient for the prototype.

## 5. How evaluation typically weighs (inferred — confirm on dashboard)

Police/data hackathons of this type generally reward:
- **Relevance to the problem statement & policing impact** (does it actually help investigators?)
- **Working prototype** (not just slides) — the deployed link and demo video matter.
- **Technical depth** — NLP, network analysis, analytics, ML.
- **Explainability, security & governance** — critical for law enforcement (audit logs, evidence trails, data protection).
- **Innovation / USP** and **scalability** on Catalyst.

## 6. Responsible-AI & data notes (important for a policing solution)

- This prototype runs on **fully synthetic data** modelled on NCRB crime heads + KSP FIR structure. **No real personal data** is used — call this out explicitly in the deck and demo.
- Emphasize **human-in-the-loop**: outputs are investigative *leads*, not verdicts. Risk scores and predictions assist prioritization; they do not establish guilt.
- Highlight **bias-awareness, audit logging, role-based access, and the explainable evidence trail** — these are differentiators with a police evaluator.

## 7. Final submission checklist

- [ ] GitHub repo public, with README + setup/run/deploy steps
- [ ] App deployed on **Catalyst** — live link working
- [ ] 3-minute demo video uploaded (public Drive / unlisted YouTube), link working
- [ ] Official PPT template filled (all slides) and exported to PDF if required
- [ ] Prototype brief written (problem, features, stack, impact)
- [ ] All links tested in an incognito window for public access
- [ ] Team details correct: **Team name: CrimeSense by DevWithData**, Leader: Shashikant, Size: 1

## Sources
- [Datathon 2026 — Hack2skill event page](https://hack2skill.com/event/datathon2026)
- [Catalyst by Zoho — Serverless / AppSail docs](https://docs.catalyst.zoho.com/en/serverless/getting-started/introduction/)
- [Catalyst Data Store docs](https://docs.catalyst.zoho.com/en/cloud-scale/help/data-store/introduction/)
- [Catalyst QuickML docs](https://docs.catalyst.zoho.com/en/quickml/getting-started/why-quickml/)
- [Prior KSP Hackathon (2023) submission repo](https://github.com/hack2skill/ksp-submission)
