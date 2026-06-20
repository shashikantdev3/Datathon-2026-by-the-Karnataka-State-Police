"""
CrimeSense NL-to-SQL Engine
---------------------------
Translates natural-language crime questions into safe, parameterised SQL over the
CrimeSense database, returning BOTH the answer data and an explainability trail
(SQL + reasoning) to satisfy the 'Explainable AI' requirement.

- Deterministic, schema-aware parser works fully OFFLINE (no API key required).
- Context-aware follow-ups: inherits district/crime/year only for genuine follow-ups.
- READ-ONLY: only SELECT statements are ever executed.
"""
import re
import sqlite3
from dataclasses import dataclass, field

CRIME_KEYWORDS = {
    "theft": "Theft", "burglary": "Burglary / House-breaking", "house-break": "Burglary / House-breaking",
    "robbery": "Robbery", "dacoity": "Dacoity", "vehicle theft": "Motor Vehicle Theft",
    "bike theft": "Motor Vehicle Theft", "cheating": "Cheating", "breach of trust": "Criminal Breach of Trust",
    "forgery": "Forgery", "cyber": "Cyber Fraud", "online fraud": "Online Financial Fraud",
    "upi": "Online Financial Fraud", "assault": "Hurt / Assault", "hurt": "Hurt / Assault",
    "murder": "Murder", "attempt to murder": "Attempt to Murder", "kidnap": "Kidnapping / Abduction",
    "riot": "Rioting", "intimidation": "Criminal Intimidation", "women": "Crime Against Women",
    "domestic": "Domestic Violence", "dowry": "Domestic Violence", "drug": "Drug Trafficking",
    "narcotic": "Drug Trafficking", "liquor": "Illegal Liquor", "extortion": "Extortion",
}
CATEGORY_KEYWORDS = {"property crime": "Property", "economic": "Economic", "cyber crime": "Cyber",
                     "violent": "Body", "narcotic": "Narcotics"}
DISTRICTS = ["Bengaluru City", "Bengaluru Rural", "Mysuru", "Mangaluru", "Hubballi-Dharwad",
             "Belagavi", "Kalaburagi", "Ballari", "Vijayapura", "Shivamogga", "Tumakuru", "Davanagere"]
FOLLOWUP_CUES = ("what about", "how about", "same ", "those", "them",
                 "there", "also ", "instead", "that district", "this crime", "for it")


@dataclass
class Context:
    district: str = None
    crime_type: str = None
    category: str = None
    year: int = None


@dataclass
class Result:
    intent: str
    sql: str
    params: list
    rows: list = field(default_factory=list)
    columns: list = field(default_factory=list)
    answer: str = ""
    reasoning: list = field(default_factory=list)
    chart: dict = None


class NLEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self.ctx = Context()

    def _con(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _extract(self, q):
        ql = q.lower()
        found = {"reasoning": []}
        for d in DISTRICTS:
            if d.lower() in ql or d.split()[0].lower() in ql:
                found["district"] = d
                found["reasoning"].append(f"Matched district -> {d}")
                break
        for kw, ct in CRIME_KEYWORDS.items():
            if kw in ql:
                found["crime_type"] = ct
                found["reasoning"].append(f"Matched crime type -> {ct}")
                break
        if "crime_type" not in found:
            for kw, cat in CATEGORY_KEYWORDS.items():
                if kw in ql:
                    found["category"] = cat
                    found["reasoning"].append(f"Matched category -> {cat}")
                    break
        ym = re.search(r"(20\d{2})", ql)
        if ym:
            found["year"] = int(ym.group(1))
            found["reasoning"].append(f"Matched year -> {ym.group(1)}")
        return found

    def _apply_context(self, found, raw_q):
        ql = raw_q.lower().strip()
        is_followup = ql.startswith("and ") or any(c in ql for c in FOLLOWUP_CUES) or len(ql.split()) <= 3
        if is_followup:
            if "district" not in found and self.ctx.district:
                found["district"] = self.ctx.district
                found["reasoning"].append(f"Follow-up -> carried over district: {self.ctx.district}")
            if "crime_type" not in found and self.ctx.crime_type:
                found["crime_type"] = self.ctx.crime_type
                found["reasoning"].append(f"Follow-up -> carried over crime type: {self.ctx.crime_type}")
            if "year" not in found and self.ctx.year:
                found["year"] = self.ctx.year
        else:
            self.ctx = Context()
        for k in ("district", "crime_type", "category", "year"):
            if k in found:
                setattr(self.ctx, k, found[k])
        return found

    def _where(self, found):
        clauses, params = [], []
        if found.get("district"):
            clauses.append("district = ?"); params.append(found["district"])
        if found.get("crime_type"):
            clauses.append("crime_type = ?"); params.append(found["crime_type"])
        if found.get("category"):
            clauses.append("category = ?"); params.append(found["category"])
        if found.get("year"):
            clauses.append("year = ?"); params.append(found["year"])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, params

    def ask(self, q):
        found = self._apply_context(self._extract(q), q)
        ql = q.lower()
        if any(w in ql for w in ["how many", "count", "number of", "total"]):
            return self._count(q, found)
        if any(w in ql for w in ["trend", "over time", "by year", "by month", "monthly", "yearly"]):
            return self._trend(q, found)
        if any(w in ql for w in ["hotspot", "top district", "which district", "highest", "most crime", "worst"]):
            return self._hotspots(q, found)
        if any(w in ql for w in ["repeat offender", "habitual", "most cases", "top accused", "risk"]):
            return self._offenders(q, found)
        if any(w in ql for w in ["gang", "network", "organized", "organised", "syndicate"]):
            return self._gangs(q, found)
        if any(w in ql for w in ["status", "investigation", "chargesheet", "convict", "pending"]):
            return self._status(q, found)
        if any(w in ql for w in ["money", "transaction", "financial", "trail", "suspicious"]):
            return self._financial(q, found)
        if re.search(r"fir\s*\d", ql) or "case detail" in ql or "summary of" in ql:
            return self._case_detail(q, found)
        if any(w in ql for w in ["breakdown", "by crime type", "type of crime", "category", "list crimes"]):
            return self._breakdown(q, found)
        return self._count(q, found)

    def _run(self, sql, params):
        con = self._con()
        cur = con.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return cols, rows

    def _count(self, q, found):
        where, params = self._where(found)
        sql = f"SELECT COUNT(*) AS total FROM fir{where}"
        cols, rows = self._run(sql, params)
        total = rows[0]["total"]
        ans = f"There are **{total:,}** FIRs{self._desc(found)}."
        return Result("count", sql, params, rows, cols, ans,
                      found["reasoning"] + ["Counted matching FIR records."])

    def _trend(self, q, found):
        where, params = self._where(found)
        group = "month" if "month" in q.lower() else "year"
        sql = f"SELECT {group}, COUNT(*) AS cases FROM fir{where} GROUP BY {group} ORDER BY {group}"
        cols, rows = self._run(sql, params)
        ans = f"Trend of FIRs by {group}{self._desc(found)} ({len(rows)} periods)."
        return Result("trend", sql, params, rows, cols, ans,
                      found["reasoning"] + [f"Grouped FIR counts by {group}."],
                      chart={"kind": "line", "x": group, "y": "cases"})

    def _hotspots(self, q, found):
        f2 = dict(found); f2.pop("district", None)
        where, params = self._where(f2)
        sql = f"SELECT district, COUNT(*) AS cases FROM fir{where} GROUP BY district ORDER BY cases DESC LIMIT 10"
        cols, rows = self._run(sql, params)
        ans = (f"Top hotspot{self._desc(f2)} is **{rows[0]['district']}** ({rows[0]['cases']:,} cases)."
               if rows else "No data.")
        return Result("hotspots", sql, params, rows, cols, ans,
                      found["reasoning"] + ["Ranked districts by FIR count (descending)."],
                      chart={"kind": "bar", "x": "district", "y": "cases"})

    def _breakdown(self, q, found):
        where, params = self._where(found)
        sql = f"SELECT crime_type, COUNT(*) AS cases FROM fir{where} GROUP BY crime_type ORDER BY cases DESC LIMIT 15"
        cols, rows = self._run(sql, params)
        ans = f"Crime-type breakdown{self._desc(found)} -- {len(rows)} types."
        return Result("breakdown", sql, params, rows, cols, ans,
                      found["reasoning"] + ["Grouped FIRs by crime type."],
                      chart={"kind": "bar", "x": "crime_type", "y": "cases"})

    def _offenders(self, q, found):
        where, params = self._where(found)
        jw = where.replace("district", "f.district").replace("crime_type", "f.crime_type")\
                  .replace("category", "f.category").replace("year", "f.year")
        sql = f"""SELECT a.accused_id, a.name, a.age, a.district, a.prior_cases,
                  COUNT(af.fir_id) AS linked_cases
                  FROM accused a JOIN accused_fir af ON a.accused_id=af.accused_id
                  JOIN fir f ON af.fir_id=f.fir_id {jw}
                  GROUP BY a.accused_id ORDER BY linked_cases DESC, a.prior_cases DESC LIMIT 10"""
        cols, rows = self._run(sql, params)
        for r in rows:
            r["risk_score"] = min(100, r["linked_cases"] * 12 + r["prior_cases"] * 6)
        cols = cols + ["risk_score"]
        ans = f"Top repeat offenders{self._desc(found)} ranked by linked cases & computed risk score."
        return Result("offenders", sql, params, rows, cols, ans,
                      found["reasoning"] + ["Joined accused<->FIR, counted links, risk_score = 12*cases + 6*priors (cap 100)."],
                      chart={"kind": "bar", "x": "name", "y": "risk_score"})

    def _gangs(self, q, found):
        where, params = self._where(found)
        w = where + (" AND gang IS NOT NULL" if where else " WHERE gang IS NOT NULL")
        sql = f"SELECT gang, COUNT(*) AS cases, COUNT(DISTINCT district) AS districts FROM fir{w} GROUP BY gang ORDER BY cases DESC"
        cols, rows = self._run(sql, params)
        ans = f"Identified **{len(rows)}** active organised-crime groups{self._desc(found)}."
        return Result("gangs", sql, params, rows, cols, ans,
                      found["reasoning"] + ["Filtered FIRs tagged to a gang; grouped by gang."],
                      chart={"kind": "bar", "x": "gang", "y": "cases"})

    def _status(self, q, found):
        where, params = self._where(found)
        sql = f"SELECT status, COUNT(*) AS cases FROM fir{where} GROUP BY status ORDER BY cases DESC"
        cols, rows = self._run(sql, params)
        ans = f"Investigation-status breakdown{self._desc(found)}."
        return Result("status", sql, params, rows, cols, ans,
                      found["reasoning"] + ["Grouped FIRs by investigation status."],
                      chart={"kind": "pie", "x": "status", "y": "cases"})

    def _financial(self, q, found):
        sql = """SELECT t.fir_id, f.crime_type, f.district, COUNT(*) AS hops,
                 SUM(t.amount) AS total_amount, SUM(t.flagged) AS flagged_txns
                 FROM transactions t JOIN fir f ON t.fir_id=f.fir_id
                 GROUP BY t.fir_id ORDER BY total_amount DESC LIMIT 12"""
        cols, rows = self._run(sql, [])
        ans = "Top money-trail cases by total transacted value (multi-hop transfers flagged)."
        return Result("financial", sql, [], rows, cols, ans,
                      found["reasoning"] + ["Aggregated transactions per FIR; surfaced highest-value money trails."],
                      chart={"kind": "bar", "x": "fir_id", "y": "total_amount"})

    def _case_detail(self, q, found):
        m = re.search(r"(fir\s*0*\d+)", q.lower())
        fir_id = None
        if m:
            num = re.search(r"\d+", m.group(1)).group()
            fir_id = f"FIR{int(num):05d}"
        if not fir_id:
            cols, rows = self._run("SELECT fir_id FROM fir ORDER BY RANDOM() LIMIT 1", [])
            fir_id = rows[0]["fir_id"]
        sql = "SELECT * FROM fir WHERE fir_id = ?"
        cols, rows = self._run(sql, [fir_id])
        ans = f"Case summary for **{fir_id}**."
        return Result("case_detail", sql, [fir_id], rows, cols, ans,
                      found["reasoning"] + [f"Retrieved full FIR record for {fir_id}."])

    def _desc(self, found):
        bits = []
        if found.get("crime_type"): bits.append(found["crime_type"])
        if found.get("category"): bits.append(found["category"] + " crimes")
        if found.get("district"): bits.append("in " + found["district"])
        if found.get("year"): bits.append("in " + str(found["year"]))
        return (" for " + ", ".join(bits)) if bits else ""


SAMPLE_QUESTIONS = [
    "How many theft cases in Bengaluru City in 2024?",
    "Show crime trend by year",
    "Which districts are the top hotspots?",
    "Who are the top repeat offenders?",
    "Show me the organized crime gangs",
    "Investigation status breakdown for cyber crime",
    "Show suspicious money trails",
    "Crime type breakdown for Mysuru",
]
