"""Generate process-flow, use-case and architecture diagrams (white bg) for the deck."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
OUT = os.environ.get("DIA_OUT", ".")
NAVY="#0b3d91"; BLUE="#2563eb"; LBLUE="#dbeafe"; RED="#b91c1c"; GREY="#475569"; INK="#0f172a"; GREEN="#15803d"

def box(ax,x,y,w,h,text,fc=LBLUE,ec=BLUE,tc=INK,fs=10,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02,rounding_size=0.08",
                 fc=fc,ec=ec,lw=1.6))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=fs,color=tc,
            fontweight="bold" if bold else "normal",wrap=True)

def arrow(ax,x1,y1,x2,y2,color=GREY):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=16,lw=1.8,color=color))

# -------- Process flow --------
def process_flow():
    fig,ax=plt.subplots(figsize=(11,4.6),dpi=140); ax.set_xlim(0,11);ax.set_ylim(0,4.6);ax.axis("off")
    fig.patch.set_facecolor("white")
    steps=[("User query\n(English / Kannada\ntext or voice)",LBLUE),
           ("Language detect\n& normalise\n(KN → EN)","#fef9c3"),
           ("Intent + entity\nextraction\n(crime, place, year)","#fef9c3"),
           ("Explainable\nNL → SQL engine\n(read-only)",LBLUE),
           ("Crime Data Store\n(FIR / accused /\nvictims / txns)","#dcfce7")]
    x=0.2;y=2.6;w=1.95;h=1.4
    for i,(t,c) in enumerate(steps):
        box(ax,x,y,w,h,t,fc=c,fs=9)
        if i<len(steps)-1: arrow(ax,x+w,y+h/2,x+w+0.18,y+h/2)
        x+=w+0.18
    # second row back
    out=[("Answer +\nevidence trail\n(SQL + reasoning)",LBLUE),
         ("Charts, network\ngraphs, risk\nscores","#dcfce7"),
         ("Export\nconversation\nto PDF","#fee2e2"),
         ("Role-based access\n+ audit log","#e0e7ff")]
    x=2.5;y=0.4;w=1.95;h=1.4
    arrow(ax,9.0,2.6,9.0,1.8)  # down from datastore area
    for i,(t,c) in enumerate(out[::-1]):
        box(ax,x,y,w,h,t,fc=c,fs=9)
        if i<len(out)-1: arrow(ax,x+w,y+h/2,x+w+0.18,y+h/2)  # left->right visually
        x+=w+0.18
    ax.text(5.5,4.4,"CrimeSense — Conversational Query Process Flow",ha="center",fontsize=13,fontweight="bold",color=NAVY)
    fig.savefig(os.path.join(OUT,"diagram_process.png"),facecolor="white",bbox_inches="tight");plt.close(fig)
    print("process flow done")

# -------- Use-case --------
def use_case():
    fig,ax=plt.subplots(figsize=(11,5.2),dpi=140); ax.set_xlim(0,11);ax.set_ylim(0,5.2);ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(5.5,5.0,"Use-Case Diagram",ha="center",fontsize=13,fontweight="bold",color=NAVY)
    actors=[("Investigator",0.7,4.0),("Analyst",0.7,2.6),("Supervisor",0.7,1.2),("Policymaker",0.7,0.2)]
    for n,x,y in actors:
        ax.add_patch(plt.Circle((x,y+0.55),0.16,fc=NAVY,ec=NAVY))
        ax.plot([x,x],[y+0.39,y+0.05],color=NAVY,lw=2)
        ax.text(x+0.45,y+0.3,n,fontsize=10,va="center",fontweight="bold",color=INK)
    uc=["Ask NL question (EN/KN)","Get explainable answer","View crime hotspots & trends",
        "Explore criminal network","Profile & risk-score offenders","Trace money trails",
        "Export conversation PDF","Receive early-warning alerts"]
    x=4.2;y=4.4;w=3.0;h=0.5
    for i,u in enumerate(uc):
        yy=y-i*0.56
        ax.add_patch(FancyBboxPatch((x,yy),w,h,boxstyle="round,pad=0.02,rounding_size=0.25",fc=LBLUE,ec=BLUE,lw=1.3))
        ax.text(x+w/2,yy+h/2,u,ha="center",va="center",fontsize=9.5,color=INK)
        ax.add_patch(FancyArrowPatch((1.6,actors[i%4][2]+0.3),(x,yy+h/2),arrowstyle="-",lw=0.7,color="#94a3b8"))
    ax.add_patch(FancyBboxPatch((4.0,-0.05),3.4,5.0,boxstyle="round,pad=0.02",fc="none",ec="#cbd5e1",lw=1.2,ls="--"))
    ax.text(5.7,4.96,"CrimeSense System",ha="center",fontsize=9,color=GREY,style="italic")
    fig.savefig(os.path.join(OUT,"diagram_usecase.png"),facecolor="white",bbox_inches="tight");plt.close(fig)
    print("use case done")

# -------- Architecture --------
def architecture():
    fig,ax=plt.subplots(figsize=(11,5.4),dpi=140); ax.set_xlim(0,11);ax.set_ylim(0,5.4);ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(5.5,5.2,"Solution Architecture — deployed on Catalyst by Zoho",ha="center",fontsize=13,fontweight="bold",color=NAVY)
    # presentation layer
    box(ax,0.5,4.0,10,0.95,"PRESENTATION LAYER  ·  Streamlit Web UI on Catalyst AppSail (Python)\nChat · Patterns · Network · Profiling · Financial · Explainable AI   |   English / Kannada · Voice · Role-based access",
        fc="#e0e7ff",ec=BLUE,fs=9.5,bold=False)
    # app/logic layer
    cells=[("NL → SQL Engine\n(explainable,\nread-only)","#fef9c3"),
           ("Analytics & Network\n(patterns, networkx,\ncentrality, clusters)","#fef9c3"),
           ("Risk Scoring &\nForecasting\n(Catalyst QuickML)","#fef9c3"),
           ("PDF Export &\nAudit Logging\n(Functions)","#fef9c3")]
    x=0.5;w=2.42
    for t,c in cells:
        box(ax,x,2.35,w,1.25,t,fc=c,ec="#ca8a04",fs=9); x+=w+0.2
    # data layer
    box(ax,0.5,0.9,10,0.95,"DATA LAYER  ·  Catalyst Data Store (Serverless RDB + OLAP)\nfir · accused · accused_fir · victims · transactions · case_log · officers",
        fc="#dcfce7",ec=GREEN,fs=9.5)
    box(ax,0.5,0.1,10,0.6,"SECURITY & GOVERNANCE  ·  Catalyst Authentication · Role-based access · Audit logs · Data-protection compliance",
        fc="#fee2e2",ec=RED,fs=9.5)
    for xx in (1.7,3.5,5.5,7.5,9.3):
        arrow(ax,xx,4.0,xx,3.62,color="#94a3b8")
        arrow(ax,xx,2.35,xx,1.88,color="#94a3b8")
    fig.savefig(os.path.join(OUT,"diagram_architecture.png"),facecolor="white",bbox_inches="tight");plt.close(fig)
    print("architecture done")

process_flow(); use_case(); architecture()
