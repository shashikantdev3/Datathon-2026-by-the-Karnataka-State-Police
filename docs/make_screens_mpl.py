"""Render prototype UI snapshots as PNG using matplotlib (no browser needed).
Each screen mimics the CrimeSense dark UI and is populated with REAL DB data."""
import os, sqlite3, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import networkx as nx

DB = os.environ["CRIMESENSE_DB"]; OUT = os.environ.get("SCREEN_OUT", ".")
sys.path.insert(0, os.environ.get("APP_DIR", "."))
from network import build_cooffender_graph, key_players

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
def q(s, p=()): return con.execute(s, p).fetchall()

BG="#0f172a"; BAR="#0b1220"; CARD="#11203a"; LINE="#1e293b"; BLUE="#2563eb"; LBLUE="#60a5fa"
TXT="#e2e8f0"; SUB="#94a3b8"; TABS=["Conversational AI","Crime Patterns","Criminal Network","Offender Profiling","Financial Trails"]

def base(active, title):
    fig = plt.figure(figsize=(12.8, 9), dpi=130); fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,1280); ax.set_ylim(0,900); ax.axis("off"); ax.invert_yaxis()
    ax.add_patch(Rectangle((0,0),1280,52,color=BAR))
    ax.add_patch(Rectangle((24,18,),16,18,color=BLUE))
    ax.text(48,30,"CrimeSense",color="#f1f5f9",fontsize=17,fontweight="bold",va="center")
    ax.text(210,32,"by DevWithData  ·  devwithdata.in",color="#94a3b8",fontsize=9.5,va="center")
    ax.text(1256,26,"Investigator  ·  audit-logged",color="#cbd5e1",fontsize=9,va="center",ha="right")
    ax.text(1256,42,"English / Kannada",color="#cbd5e1",fontsize=9,va="center",ha="right")
    x=24
    for i,t in enumerate(TABS):
        w=12+len(t)*7.2
        ax.add_patch(FancyBboxPatch((x,60),w,26,boxstyle="round,pad=2",
                     fc=BLUE if i==active else CARD, ec="none"))
        ax.text(x+w/2,73,t,color="#fff" if i==active else "#cbd5e1",fontsize=9.5,ha="center",va="center")
        x+=w+8
    ax.text(24,116,title,color="#f1f5f9",fontsize=14,fontweight="bold",va="center")
    return fig, ax

def card(ax,x,y,w,h,fc=CARD,ec=LINE):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=3",fc=fc,ec=ec,lw=1))

def metrics(ax,y,items):
    x=24; w=(1280-48-16*(len(items)-1))/len(items)
    for v,l in items:
        card(ax,x,y,w,72)
        ax.text(x+20,y+34,str(v),color=LBLUE,fontsize=24,fontweight="bold",va="center")
        ax.text(x+20,y+58,l,color=SUB,fontsize=10,va="center")
        x+=w+16

def embed_chart(fig, rect, draw):
    ax=fig.add_axes(rect); ax.set_facecolor(BG)
    draw(ax)
    ax.tick_params(colors=SUB,labelsize=7)
    for s in ax.spines.values(): s.set_color(LINE)
    return ax

def save(fig,name):
    fig.savefig(os.path.join(OUT,name+".png"),facecolor=BG); plt.close(fig); print("wrote",name)

# ---------------- Screen 1: Chat ----------------
def s_chat():
    fig,ax=base(0,"Conversational Crime Intelligence — ask in English or Kannada")
    r=q("SELECT COUNT(*) c FROM fir WHERE crime_type='Theft' AND district='Bengaluru City' AND year=2024")[0]["c"]
    ax.text(24,150,"User:  How many theft cases in Bengaluru City in 2024?",color="#f1f5f9",fontsize=11,fontweight="bold")
    card(ax,24,162,1232,40,fc=CARD); ax.add_patch(Rectangle((24,162),4,40,color=BLUE))
    ax.text(44,182,f"CrimeSense:  There are {r} FIRs for Theft, in Bengaluru City, in 2024.",color=TXT,fontsize=11,va="center")
    card(ax,24,210,1232,46,fc="#0b1626")
    ax.text(40,224,"Explainable AI  —  Matched crime type → Theft · district → Bengaluru City · year → 2024",color=SUB,fontsize=8.5,va="center")
    ax.text(40,242,"SQL: SELECT COUNT(*) FROM fir WHERE crime_type=? AND district=? AND year=?",color="#7dd3fc",fontsize=8,va="center",family="monospace")
    ax.text(24,286,"User:  Which districts are the top hotspots?",color="#f1f5f9",fontsize=11,fontweight="bold")
    rows=q("SELECT district,COUNT(*) c FROM fir GROUP BY district ORDER BY c DESC LIMIT 8")
    card(ax,24,298,1232,34,fc=CARD); ax.add_patch(Rectangle((24,298),4,34,color=BLUE))
    ax.text(44,315,f"CrimeSense:  Top hotspot is {rows[0]['district']} ({rows[0]['c']} cases).",color=TXT,fontsize=11,va="center")
    def d(a):
        a.set_xticks(range(len(rows)))
        a.bar(range(len(rows)),[x["c"] for x in rows],color=BLUE)
        a.set_xticklabels([x["district"] for x in rows],rotation=18,ha="right",fontsize=8)
        a.set_title("Hotspots — FIRs by district",color=TXT,fontsize=10)
    embed_chart(fig,[0.04,0.18,0.93,0.40],d)
    ax.text(24,856,"Export conversation to PDF       Voice input (Web Speech API)       Context-aware follow-ups       Role-based access",color="#cbd5e1",fontsize=10)
    save(fig,"01_chat")

# ---------------- Screen 2: Patterns ----------------
def s_patterns():
    fig,ax=base(1,"Crime Pattern & Trend Analytics")
    metrics(ax,140,[(f"{q('SELECT COUNT(*) c FROM fir')[0]['c']:,}","Total FIRs"),
                    (q("SELECT COUNT(DISTINCT district) c FROM fir")[0]["c"],"Districts"),
                    (q("SELECT COUNT(*) c FROM accused")[0]["c"],"Accused"),
                    (q("SELECT COUNT(DISTINCT gang) c FROM fir WHERE gang IS NOT NULL")[0]["c"],"Active gangs")])
    yr=q("SELECT year,COUNT(*) c FROM fir GROUP BY year ORDER BY year")
    mo=q("SELECT month,COUNT(*) c FROM fir GROUP BY month ORDER BY month")
    ty=q("SELECT crime_type,COUNT(*) c FROM fir GROUP BY crime_type ORDER BY c DESC LIMIT 10")
    embed_chart(fig,[0.04,0.45,0.43,0.22],lambda a:(a.plot([x["year"] for x in yr],[x["c"] for x in yr],marker="o",color=LBLUE),a.set_title("Yearly trend",color=TXT,fontsize=10)))
    embed_chart(fig,[0.54,0.45,0.43,0.22],lambda a:(a.plot([x["month"] for x in mo],[x["c"] for x in mo],marker="o",color="#f59e0b"),a.set_title("Seasonality — festival-season uptick",color=TXT,fontsize=10)))
    def d(a):
        a.set_xticks(range(len(ty)))
        a.bar(range(len(ty)),[x["c"] for x in ty],color=BLUE)
        a.set_xticklabels([x["crime_type"] for x in ty],rotation=22,ha="right",fontsize=7)
        a.set_title("Top crime types (hotspot heads)",color=TXT,fontsize=10)
    embed_chart(fig,[0.04,0.08,0.93,0.24],d)
    save(fig,"02_patterns")

# ---------------- Screen 3: Network ----------------
def s_network():
    fig,ax=base(2,"Criminal Network & Relationship Analysis")
    G,names,gm=build_cooffender_graph(DB); kp=key_players(G)
    try: cl=len(nx.community.greedy_modularity_communities(G))
    except Exception: cl=len(list(nx.connected_components(G)))
    metrics(ax,140,[(G.number_of_nodes(),"Linked offenders"),(G.number_of_edges(),"Relationships"),(cl,"Detected cells")])
    def d(a):
        pos=nx.spring_layout(G,k=0.5,seed=42)
        gangs=sorted({gm.get(n) for n in G.nodes if gm.get(n)})
        pal=["#ef4444","#f59e0b","#10b981","#3b82f6","#a855f7"]
        cmap={g:pal[i%len(pal)] for i,g in enumerate(gangs)}
        cn=[cmap.get(gm.get(n),"#64748b") for n in G.nodes]
        bc=nx.betweenness_centrality(G); sizes=[40+500*bc[n] for n in G.nodes]
        nx.draw_networkx_edges(G,pos,ax=a,edge_color="#334155",width=0.5,alpha=0.6)
        nx.draw_networkx_nodes(G,pos,ax=a,node_color=cn,node_size=sizes,alpha=0.9)
        a.axis("off"); a.set_title("Co-offending graph (node colour = gang, size = centrality)",color=TXT,fontsize=10)
    embed_chart(fig,[0.03,0.30,0.62,0.42],d)
    ax.text(852,250,"Key players (betweenness centrality)",color="#f1f5f9",fontsize=11,fontweight="bold")
    ax.text(852,272,"Likely kingpins / connectors:",color=SUB,fontsize=9)
    yy=296
    for n,s in kp[:7]:
        ax.text(852,yy,f"• {names.get(n,n)} ({n})",color=TXT,fontsize=9.5)
        ax.text(1240,yy,f"{s}",color=LBLUE,fontsize=9.5,ha="right"); yy+=26
    save(fig,"03_network")

# ---------------- Screen 4: Offenders ----------------
def s_offenders():
    fig,ax=base(3,"Criminology-Based Offender Profiling & Risk Scoring")
    rows=q("""SELECT a.name,a.age,a.district,a.occupation,COUNT(af.fir_id) lc,a.prior_cases pc
              FROM accused a JOIN accused_fir af ON a.accused_id=af.accused_id
              GROUP BY a.accused_id ORDER BY lc DESC LIMIT 9""")
    cols=[("Name",40),("Age",330),("District",400),("Occupation",560),("Linked",740),("Priors",840),("Risk",930),("Band",1020)]
    ax.add_patch(Rectangle((24,150),1232,26,color=LINE))
    for c,x in cols: ax.text(x,163,c,color="#cbd5e1",fontsize=9.5,va="center",fontweight="bold")
    yy=190
    for r in rows:
        risk=min(100,r["lc"]*12+r["pc"]*6)
        band=("HIGH","#fecaca") if risk>60 else (("MEDIUM","#fde68a") if risk>30 else ("LOW","#bbf7d0"))
        vals=[r["name"],r["age"],r["district"],r["occupation"],r["lc"],r["pc"],risk]
        for (c,x),v in zip(cols[:-1],vals): ax.text(x,yy,str(v),color=TXT,fontsize=9,va="center")
        ax.text(1020,yy,band[0],color=band[1],fontsize=9,va="center")
        ax.add_patch(Rectangle((24,yy+12),1232,0.6,color=LINE)); yy+=28
    ax.text(24,yy+14,"Risk score = 12 × linked cases + 6 × prior cases (capped 100) — transparent & explainable.",color=SUB,fontsize=9)
    ages=q("SELECT CASE WHEN age<25 THEN '18-24' WHEN age<35 THEN '25-34' WHEN age<45 THEN '35-44' ELSE '45+' END b,COUNT(*) n FROM accused GROUP BY b ORDER BY b")
    edu=q("SELECT education,COUNT(*) n FROM accused GROUP BY education ORDER BY n DESC")
    embed_chart(fig,[0.04,0.06,0.43,0.22],lambda a:(a.bar([x["b"] for x in ages],[x["n"] for x in ages],color="#10b981"),a.set_title("Accused by age band",color=TXT,fontsize=10)))
    def de(a):
        a.set_xticks(range(len(edu)))
        a.bar(range(len(edu)),[x["n"] for x in edu],color="#a855f7")
        a.set_xticklabels([x["education"] for x in edu],rotation=18,ha="right",fontsize=7)
        a.set_title("Accused by education",color=TXT,fontsize=10)
    embed_chart(fig,[0.54,0.06,0.43,0.22],de)
    save(fig,"04_offenders")

# ---------------- Screen 5: Financial ----------------
def s_financial():
    fig,ax=base(4,"Financial Crime & Transaction Link Analysis")
    metrics(ax,140,[(q("SELECT COUNT(*) c FROM transactions")[0]["c"],"Tracked transactions"),
                    (q("SELECT COUNT(*) c FROM transactions WHERE flagged=1")[0]["c"],"Flagged (suspicious)")])
    rows=q("""SELECT t.fir_id,f.crime_type,f.district,COUNT(*) hops,SUM(t.amount) amt,SUM(t.flagged) fl
              FROM transactions t JOIN fir f ON t.fir_id=f.fir_id GROUP BY t.fir_id ORDER BY amt DESC LIMIT 7""")
    cols=[("FIR",40),("Crime type",200),("District",430),("Hops",640),("Total (Rs)",740),("Flagged",960)]
    ax.add_patch(Rectangle((24,236),1232,26,color=LINE))
    for c,x in cols: ax.text(x,249,c,color="#cbd5e1",fontsize=9.5,va="center",fontweight="bold")
    yy=276
    for r in rows:
        for (c,x),v in zip(cols,[r["fir_id"],r["crime_type"],r["district"],r["hops"],f"Rs {r['amt']:,}",r["fl"]]):
            ax.text(x,yy,str(v),color=TXT,fontsize=9,va="center")
        ax.add_patch(Rectangle((24,yy+12),1232,0.6,color=LINE)); yy+=28
    top=rows[0]["fir_id"]; trail=q("SELECT from_account,to_account FROM transactions WHERE fir_id=?",(top,))
    def d(a):
        Gt=nx.DiGraph()
        for r in trail: Gt.add_edge(r["from_account"],r["to_account"])
        pos=nx.spring_layout(Gt,seed=1)
        nx.draw_networkx(Gt,pos,ax=a,node_color="#f59e0b",edge_color="#ef4444",font_size=8,node_size=900,font_color=BG)
        a.axis("off"); a.set_title(f"Money trail — {top} (multi-hop transfer chain)",color=TXT,fontsize=10)
    embed_chart(fig,[0.04,0.06,0.92,0.26],d)
    save(fig,"05_financial")

for f in (s_chat,s_patterns,s_network,s_offenders,s_financial): f()
con.close()
