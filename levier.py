#!/usr/bin/env python3
"""levier — SOUS LE FEU, LES FORMES COMMANDEES SONT-ELLES ENCORE DIFFERENTES ?

C est la question qui decide de la brique, et elle passe AVANT toute regle de choix : si
`FILE` et `LINE` produisent la meme geometrie une fois les balles parties, aucune regle ne
peut rien piloter. Le choix n aurait pas de levier.

DESCRIPTEUR — l ALLONGEMENT, dans le repere DU CHEF :
    chaque homme vivant est projete sur (le long du cap, en travers du cap) ;
    allongement = RMS(le long) / RMS(en travers).
  FILE -> tres allonge.  LINE -> tres large.  WEDGE / DIAMOND -> entre les deux.
  Il ne depend ni de la position du chef ni de son cap : une escouade en TRANSIT ne le fausse
  pas — c etait le confondant du bras C.

CONTROLE POSITIF INTEGRE : le meme descripteur en MONDE VIDE doit separer les quatre formes.
S il n y arrive pas la, c est LUI qui est en cause, pas le monde.

SEUIL DIMENSIONNE : le plancher est obtenu par PERMUTATION des etiquettes de forme (1000 tirages).
On ne declare une separation que si elle bat ce plancher.
"""
import sys, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from marge import scene
from assemblage import E

NATIF = {"colonne": "FILE", "ligne": "LINE", "coin": "WEDGE", "losange": "DIAMOND"}
FORMES = ("colonne", "ligne", "coin", "losange")
SCENES = (0, 1, 2, 3)

LIRE = ('private _v = (units HMT_GB select {alive _x}); private _l = leader HMT_GB;'
        'private _c = getDir _l; HMT_R = "";'
        '{ private _d = (getPosASL _x) vectorDiff (getPosASL _l);'
        '  private _dx = _d select 0; private _dy = _d select 1;'
        '  private _lo = _dx * (sin _c) + _dy * (cos _c);'      # le long du cap
        '  private _tr = _dx * (cos _c) - _dy * (sin _c);'      # en travers
        '  HMT_R = HMT_R + format ["%1,%2;", round (10*_lo), round (10*_tr)];'
        '} forEach _v;')

def allongement(b):
    r = b.query(LIRE + E("HMTL %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTL (\d+) (\S*)", want=1, timeout=60)
    if not r: return None, 0
    n = int(r[0].group(1))
    pts = [p for p in r[0].group(2).split(";") if p]
    if len(pts) < 4: return None, n
    lo = np.array([float(p.split(",")[0]) / 10 for p in pts])
    tr = np.array([float(p.split(",")[1]) / 10 for p in pts])
    a = float(np.sqrt((lo ** 2).mean())); t = float(np.sqrt((tr ** 2).mean()))
    return (a / t if t > 0.5 else None), n

def essai(b, nom, sc, vide):
    scene(b, sc); time.sleep(2)
    if vide:
        b.query('{ deleteVehicle _x } forEach (units HMT_GO);' + E("HMTV %1", "1"), r"HMTV (\d+)", want=1, timeout=40)
    time.sleep(3)
    b.query('HMT_GB setFormation "%s";' % NATIF[nom] + E("HMTN %1", "1"), r"HMTN (\d+)", want=1, timeout=40)
    ech = []
    for _ in range(8):                       # 40 s d observation, on garde la MEDIANE
        time.sleep(5)
        a, n = allongement(b)
        if a is not None: ech.append(a)
    return (float(np.median(ech)) if ech else None), len(ech)

def separation(par_forme):
    """Statistique = etendue des medianes entre formes. Plancher par PERMUTATION des etiquettes."""
    lab, val = [], []
    for f, v in par_forme.items():
        for x in v: lab.append(f); val.append(x)
    lab = np.array(lab); val = np.array(val)
    if len(val) < 6: return None, None, None
    obs = float(np.ptp([np.median(val[lab == f]) for f in par_forme if (lab == f).any()]))
    rng = np.random.default_rng(0); nul = []
    for _ in range(1000):
        p = rng.permutation(lab)
        nul.append(np.ptp([np.median(val[p == f]) for f in par_forme if (p == f).any()]))
    nul = np.array(nul)
    return obs, float(np.percentile(nul, 95)), float((nul >= obs).mean())

if __name__ == "__main__":
    print("=" * 92); print(" LE LEVIER — les formes commandees restent-elles differentes SOUS LE FEU ?"); print("=" * 92)
    R = {}; b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        for cond, vide in (("VIDE (controle positif)", True), ("SOUS LE FEU", False)):
            print("\n─── %s ───" % cond, flush=True)
            R[cond] = {}
            for nom in FORMES:
                R[cond][nom] = []
                for sc in SCENES:
                    a, k = essai(b, nom, sc, vide)
                    if a is not None: R[cond][nom].append(a)
                    print("  %-9s sc%d : allongement %s   (%d lectures)"
                          % (nom, sc, ("%5.2f" % a) if a is not None else "  —  ", k), flush=True)
                if R[cond][nom]:
                    print("     -> %-9s mediane %.2f" % (nom, np.median(R[cond][nom])), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass

    print("\n" + "=" * 92)
    verdict = {}
    for cond in R:
        obs, p95, pval = separation(R[cond])
        verdict[cond] = {"etendue": obs, "plancher95": p95, "p": pval}
        print("\n  %s" % cond)
        for f in FORMES:
            v = R[cond].get(f, [])
            if v: print("     %-9s mediane %5.2f   (n=%d, min %.2f max %.2f)" % (f, np.median(v), len(v), min(v), max(v)))
        if obs is None: print("     pas assez de lectures"); continue
        print("     etendue entre formes %.2f   |  plancher de permutation (95e) %.2f   |  p = %.3f"
              % (obs, p95, pval))
        print("     -> %s" % ("✅ LES FORMES SONT SEPAREES" if obs > p95 else "⛔ INDISTINGUABLES du hasard d etiquettes"))
    json.dump({"mesures": R, "verdict": verdict}, open('/mnt/data/levier.json', 'w'), indent=1)
    vd = verdict.get("VIDE (controle positif)", {}); fu = verdict.get("SOUS LE FEU", {})
    print("\n" + "─" * 92)
    if vd.get("etendue") is None or fu.get("etendue") is None:
        print("  lecture impossible")
    elif not (vd["etendue"] > vd["plancher95"]):
        print("  ⚠️ LE CONTROLE POSITIF ECHOUE : meme en monde vide le descripteur ne separe pas les")
        print("     formes. C est LUI qui est en cause. Aucun verdict sur la brique.")
    elif fu["etendue"] > fu["plancher95"]:
        print("  ✅ LE LEVIER EXISTE : sous le feu les formes commandees restent distinctes.")
        print("     Une regle de choix a donc quelque chose a piloter. La brique tient.")
    else:
        print("  ⛔ PAS DE LEVIER : le descripteur separe les formes en monde vide mais PAS sous le feu.")
        print("     Le combat efface la forme commandee. Une regle qui choisit entre elles choisirait")
        print("     entre des objets identiques. LA BRIQUE MEURT ICI — avant la campagne.")
