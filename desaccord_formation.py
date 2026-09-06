#!/usr/bin/env python3
"""desaccord_formation — LA LAME AVANT LA NUIT : la règle basculerait-elle seulement ?

⟨Fable⟩ « Rejoue la règle SUR LES LOGS et compte combien de fois elle aurait basculé — une
règle qui ne bascule presque jamais n a pas de leçon à donner, et tu le sais AVANT de payer
une nuit. » C est la lame que D1 m a apprise : il apprenait un signal redondant à 88 %, et
c était mesurable avant le premier gradient.

⚠️ LES SEUILS SE DÉPOSENT PAR LEURS ENTRÉES, JAMAIS PAR LEURS SORTIES. On lit ici la
DISTRIBUTION réelle des états de menace (comptes de voyants par secteur, entropie sectorielle)
et on en tire des TERCILES. Aucun score n intervient. La table état→forme est écrite APRÈS
cette lecture, et hachée avant le premier épisode noté.

Aucune formation n est jouée ici. On mesure l ÉTAT, et le taux de bascule qu il implique.
"""
import sys, math, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from marge import scene, ORDRES, NB_ENN, PAS
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))

# 8 SECTEURS autour du CENTRE DE MASSE de l escouade : combien d ennemis verraient un homme
# posté à 25 m dans ce secteur. Même primitive que le champ géométrique certifié.
SQF_MENACE = (
    'private _ens = (units HMT_GO select {alive _x});'
    'private _viv = (units HMT_GB select {alive _x});'
    'private _cx = 0; private _cy = 0;'
    '{ _cx = _cx + (getPosASL _x select 0); _cy = _cy + (getPosASL _x select 1) } forEach _viv;'
    'private _n = count _viv; if (_n == 0) then { _n = 1 };'
    '_cx = _cx / _n; _cy = _cy / _n;'
    'HMT_R = "";'
    'for "_d" from 0 to 7 do {'
    '  private _a = _d * 45;'
    '  private _c = [_cx + 25 * sin _a, _cy + 25 * cos _a, 0];'
    '  _c set [2, (getTerrainHeightASL _c) + 1.5];'
    '  private _b = 0;'
    '  { private _pe = eyePos _x;'
    '    if !(terrainIntersectASL [_pe, _c]) then {'
    '      if (count (lineIntersectsSurfaces [_pe, _c, _x, objNull]) == 0) then { _b = _b + 1 } };'
    '  } forEach _ens;'
    '  HMT_R = HMT_R + format ["%1;", _b];'
    '};'
)

def menace(b):
    r = b.query(SQF_MENACE + E("HMTX %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTX (\d+) (\S*)", want=1, timeout=90)
    if not r: return None
    v = [float(x) for x in r[0].group(2).split(";") if x]
    return np.array(v) if len(v) == 8 else None

def descripteurs(m):
    """Les DEUX grandeurs d état, et rien d autre : intensité et concentration."""
    tot = m.sum()
    if tot <= 0: return 0.0, 0.0
    p = m / tot
    ent = -(p[p > 0] * np.log(p[p > 0])).sum() / math.log(8)   # 0 = tout d un côté, 1 = partout
    return float(tot), float(ent)

if __name__ == "__main__":
    print("=" * 92); print(" DÉSACCORD DE FORMATION — la règle basculerait-elle ?"); print("=" * 92)
    print("  on relit l ÉTAT DE MENACE sur les scénarios GELÉS, sans jouer aucune formation", flush=True)
    ETATS = []; b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        for sc in range(8):
            scene(b, sc); time.sleep(3)
            # on laisse l escouade jouer `eventail` (le seul bras qui batte le hasard)
            t0 = time.time()
            while time.time() - t0 < 240:
                b.query(ORDRES["eventail"] + E("HMTO %1", "1"), r"HMTO (\d+)", want=1, timeout=30)
                m = menace(b)
                if m is not None:
                    tot, ent = descripteurs(m)
                    ETATS.append(dict(sc=sc, t=round(time.time() - t0), secteurs=m.tolist(),
                                      intensite=tot, entropie=ent))
                time.sleep(PAS)
            print("  sc%d : %d états relevés" % (sc, len([e for e in ETATS if e["sc"] == sc])), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass

    if len(ETATS) < 30:
        print("\n  ⛔ trop peu d états (%d) pour déposer des terciles" % len(ETATS)); sys.exit(0)
    I = np.array([e["intensite"] for e in ETATS]); H = np.array([e["entropie"] for e in ETATS])
    print("\n─── LA DISTRIBUTION DES ÉTATS (%d relevés) ───" % len(ETATS))
    print("  INTENSITÉ (somme des voyants sur 8 secteurs) : médiane %.1f  p33 %.1f  p67 %.1f  max %.0f"
          % (np.median(I), np.percentile(I, 33), np.percentile(I, 67), I.max()))
    print("  ENTROPIE  (0 = menace d un seul côté, 1 = de partout) : médiane %.2f  p33 %.2f  p67 %.2f"
          % (np.median(H), np.percentile(H, 33), np.percentile(H, 67)))
    print("  part des états à intensité NULLE (personne ne voit) : %.1f %%" % (100 * (I == 0).mean()))

    # ─── LA TABLE, écrite depuis les TERCILES et rien d autre ───
    i33, i67 = np.percentile(I, 33), np.percentile(I, 67)
    h50 = np.median(H)
    def forme(tot, ent):
        if tot <= i33: return "colonne"                       # peu vu : on file vite
        if tot >= i67: return "losange" if ent >= h50 else "ligne"   # très vu : 360° ou face
        return "coin" if ent < h50 else "eventail"            # entre-deux
    F = [forme(e["intensite"], e["entropie"]) for e in ETATS]
    print("\n─── LA TABLE ÉTAT→FORME, issue des terciles (aucun score n est intervenu) ───")
    print("  intensité ≤ %.1f -> colonne | ≥ %.1f -> losange si entropie ≥ %.2f sinon ligne"
          % (i33, i67, h50))
    print("  entre les deux -> coin si entropie < %.2f sinon eventail" % h50)
    from collections import Counter
    for k, v in Counter(F).most_common():
        print("     %-10s %5.1f %% des états" % (k, 100 * v / len(F)))

    print("\n─── ⭐ LE TAUX DE BASCULE — la lame ───")
    bascules = tot_pas = 0
    for sc in range(8):
        seq = [f for e, f in zip(ETATS, F) if e["sc"] == sc]
        bascules += sum(1 for a, b2 in zip(seq, seq[1:]) if a != b2); tot_pas += max(len(seq) - 1, 0)
    taux = 100.0 * bascules / max(tot_pas, 1)
    print("  la règle change de forme sur %.1f %% des pas (%d bascules sur %d)" % (taux, bascules, tot_pas))
    print("  formes distinctes réellement visitées : %d sur 4" % len(set(F)))
    print("\n  -> %s" % ("✅ IL Y A UNE LEÇON : la règle bascule assez pour se distinguer d une forme fixe"
                         if taux >= 10 and len(set(F)) >= 3 else
                         "⛔ PAS DE LEÇON : la règle ne bascule presque jamais — inutile de payer la nuit"
                         if taux < 10 else
                         "⚠️ elle bascule mais ne visite que %d formes — vocabulaire trop pauvre" % len(set(F))))
    json.dump({"etats": ETATS, "terciles": dict(i33=i33, i67=i67, h50=h50),
               "taux_bascule": taux, "formes": dict(Counter(F))},
              open('/mnt/data/desaccord_formation.json', 'w'), indent=1)
