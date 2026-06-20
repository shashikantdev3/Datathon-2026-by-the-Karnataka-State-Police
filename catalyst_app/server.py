"""
CrimeSense by DevWithData — Catalyst-deployable Flask edition
-------------------------------------------------------------
Server-rendered version of the CrimeSense platform that depends on ONLY Flask
(pure-Python) so it vendors cleanly and runs on Catalyst AppSail's managed
Python runtime. Charts/graphs are hand-rendered as inline SVG (no pandas /
matplotlib / numpy). The conversational NL->SQL engine is reused unchanged.

Run locally:   python server.py        (http://localhost:9000)
On Catalyst:   startup command = python3 -u server.py
"""
import os, sqlite3, math, html
from flask import Flask, request, redirect, url_for, session
from nl_engine import NLEngine, SAMPLE_QUESTIONS
import i18n

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "crimesense.db")

app = Flask(__name__)
app.secret_key = os.getenv("CRIMESENSE_SECRET", "crimesense-devwithdata-demo")
engine = NLEngine(DB)

# ----------------------------------------------------------------- helpers
def q(sql, params=()):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute(sql, params).fetchall(); con.close()
    return rows

def esc(s): return html.escape(str(s))

CSS = """
*{box-sizing:border-box;font-family:'Segoe UI',Arial,sans-serif}
body{margin:0;background:#0f172a;color:#e2e8f0}
a{color:#93c5fd;text-decoration:none}
.bar{background:#0b1220;border-bottom:1px solid #1e293b;padding:12px 24px;display:flex;align-items:center;gap:14px}
.logo{width:16px;height:16px;background:#2563eb;border-radius:3px}
.bar h1{font-size:18px;margin:0;color:#f1f5f9}
.brand{font-size:12px;color:#64748b}
.role{margin-left:auto;font-size:12px;color:#cbd5e1}
.tabs{display:flex;gap:6px;padding:10px 24px;background:#0b1220;border-bottom:1px solid #1e293b;flex-wrap:wrap}
.tab{padding:7px 15px;border-radius:8px;background:#11203a;color:#cbd5e1;font-size:14px}
.tab.on{background:#2563eb;color:#fff}
.wrap{padding:22px 24px;max-width:1180px}
h2{color:#f1f5f9;margin:6px 0 14px}
.metrics{display:flex;gap:16px;margin:6px 0 20px;flex-wrap:wrap}
.m{background:#11203a;border:1px solid #1e293b;border-radius:10px;padding:14px 22px;min-width:150px}
.m .v{font-size:26px;color:#60a5fa;font-weight:700}.m .l{font-size:12px;color:#94a3b8}
.card{background:#11203a;border:1px solid #1e293b;border-radius:10px;padding:16px;margin:14px 0}
.answer{background:#11203a;border-left:4px solid #2563eb;padding:12px 16px;border-radius:8px;margin:8px 0}
.user{font-weight:600;color:#f1f5f9;margin-top:14px}
.ev{background:#0b1626;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;font-size:12px;color:#94a3b8;margin-top:8px}
.ev code{color:#7dd3fc;display:block;margin-top:6px;white-space:pre-wrap}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th{background:#1e293b;color:#cbd5e1;text-align:left;padding:8px 10px}
td{padding:7px 10px;border-bottom:1px solid #1e293b}
input[type=text]{width:100%;padding:11px 14px;border-radius:8px;border:1px solid #334155;background:#0b1626;color:#e2e8f0;font-size:15px}
button{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:11px 22px;font-size:15px;cursor:pointer}
.pill{display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:14px;padding:4px 11px;margin:3px 4px 3px 0;font-size:13px;color:#cbd5e1}
.sample{display:block;width:100%;text-align:left;background:#11203a;border:1px solid #1e293b;color:#cbd5e1;
        border-radius:8px;padding:9px 12px;margin:5px 0;font-size:13px;cursor:pointer}
.badge{padding:2px 9px;border-radius:10px;font-size:11px}
.hi{background:#7f1d1d;color:#fecaca}.md{background:#78350f;color:#fde68a}.lo{background:#14532d;color:#bbf7d0}
.cols{display:flex;gap:18px;flex-wrap:wrap}.cols>div{flex:1;min-width:320px}
.note{color:#64748b;font-size:12px;margin-top:18px}
"""

TABS = [("/", "Conversational AI"), ("/patterns", "Crime Patterns"),
        ("/network", "Criminal Network"), ("/offenders", "Offender Profiling"),
        ("/financial", "Financial Trails"), ("/about", "About")]

def page(active, body):
    tabs = "".join(
        f'<a class="tab {"on" if p==active else ""}" href="{p}">{esc(t)}</a>' for p, t in TABS)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CrimeSense by DevWithData</title>
<style>{CSS}</style></head><body>
<div class="bar"><div class="logo"></div><h1>CrimeSense</h1>
<span class="brand">by DevWithData · devwithdata.in</span>
<span class="role">Investigator · audit-logged · EN/Kannada</span></div>
<div class="tabs">{tabs}</div><div class="wrap">{body}</div>
<div class="wrap note">Prototype on fully synthetic, NCRB/KSP-structured data — no real personal data.
Deployed on Catalyst by Zoho (AppSail).</div></body></html>"""

# ----------------------------------------------------------------- SVG charts
def svg_bars(pairs, color="#2563eb", w=860, h=300, title=""):
    if not pairs: return ""
    pad_l, pad_b, pad_t = 40, 70, 26
    mx = max(v for _, v in pairs) or 1
    n = len(pairs); bw = (w - pad_l - 10) / n
    bars = ""
    for i, (lab, v) in enumerate(pairs):
        bh = (h - pad_b - pad_t) * v / mx
        x = pad_l + i * bw + bw * 0.12; y = h - pad_b - bh
        bars += f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*0.76:.1f}" height="{bh:.1f}" fill="{color}" rx="3"/>'
        bars += f'<text x="{x+bw*0.38:.1f}" y="{y-5:.1f}" fill="#94a3b8" font-size="10" text-anchor="middle">{v}</text>'
        lab = esc(lab if len(str(lab)) <= 14 else str(lab)[:13] + "…")
        bars += (f'<text x="{x+bw*0.38:.1f}" y="{h-pad_b+14:.1f}" fill="#94a3b8" font-size="10" '
                 f'text-anchor="end" transform="rotate(-30 {x+bw*0.38:.1f} {h-pad_b+14:.1f})">{lab}</text>')
    t = f'<text x="{pad_l}" y="16" fill="#e2e8f0" font-size="13">{esc(title)}</text>' if title else ""
    return f'<svg viewBox="0 0 {w} {h}" width="100%" style="background:#0f172a;border-radius:8px">{t}{bars}</svg>'

def svg_line(pairs, color="#60a5fa", w=520, h=240, title=""):
    if not pairs: return ""
    pad_l, pad_b, pad_t = 38, 40, 26
    mx = max(v for _, v in pairs) or 1; mn = min(v for _, v in pairs)
    n = len(pairs); span = (w - pad_l - 14)
    def X(i): return pad_l + span * (i / max(1, n - 1))
    def Y(v): return h - pad_b - (h - pad_b - pad_t) * ((v - mn) / max(1, (mx - mn)))
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, (_, v) in enumerate(pairs))
    dots = "".join(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="{color}"/>' for i, (_, v) in enumerate(pairs))
    labs = "".join(f'<text x="{X(i):.1f}" y="{h-pad_b+16:.1f}" fill="#94a3b8" font-size="10" text-anchor="middle">{esc(l)}</text>'
                   for i, (l, _) in enumerate(pairs))
    t = f'<text x="{pad_l}" y="16" fill="#e2e8f0" font-size="13">{esc(title)}</text>' if title else ""
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" style="background:#0f172a;border-radius:8px">{t}'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>{dots}{labs}</svg>')

def svg_network(nodes, edges, groups, w=760, h=460):
    # pure-python circular-by-cluster layout (no numpy)
    pos = {}
    comps = list(groups)
    ncomp = len(comps) or 1
    for ci, comp in enumerate(comps):
        cx = w * (0.2 + 0.6 * ((ci % 3) / 2)) if ncomp > 1 else w / 2
        cy = h * (0.25 + 0.5 * (ci // 3) / max(1, (ncomp - 1) // 3 + 0)) if ncomp > 3 else h / 2
        r = 60 + 8 * math.sqrt(len(comp))
        for k, nid in enumerate(sorted(comp)):
            a = 2 * math.pi * k / max(1, len(comp))
            pos[nid] = (cx + r * math.cos(a), cy + r * math.sin(a))
    palette = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#a855f7", "#64748b"]
    gcolor = {}
    gangs = sorted({g for g in nodes.values() if g})
    for i, g in enumerate(gangs):
        gcolor[g] = palette[i % len(palette)]
    els = ""
    for a, b in edges:
        if a in pos and b in pos:
            x1, y1 = pos[a]; x2, y2 = pos[b]
            els += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#334155" stroke-width="0.7"/>'
    for nid, (x, y) in pos.items():
        c = gcolor.get(nodes.get(nid), "#64748b")
        els += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{c}" opacity="0.9"/>'
    return f'<svg viewBox="0 0 {w} {h}" width="100%" style="background:#0f172a;border-radius:8px">{els}</svg>'

def table(cols, rows, cells=None):
    head = "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in (cells(r) if cells else [esc(r[k]) for k in cols])) + "</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"

# ----------------------------------------------------------------- routes
@app.route("/", methods=["GET", "POST"])
def chat():
    if "hist" not in session: session["hist"] = []
    if request.method == "POST":
        ques = (request.form.get("q") or "").strip()
        if ques == "__clear__":
            session["hist"] = []
        elif ques:
            h = session["hist"]; h.append(ques); session["hist"] = h[-8:]
        return redirect(url_for("chat"))

    samples = "".join(f'<form method="post" style="margin:0"><input type="hidden" name="q" value="{esc(s)}">'
                      f'<button class="sample" type="submit">{esc(s)}</button></form>' for s in SAMPLE_QUESTIONS)
    convo = ""
    eng = NLEngine(DB)  # fresh context per render of the whole thread
    for ques in session.get("hist", []):
        res = eng.ask(i18n.normalize_query(ques))
        convo += f'<div class="user">🧑 {esc(ques)}</div>'
        convo += f'<div class="answer">🤖 {esc(res.answer).replace("**","")}</div>'
        if res.rows:
            cols = list(res.rows[0].keys())
            convo += table(cols, res.rows, cells=lambda r: [esc(r[c]) for c in cols])
            if res.chart and len(res.rows) > 1:
                pairs = [(r[res.chart["x"]], r[res.chart["y"]]) for r in res.rows]
                convo += (svg_line(pairs, title="") if res.chart["kind"] == "line"
                          else svg_bars(pairs, title=""))
        reasoning = "".join(f"<div>• {esc(x)}</div>" for x in res.reasoning)
        convo += f'<div class="ev"><b>Explainable AI — evidence trail</b>{reasoning}<code>{esc(res.sql)}</code></div>'
    clearbtn = ('<form method="post" style="margin-top:10px"><input type="hidden" name="q" value="__clear__">'
                '<button type="submit" style="background:#334155">Clear conversation</button></form>') if session.get("hist") else ""
    body = f"""
    <h2>Conversational Crime Intelligence</h2>
    <div class="cols">
      <div>
        <form method="post"><input type="text" name="q" autofocus
          placeholder="Ask about FIRs, hotspots, gangs, offenders, money trails… (English or Kannada)">
          <div style="margin-top:10px"><button type="submit">Ask</button></div></form>
        {convo}{clearbtn}
        <div style="margin-top:16px">
          <span class="pill">Context-aware follow-ups</span>
          <span class="pill">Explainable (SQL + reasoning)</span>
          <span class="pill">English / ಕನ್ನಡ</span></div>
      </div>
      <div style="max-width:330px">
        <div class="card"><b>Try a sample question</b>{samples}</div>
      </div>
    </div>"""
    return page("/", body)

@app.route("/patterns")
def patterns():
    tot = q("SELECT COUNT(*) c FROM fir")[0]["c"]
    dis = q("SELECT COUNT(DISTINCT district) c FROM fir")[0]["c"]
    acc = q("SELECT COUNT(*) c FROM accused")[0]["c"]
    gang = q("SELECT COUNT(DISTINCT gang) c FROM fir WHERE gang IS NOT NULL")[0]["c"]
    metrics = f"""<div class="metrics">
      <div class="m"><div class="v">{tot:,}</div><div class="l">Total FIRs</div></div>
      <div class="m"><div class="v">{dis}</div><div class="l">Districts</div></div>
      <div class="m"><div class="v">{acc}</div><div class="l">Accused</div></div>
      <div class="m"><div class="v">{gang}</div><div class="l">Active gangs</div></div></div>"""
    dist = [(r["district"], r["c"]) for r in q("SELECT district,COUNT(*) c FROM fir GROUP BY district ORDER BY c DESC")]
    yr = [(r["year"], r["c"]) for r in q("SELECT year,COUNT(*) c FROM fir GROUP BY year ORDER BY year")]
    mo = [(r["month"], r["c"]) for r in q("SELECT month,COUNT(*) c FROM fir GROUP BY month ORDER BY month")]
    ty = [(r["crime_type"], r["c"]) for r in q("SELECT crime_type,COUNT(*) c FROM fir GROUP BY crime_type ORDER BY c DESC LIMIT 10")]
    body = f"""<h2>Crime Pattern & Trend Analytics</h2>{metrics}
      <div class="card"><b>Hotspots — FIRs by district</b>{svg_bars(dist)}</div>
      <div class="cols">
        <div class="card"><b>Yearly trend</b>{svg_line(yr)}</div>
        <div class="card"><b>Seasonality — festival-season uptick</b>{svg_line(mo, color="#f59e0b")}</div>
      </div>
      <div class="card"><b>Top crime types</b>{svg_bars(ty)}</div>"""
    return page("/patterns", body)

@app.route("/network")
def network():
    # build co-offending graph in pure python
    active = [r["accused_id"] for r in q(
        "SELECT accused_id,COUNT(*) c FROM accused_fir GROUP BY accused_id ORDER BY c DESC LIMIT 120")]
    keep = set(active)
    fir_acc = {}
    for r in q("SELECT accused_id,fir_id FROM accused_fir"):
        if r["accused_id"] in keep:
            fir_acc.setdefault(r["fir_id"], []).append(r["accused_id"])
    names = {r["accused_id"]: r["name"] for r in q("SELECT accused_id,name FROM accused")}
    gangmap = {}
    for r in q("SELECT af.accused_id a, f.gang g FROM accused_fir af JOIN fir f ON af.fir_id=f.fir_id WHERE f.gang IS NOT NULL"):
        gangmap[r["a"]] = r["g"]
    edges = set(); adj = {}
    for accs in fir_acc.values():
        for i in range(len(accs)):
            for j in range(i + 1, len(accs)):
                a, b = sorted((accs[i], accs[j]))
                edges.add((a, b)); adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    nodes = {n: gangmap.get(n) for n in adj}
    # connected components (BFS) = candidate cells
    seen = set(); comps = []
    for n in adj:
        if n in seen: continue
        stack = [n]; comp = set()
        while stack:
            x = stack.pop()
            if x in seen: continue
            seen.add(x); comp.add(x); stack.extend(adj.get(x, []))
        if len(comp) >= 2: comps.append(comp)
    # key players = highest degree
    deg = sorted(adj.items(), key=lambda kv: len(kv[1]), reverse=True)[:8]
    metrics = f"""<div class="metrics">
      <div class="m"><div class="v">{len(adj)}</div><div class="l">Linked offenders</div></div>
      <div class="m"><div class="v">{len(edges)}</div><div class="l">Relationships</div></div>
      <div class="m"><div class="v">{len(comps)}</div><div class="l">Detected cells</div></div></div>"""
    kp = "".join(f"<tr><td>{esc(names.get(n,n))}</td><td>{esc(n)}</td><td>{len(d)}</td></tr>" for n, d in deg)
    body = f"""<h2>Criminal Network & Relationship Analysis</h2>{metrics}
      <div class="cols">
        <div class="card" style="flex:2"><b>Co-offending graph</b> <span style="color:#94a3b8;font-size:12px">(colour = gang)</span>
          {svg_network(nodes, edges, comps)}</div>
        <div class="card"><b>Key players (by connections)</b>
          <table><tr><th>Accused</th><th>ID</th><th>Links</th></tr>{kp}</table></div>
      </div>"""
    return page("/network", body)

@app.route("/offenders")
def offenders():
    rows = q("""SELECT a.name,a.age,a.gender,a.district,a.occupation,a.education,
                COUNT(af.fir_id) lc, a.prior_cases pc
                FROM accused a JOIN accused_fir af ON a.accused_id=af.accused_id
                GROUP BY a.accused_id ORDER BY lc DESC LIMIT 15""")
    def cells(r):
        risk = min(100, r["lc"] * 12 + r["pc"] * 6)
        band = ('<span class="badge hi">HIGH</span>' if risk > 60 else
                '<span class="badge md">MEDIUM</span>' if risk > 30 else '<span class="badge lo">LOW</span>')
        return [esc(r["name"]), esc(r["age"]), esc(r["district"]), esc(r["occupation"]),
                esc(r["education"]), esc(r["lc"]), esc(r["pc"]), risk, band]
    tbl = table(["Name", "Age", "District", "Occupation", "Education", "Linked", "Priors", "Risk", "Band"], rows, cells)
    ages = [(r["b"], r["n"]) for r in q("""SELECT CASE WHEN age<25 THEN '18-24' WHEN age<35 THEN '25-34'
            WHEN age<45 THEN '35-44' ELSE '45+' END b,COUNT(*) n FROM accused GROUP BY b ORDER BY b""")]
    edu = [(r["education"], r["n"]) for r in q("SELECT education,COUNT(*) n FROM accused GROUP BY education ORDER BY n DESC")]
    body = f"""<h2>Criminology-Based Offender Profiling & Risk Scoring</h2>
      <div class="card">{tbl}
        <div class="note">Risk score = 12 × linked cases + 6 × prior cases (capped 100) — transparent & explainable.</div></div>
      <div class="cols">
        <div class="card"><b>Accused by age band</b>{svg_bars(ages, color="#10b981")}</div>
        <div class="card"><b>Accused by education</b>{svg_bars(edu, color="#a855f7")}</div></div>"""
    return page("/offenders", body)

@app.route("/financial")
def financial():
    tt = q("SELECT COUNT(*) c FROM transactions")[0]["c"]
    fl = q("SELECT COUNT(*) c FROM transactions WHERE flagged=1")[0]["c"]
    rows = q("""SELECT t.fir_id,f.crime_type,f.district,COUNT(*) hops,SUM(t.amount) amt,SUM(t.flagged) fl
                FROM transactions t JOIN fir f ON t.fir_id=f.fir_id GROUP BY t.fir_id ORDER BY amt DESC LIMIT 12""")
    tbl = table(["FIR", "Crime type", "District", "Hops", "Total (₹)", "Flagged"], rows,
                cells=lambda r: [esc(r["fir_id"]), esc(r["crime_type"]), esc(r["district"]),
                                 esc(r["hops"]), f"₹{r['amt']:,}", esc(r["fl"])])
    metrics = f"""<div class="metrics">
      <div class="m"><div class="v">{tt}</div><div class="l">Tracked transactions</div></div>
      <div class="m"><div class="v">{fl}</div><div class="l">Flagged (suspicious)</div></div></div>"""
    body = f"""<h2>Financial Crime & Transaction Link Analysis</h2>{metrics}
      <div class="card"><b>Top money-trail cases (multi-hop transfers)</b>{tbl}</div>"""
    return page("/financial", body)

@app.route("/about")
def about():
    body = """<h2>About CrimeSense</h2>
    <div class="card">
    <p><b>CrimeSense by DevWithData</b> is an Intelligent Conversational AI & Crime Analytics platform
    built for the Karnataka State Police Datathon 2026.</p>
    <p>Investigators, analysts and policymakers query the crime database in plain English or Kannada and get
    answers backed by a transparent evidence trail (the exact SQL + reasoning), plus analytics for crime
    patterns, criminal networks, offender risk-scoring and financial money-trails.</p>
    <p><b>Explainable by design · privacy-first (synthetic data) · role-based access.</b>
    Deployed on Catalyst by Zoho (AppSail).</p>
    <p style="color:#64748b">Built by Shashikant · devwithdata.in</p></div>"""
    return page("/about", body)

@app.route("/health")
def health():
    return {"status": "ok", "firs": q("SELECT COUNT(*) c FROM fir")[0]["c"]}

if __name__ == "__main__":
    port = int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", os.getenv("PORT", 9000)))
    app.run(host="0.0.0.0", port=port, threaded=True)
