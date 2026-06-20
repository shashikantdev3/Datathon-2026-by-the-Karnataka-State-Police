"""
CrimeSense by DevWithData - Synthetic Karnataka Crime Database Generator
------------------------------------------------------------------------
Generates a realistic, *fully synthetic* crime dataset modelled on the structure
of Indian police FIR records (KSP) and NCRB crime heads. NO real personal data is
used. All names, FIRs, and identifiers are randomly generated for prototype/demo
purposes only.

Tables produced (SQLite -> data/crimesense.db):
  fir           : First Information Reports (the core crime incident table)
  accused       : Accused persons linked to FIRs
  victims       : Victims linked to FIRs
  officers       : Investigating officers
  transactions  : Financial transactions (for money-trail / financial crime module)
  case_log      : Investigation timeline events per FIR

Run:  python data/generate_data.py
"""
import os, sqlite3, random, datetime as dt
from faker import Faker

fake = Faker("en_IN")
Faker.seed(42); random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("CRIMESENSE_DB", os.path.join(HERE, "crimesense.db"))

# ---- Real Karnataka reference data (public knowledge) ----------------------
DISTRICTS = {
    "Bengaluru City": ["Whitefield", "Koramangala", "Jayanagar", "Yeshwanthpur", "KR Puram", "Hebbal", "Banashankari"],
    "Bengaluru Rural": ["Devanahalli", "Hoskote", "Nelamangala", "Doddaballapura"],
    "Mysuru": ["Devaraja", "Nazarbad", "Vijayanagar", "Krishnaraja"],
    "Mangaluru": ["Mangaluru North", "Kadri", "Pandeshwar", "Surathkal"],
    "Hubballi-Dharwad": ["Gokul Road", "Vidyanagar", "Keshwapur", "Old Hubli"],
    "Belagavi": ["Tilakwadi", "Camp", "Market", "Shahapur"],
    "Kalaburagi": ["Brahmpur", "Station Bazar", "Roza", "MB Nagar"],
    "Ballari": ["Cowl Bazar", "Brucepet", "Gandhi Nagar"],
    "Vijayapura": ["Gandhi Chowk", "Adarsh Nagar", "Jalanagar"],
    "Shivamogga": ["Doddapet", "Tunga Nagar", "Vinoba Nagar"],
    "Tumakuru": ["Kyathsandra", "Batawadi", "Town"],
    "Davanagere": ["Azad Nagar", "Vidyanagar", "Nittuvalli"],
}

# NCRB-aligned crime heads with representative IPC / special-act sections
CRIME_TYPES = [
    ("Theft", "IPC 379", "Property"),
    ("Burglary / House-breaking", "IPC 457", "Property"),
    ("Robbery", "IPC 392", "Property"),
    ("Dacoity", "IPC 395", "Property"),
    ("Motor Vehicle Theft", "IPC 379", "Property"),
    ("Cheating", "IPC 420", "Economic"),
    ("Criminal Breach of Trust", "IPC 406", "Economic"),
    ("Forgery", "IPC 468", "Economic"),
    ("Cyber Fraud", "IT Act 66D", "Cyber"),
    ("Online Financial Fraud", "IT Act 66C", "Cyber"),
    ("Hurt / Assault", "IPC 323", "Body"),
    ("Grievous Hurt", "IPC 325", "Body"),
    ("Murder", "IPC 302", "Body"),
    ("Attempt to Murder", "IPC 307", "Body"),
    ("Kidnapping / Abduction", "IPC 363", "Body"),
    ("Rioting", "IPC 147", "Public Order"),
    ("Criminal Intimidation", "IPC 506", "Public Order"),
    ("Crime Against Women", "IPC 354", "Women"),
    ("Domestic Violence", "IPC 498A", "Women"),
    ("Drug Trafficking", "NDPS 20", "Narcotics"),
    ("Illegal Liquor", "Excise Act", "Narcotics"),
    ("Extortion", "IPC 384", "Organized"),
]
MODUS = {
    "Theft": ["Pickpocketing in market", "Snatching at signal", "Shoplifting", "Theft from parked vehicle"],
    "Burglary / House-breaking": ["Night break-in via window", "Lock-breaking when house empty", "Roof entry"],
    "Robbery": ["Two-wheeler chain snatching", "Armed robbery at shop", "Highway robbery"],
    "Dacoity": ["Gang armed dacoity at farmhouse", "Bank approach-road dacoity"],
    "Motor Vehicle Theft": ["Bike lifted from parking", "Car key duplication", "Tow-away theft"],
    "Cheating": ["Fake job offer", "Property sale fraud", "Fake gold scheme"],
    "Criminal Breach of Trust": ["Misappropriation of deposits", "Chit fund default"],
    "Forgery": ["Forged property documents", "Fake degree certificate"],
    "Cyber Fraud": ["OTP phishing", "Fake customer-care call", "KYC update scam"],
    "Online Financial Fraud": ["UPI fraud", "Investment app scam", "Loan app extortion"],
    "Hurt / Assault": ["Bar brawl", "Road-rage assault", "Neighbour dispute"],
    "Grievous Hurt": ["Assault with weapon", "Group attack"],
    "Murder": ["Property dispute", "Personal enmity", "Gang rivalry"],
    "Attempt to Murder": ["Stabbing in rivalry", "Vehicle hit attempt"],
    "Kidnapping / Abduction": ["Abduction for ransom", "Eloping case"],
    "Rioting": ["Communal clash", "Political faction clash"],
    "Criminal Intimidation": ["Threat over loan", "Threat in land dispute"],
    "Crime Against Women": ["Harassment at workplace", "Public molestation"],
    "Domestic Violence": ["Dowry harassment", "Marital cruelty"],
    "Drug Trafficking": ["Ganja transport", "MDMA peddling near college"],
    "Illegal Liquor": ["Illicit liquor sale", "Inter-state smuggling"],
    "Extortion": ["Protection money from shops", "Threat call for money"],
}
STATUS = ["Under Investigation", "Chargesheet Filed", "Convicted", "Acquitted", "Pending Trial", "Closed - Undetected"]
GANGS = ["Silk Board Gang", "KR Market Chain Snatchers", "Peenya Auto-lifters",
         "Cyber Nest Syndicate", "Hubli Highway Gang", None, None, None, None, None]

def rand_date(start_year=2021, end_year=2025):
    start = dt.date(start_year, 1, 1); end = dt.date(end_year, 12, 31)
    return start + dt.timedelta(days=random.randint(0, (end - start).days))

def main():
    if os.path.exists(DB): os.remove(DB)
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.executescript("""
    CREATE TABLE fir(fir_id TEXT PRIMARY KEY, fir_no TEXT, date TEXT, year INT, month INT,
        district TEXT, police_station TEXT, crime_type TEXT, ipc_section TEXT, category TEXT,
        modus_operandi TEXT, status TEXT, gang TEXT, property_value INT, officer_id TEXT, lat REAL, lon REAL);
    CREATE TABLE accused(accused_id TEXT PRIMARY KEY, name TEXT, age INT, gender TEXT,
        district TEXT, occupation TEXT, education TEXT, prior_cases INT);
    CREATE TABLE accused_fir(accused_id TEXT, fir_id TEXT);
    CREATE TABLE victims(victim_id TEXT PRIMARY KEY, fir_id TEXT, name TEXT, age INT, gender TEXT,
        occupation TEXT, loss_amount INT);
    CREATE TABLE officers(officer_id TEXT PRIMARY KEY, name TEXT, rank TEXT, station TEXT);
    CREATE TABLE transactions(txn_id TEXT PRIMARY KEY, fir_id TEXT, from_account TEXT, to_account TEXT,
        amount INT, date TEXT, channel TEXT, flagged INT);
    CREATE TABLE case_log(log_id INTEGER PRIMARY KEY AUTOINCREMENT, fir_id TEXT, date TEXT, event TEXT);
    """)

    # Officers
    ranks = ["PSI", "PI", "ASI", "DySP"]
    officers = []
    for i in range(40):
        oid = f"OFF{i+1:03d}"
        d = random.choice(list(DISTRICTS)); ps = random.choice(DISTRICTS[d])
        officers.append((oid, fake.name(), random.choice(ranks), f"{ps} PS, {d}"))
    cur.executemany("INSERT INTO officers VALUES(?,?,?,?)", officers)

    # Accused pool (some are repeat offenders reused across FIRs)
    accused = []
    occ = ["Unemployed", "Daily wage", "Driver", "Mechanic", "Student", "Shopkeeper", "Auto driver", "Labourer", "IT employee", "Farmer"]
    edu = ["Illiterate", "Primary", "SSLC", "PUC", "Graduate", "Diploma"]
    for i in range(600):
        aid = f"ACC{i+1:04d}"
        g = random.choices(["Male", "Female"], [0.86, 0.14])[0]
        accused.append((aid, fake.name_male() if g == "Male" else fake.name_female(),
                        random.randint(18, 62), g, random.choice(list(DISTRICTS)),
                        random.choice(occ), random.choice(edu), 0))
    repeat_pool = [a[0] for a in accused[:120]]  # habitual offenders

    # FIRs
    firs, accused_fir, victims, txns, logs = [], [], [], [], []
    prior = {a[0]: 0 for a in accused}
    for i in range(1500):
        fid = f"FIR{i+1:05d}"
        d = random.choice(list(DISTRICTS)); ps = random.choice(DISTRICTS[d])
        ct, ipc, cat = random.choice(CRIME_TYPES)
        date = rand_date(); year, month = date.year, date.month
        # seasonal & festival weighting for property crime
        if cat == "Property" and month in (10, 11):  # festival season uptick
            if random.random() < 0.4: date = rand_date(year, year); month = random.choice([10, 11])
        gang = random.choice(GANGS) if cat in ("Property", "Organized", "Cyber") else None
        status = random.choices(STATUS, [0.30, 0.22, 0.13, 0.07, 0.18, 0.10])[0]
        pval = 0
        if cat in ("Property", "Economic", "Cyber"):
            pval = random.choice([5000, 12000, 25000, 50000, 120000, 350000, 900000])
        lat = round(12 + random.random() * 4, 5); lon = round(74 + random.random() * 4, 5)
        oid = random.choice(officers)[0]
        firs.append((fid, f"{random.randint(1,300)}/{year}", date.isoformat(), year, month, d, ps,
                     ct, ipc, cat, random.choice(MODUS[ct]), status, gang, pval, oid, lat, lon))

        # link accused (repeat offenders favoured for gang/property)
        n_acc = random.choices([1, 2, 3, 4], [0.6, 0.25, 0.1, 0.05])[0]
        chosen = set()
        for _ in range(n_acc):
            if gang and random.random() < 0.7:
                aid = random.choice(repeat_pool)
            else:
                aid = random.choice(accused)[0]
            if aid in chosen: continue
            chosen.add(aid); prior[aid] += 1
            accused_fir.append((aid, fid))

        # victims
        if cat not in ("Narcotics",):
            for _ in range(random.choices([1, 2], [0.85, 0.15])[0]):
                vg = random.choice(["Male", "Female"])
                loss = pval if pval and random.random() < 0.8 else random.choice([0, 0, 2000, 8000])
                victims.append((f"VIC{len(victims)+1:05d}", fid,
                                fake.name_male() if vg == "Male" else fake.name_female(),
                                random.randint(16, 75), vg, random.choice(occ), loss))

        # financial transactions for economic/cyber crime (money trail)
        if cat in ("Economic", "Cyber", "Organized") and random.random() < 0.7:
            n_hops = random.randint(1, 4)
            acc_from = f"AC{random.randint(10000,99999)}"
            for h in range(n_hops):
                acc_to = f"AC{random.randint(10000,99999)}"
                txns.append((f"TXN{len(txns)+1:06d}", fid, acc_from, acc_to,
                             random.choice([10000, 25000, 50000, 100000, 250000]),
                             date.isoformat(), random.choice(["UPI", "IMPS", "NEFT", "Wallet", "Cash deposit"]),
                             1 if random.random() < 0.5 else 0))
                acc_from = acc_to

        # case log timeline
        logs.append((None, fid, date.isoformat(), "FIR registered"))
        logs.append((None, fid, (date + dt.timedelta(days=random.randint(1,5))).isoformat(), "Spot investigation / panchnama"))
        if status in ("Chargesheet Filed", "Convicted", "Acquitted", "Pending Trial"):
            logs.append((None, fid, (date + dt.timedelta(days=random.randint(20,90))).isoformat(), "Chargesheet filed"))
        if status in ("Convicted", "Acquitted"):
            logs.append((None, fid, (date + dt.timedelta(days=random.randint(120,500))).isoformat(),
                         f"Court verdict: {status}"))

    # update prior_cases on accused
    accused = [(a[0], a[1], a[2], a[3], a[4], a[5], a[6], prior[a[0]]) for a in accused]

    cur.executemany("INSERT INTO fir VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", firs)
    cur.executemany("INSERT INTO accused VALUES(?,?,?,?,?,?,?,?)", accused)
    cur.executemany("INSERT INTO accused_fir VALUES(?,?)", accused_fir)
    cur.executemany("INSERT INTO victims VALUES(?,?,?,?,?,?,?)", victims)
    cur.executemany("INSERT INTO transactions VALUES(?,?,?,?,?,?,?,?)", txns)
    cur.executemany("INSERT INTO case_log(log_id,fir_id,date,event) VALUES(?,?,?,?)", logs)
    con.commit()

    print(f"DB written -> {DB}")
    for t in ["fir", "accused", "accused_fir", "victims", "officers", "transactions", "case_log"]:
        print(f"  {t:14s}: {cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
    con.close()

if __name__ == "__main__":
    main()
