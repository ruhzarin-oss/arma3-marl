"""CLAUDE BRANCHE SUR LE MONDE - point 12 des douze manques.

Un serveur MCP en lecture seule : il ouvre le monde a l observation sans jamais toucher a une mesure en cours.
C est la regle posee le 05/09 pour le labo MCP d Arma : le MCP observe, le job mesure.

Outils : etat_du_monde, journal_du_monde, habitants, doctrine, portes.
Lancement ( par le client MCP, en stdio ) :
   python -m monde.mcp_monde --dossier /mnt/data/hmt/monde
Rien ici n ecrit dans le monde : pas d ordre, pas de reprise, pas de suppression."""
import argparse, glob, json, os, pickle, sys

DOSSIER = "/mnt/data/hmt/monde"


def dernier_cycle(dossier):
    fichier = os.path.join(dossier, "cycle_courant")
    if os.path.exists(fichier):
        d = open(fichier).read().strip()
        if os.path.isdir(d): return d
    cands = sorted(glob.glob(os.path.join(dossier, "*")), key=os.path.getmtime, reverse=True)
    return next((c for c in cands if os.path.isdir(c) and os.path.exists(os.path.join(c, "trace_e2.jsonl"))), dossier)


def lire_lignes(chemin, n):
    if not os.path.exists(chemin): return []
    with open(chemin) as f: lignes = f.readlines()[-n:]
    out = []
    for l in lignes:
        try: out.append(json.loads(l))
        except json.JSONDecodeError: pass
    return out


def etat_du_monde(dossier, **_):
    """Ou en est le monde : son heure, ses corps, son pont, ses anomalies."""
    d = dernier_cycle(dossier)
    bilans = [b for b in lire_lignes(os.path.join(d, "trace_e2.jsonl"), 400) if b.get("type") == "bilan"]
    instantane = os.path.join(d, "instantane.pkl")
    etat = {"cycle": os.path.basename(d), "dernier_bilan": bilans[-1] if bilans else None,
            "instantane": os.path.exists(instantane)}
    if os.path.exists(instantane):
        try:
            w = pickle.load(open(instantane, "rb"))
            etat["monde"] = {"jour": w.jour, "heure": round(w.heure, 2),
                             "vivants": sum(1 for h in w.habitants if h.vivant), "resume": w.resume_jour()}
        except Exception as ex: etat["monde"] = f"instantane illisible : {ex}"
    return etat


def journal_du_monde(dossier, n=30, type=None, **_):
    """Ce qui est arrive dans le monde : decisions du gouvernement, ecole, convois, naissances, morts."""
    d = dernier_cycle(dossier)
    ev = lire_lignes(os.path.join(d, "journal_monde.jsonl"), 4000)
    if type: ev = [e for e in ev if e.get("type") == type]
    return ev[-int(n):]


def habitants(dossier, n=20, role=None, **_):
    """Qui vit dans le pays, d apres le dernier instantane."""
    d = dernier_cycle(dossier)
    chemin = os.path.join(d, "instantane.pkl")
    if not os.path.exists(chemin): return {"erreur": "aucun instantane : le monde n a pas encore passe un jour"}
    w = pickle.load(open(chemin, "rb"))
    gens = [h for h in w.habitants if h.vivant and (role is None or h.role == role)]
    return [{"id": h.id, "role": h.role, "age": round(h.age, 1), "lieu": getattr(h.lieu, "id", None),
             "poste": h.poste, "faim": round(h.faim, 2), "etat": h.etat} for h in gens[:int(n)]]


def doctrine(dossier, **_):
    """Ce que les menages ont appris : les poids partages et leur nombre de lecons."""
    for c in (os.path.join(dossier, "doctrine", "menages.json"), os.path.join(dernier_cycle(dossier), "doctrine.json")):
        if os.path.exists(c):
            with open(c) as f: return json.load(f)
    return {"erreur": "aucune doctrine ecrite"}


def portes(dossier, **_):
    """Les portes du monde et leur dernier resultat connu."""
    chemin = "/mnt/data/hmt/depot/monde/resultats"
    return {os.path.basename(f): json.load(open(f)) for f in glob.glob(os.path.join(chemin, "*.json"))[:6]}


OUTILS = {"etat_du_monde": etat_du_monde, "journal_du_monde": journal_du_monde, "habitants": habitants,
          "doctrine": doctrine, "portes": portes}


def repondre(msg, dossier):
    m, i = msg.get("method"), msg.get("id")
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": i, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                                                      "serverInfo": {"name": "monde", "version": "1"}}}
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": i, "result": {"tools": [
            {"name": n, "description": (f.__doc__ or "").strip().split("\n")[0],
             "inputSchema": {"type": "object", "properties": {"n": {"type": "integer"}, "type": {"type": "string"},
                                                              "role": {"type": "string"}}}}
            for n, f in OUTILS.items()]}}
    if m == "tools/call":
        p = msg.get("params", {})
        f = OUTILS.get(p.get("name"))
        if f is None: return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "outil inconnu"}}
        try: r = f(dossier, **(p.get("arguments") or {}))
        except Exception as ex: r = {"erreur": str(ex)}
        return {"jsonrpc": "2.0", "id": i, "result": {"content": [{"type": "text",
                "text": json.dumps(r, ensure_ascii=False, default=str)[:60000]}]}}
    if i is None: return None
    return {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": f"methode inconnue {m}"}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dossier", default=DOSSIER)
    a = p.parse_args()
    for ligne in sys.stdin:
        ligne = ligne.strip()
        if not ligne: continue
        try: msg = json.loads(ligne)
        except json.JSONDecodeError: continue
        r = repondre(msg, a.dossier)
        if r is not None:
            sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n"); sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
