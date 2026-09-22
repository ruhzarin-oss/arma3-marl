"""Lecture UNIQUE de la confirmation de « toujours attendre » ( CONFIRMATION_ATTENDRE.md, ecrit avant ).
Tant que les 480 paires ne sont pas la, n affiche QUE le compte.   python -m oracle.autonome.lire_confirmation"""
import json, os, re, sys
import numpy as np
from . import config as C, donnees as Dn

N, PREMIERE, ALPHA, GRAINE = 480, 12, 0.05, 20260922


def paires():
    etat = json.load(open(f"{C.ETAT_DIR}/etat.json")) if os.path.exists(f"{C.ETAT_DIR}/etat.json") else {"historique": []}
    sales = {h["campagne"] for h in etat["historique"] if h.get("quarantaine")}
    E = Dn.utilisables(Dn.episodes(lambda c: str(c).startswith("ORACLE-I") and int(str(c)[8:] or 0) >= PREMIERE and c not in sales))
    E.sort(key=lambda e: e["dossier"])
    cases = {}
    for e in E:
        m = re.match(r"ORA-(\d+)-c(\d+)-o(\d)-r(\d)", str(e["version"]))
        if not m: continue
        cle = (int(m.group(1)), int(m.group(2)), int(m.group(4)), e["graine"])
        cases.setdefault(cle, {}).setdefault(int(m.group(3)), e)          # premier accepte gagne
    P = [(k, v[1], v[2]) for k, v in sorted(cases.items()) if 1 in v and 2 in v]
    return P


def test(d, tirages, rng):
    obs = d.mean(); s = rng.choice([-1.0, 1.0], size=(tirages, len(d)))
    return float((np.sum((s * d).mean(1) <= obs) + 1) / (tirages + 1))


if __name__ == "__main__":
    P = paires()
    print(f"paires de confirmation disponibles : {len(P)} / {N}")
    if len(P) < N:
        print("EN ATTENTE : aucune statistique n est calculee avant les 480 paires ( un seul regard )."); sys.exit(0)
    P = P[:N]; rng = np.random.default_rng(GRAINE)
    d = np.array([a["compromis"] - t["compromis"] for _, t, a in P], dtype=float)
    # --- controles de l instrument, AVANT H1 ---
    neg = np.mean([test(d * rng.choice([-1.0, 1.0], len(d)), 2000, rng) < ALPHA for _ in range(200)])
    pos = []
    for _ in range(200):
        ya = np.array([a["compromis"] for _, t, a in P], dtype=float); yt = np.array([t["compromis"] for _, t, a in P], dtype=float)
        q = min(1.0, 0.07 / max(ya.mean(), 0.07)); ya = np.where((ya == 1) & (rng.random(len(ya)) < q), 0.0, ya)
        dd = (ya - yt) - ((ya - yt).mean() - (d.mean() - 0.07))                  # centre l effet injecte a d - 0,07
        pos.append(test(dd, 2000, rng) < ALPHA)
    pos = float(np.mean(pos))
    print(f"controle negatif : rejets {neg:.1%} ( attendu 2 a 9 % ) ; controle positif : rejets {pos:.1%} ( attendu >= 70 % )")
    if not (0.02 <= neg <= 0.09 and pos >= 0.70):
        print("UN CONTROLE A ECHOUE : H1 N EST PAS LUE."); sys.exit(0)
    p = test(d, 100000, np.random.default_rng(GRAINE))
    print(f"\nH1 : moyenne de d = {d.mean():+.4f} sur {len(d)} paires ; permutation des signes, p = {p:.4f}")
    print("DECISION :", "H0 REJETEE -> l Architecte adopte « toujours attendre »" if p < ALPHA else
          "H0 non rejetee -> rien n est adopte ; la question passe au monde ( horloge )")
    b = [rng.choice(d, len(d)).mean() for _ in range(10000)]; b.sort()
    print(f"\n( description ) IC 95 % par paire [{b[250]:+.4f} ; {b[9750]:+.4f}]")
    W = np.array([t["graine"] for _, t, a in P])
    print("( description ) signe par monde :", {int(w): round(float(d[W == w].mean()), 3) for w in sorted(set(W))})
    for nom, f in (("poste proche", lambda t: t["menace_p2"] == 5), ("patrouille proche", lambda t: t["menace_p2"] == 4)):
        m = np.array([f(t) for _, t, a in P])
        if m.sum(): print(f"( description ) {nom} : {d[m].mean():+.4f} sur {m.sum()} paires")
