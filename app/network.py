"""
Criminal Network & Relationship Analysis
----------------------------------------
Builds a graph of accused <-> FIR <-> co-accused / location links and detects
tightly-connected groups (potential organised-crime clusters) using networkx.
"""
import sqlite3
import networkx as nx


def build_cooffender_graph(db_path, min_shared=1, limit_accused=120):
    """Edges between accused who share at least `min_shared` FIRs (co-offending)."""
    con = sqlite3.connect(db_path); con.row_factory = sqlite3.Row
    # focus on the most active accused to keep the graph readable
    active = con.execute("""SELECT af.accused_id, COUNT(*) c FROM accused_fir af
                            GROUP BY af.accused_id ORDER BY c DESC LIMIT ?""", (limit_accused,)).fetchall()
    keep = {r["accused_id"] for r in active}
    rows = con.execute("SELECT accused_id, fir_id FROM accused_fir").fetchall()
    names = {r["accused_id"]: r["name"] for r in con.execute("SELECT accused_id,name FROM accused")}
    gang = {}
    for r in con.execute("""SELECT af.accused_id, f.gang FROM accused_fir af
                            JOIN fir f ON af.fir_id=f.fir_id WHERE f.gang IS NOT NULL"""):
        gang[r["accused_id"]] = r["gang"]
    con.close()

    fir_to_acc = {}
    for r in rows:
        if r["accused_id"] in keep:
            fir_to_acc.setdefault(r["fir_id"], []).append(r["accused_id"])

    G = nx.Graph()
    for aid in keep:
        G.add_node(aid, label=names.get(aid, aid), gang=gang.get(aid))
    for fir, accs in fir_to_acc.items():
        for i in range(len(accs)):
            for j in range(i + 1, len(accs)):
                a, b = accs[i], accs[j]
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    # drop isolated nodes for a cleaner network view
    G.remove_nodes_from([n for n in list(G.nodes) if G.degree(n) == 0])
    return G, names, gang


def detect_clusters(G):
    """Greedy modularity communities = candidate organised-crime cells."""
    if G.number_of_edges() == 0:
        return []
    try:
        comms = nx.community.greedy_modularity_communities(G)
    except Exception:
        comms = list(nx.connected_components(G))
    return [c for c in comms if len(c) >= 2]


def key_players(G, top=10):
    """Betweenness centrality ranks 'connectors' / kingpins in the network."""
    if G.number_of_nodes() == 0:
        return []
    bc = nx.betweenness_centrality(G, weight="weight")
    ranked = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:top]
    return [(n, round(s, 4)) for n, s in ranked]
