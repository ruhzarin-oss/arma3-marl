#!/usr/bin/env python3
"""prix_hybride — LE PRIX D UNE POSITION. Le moteur dit OU, les tarifs mesures disent COMBIEN.

    prix(candidat) = (nombre d ennemis qui le VOIENT) x TARIF_VU
                   + (suppression subie par l homme)  x TARIF_SUPP

· LA GEOMETRIE vient d ARMA, mesuree le 27/08 : etendue 13,5 sur 8 directions, 0 % de
  directions equivalentes. C est un CONTREFACTUEL — une position ou personne n est alle.
· LES TARIFS viennent des JOURNAUX, deposes le 26/08 (DEPOT_BARREAU.md) :
      vu x2,45   ·   supprime x29,81
  Ce sont des RAPPORTS DE TAUX DE MORT mesures sur 432 transitions, blocs tenus a l ecart.

ZERO ENTRAINEMENT. Structure de `_champ_danger` du gymnase (+15,3 en greffe), avec des tarifs
MESURES SUR ARMA au lieu d etre supposes.

⚠️ REGLE 16, ETAGE 2 : le CONTROLE POSITIF tourne AVANT tout usage. La question est celle qui
a tue `monde2` (50,5 %, le hasard) : le prix separe-t-il « vers l ennemi » de « a l oppose » ?
"""
import sys, math, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from champ_hybride import scene
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
TARIF_VU, TARIF_SUPP = 2.45, 29.81

def _vu_sqf(pt):
    """compte les ennemis qui voient le point `pt` — relief d abord (bon marche), puis surfaces."""
    return ('private _b = 0;'
            '{ private _pe = eyePos _x;'
            '  if !(terrainIntersectASL [_pe, %s]) then {'
            '    if (count (lineIntersectsSurfaces [_pe, %s, _x, _u]) == 0) then { _b = _b + 1 } };'
            '} forEach _ens;' % (pt, pt))

SQF_PRIX = (
    'HMT_R = ""; private _ens = (units HMT_GO select {alive _x});'
    '{'
    '  private _u = _x; private _p = eyePos _u;'
    '  private _sup = getSuppression _u; private _ligne = "";'
    '  for "_d" from 0 to 7 do {'
    '    private _a = _d * 45;'
    '    private _c = [(_p select 0) + 25 * sin _a, (_p select 1) + 25 * cos _a, 0];'
    '    _c set [2, (getTerrainHeightASL _c) + 1.5];'
    + _vu_sqf('_c') +
    '    _ligne = _ligne + format ["%1;", _b];'
    '  };'
    '  HMT_R = HMT_R + _ligne + format ["%1|", round (1000 * _sup)];'
    '} forEach (units HMT_GB select {alive _x});'
)

def lire_prix(b):
    """-> liste par homme : (8 comptes d ennemis qui voient, suppression)"""
    r = b.query(SQF_PRIX + E("HMTP %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTP (\d+) (\S*)", want=1, timeout=120)
    if not r: raise RuntimeError("le prix n a rien rendu")
    n, blob = int(r[0].group(1)), r[0].group(2)
    out = []
    for seg in blob.split("|"):
        if not seg: continue
        v = [x for x in seg.split(";") if x]
        if len(v) != 9: continue
        out.append((np.array([float(x) for x in v[:8]]), float(v[8]) / 1000.0))
    if n and not out: raise RuntimeError("%d hommes annonces, 0 lus" % n)
    return out

def prix(vus, supp):
    """LE PRIX. Une ligne, aucun parametre libre : les deux tarifs sont deposes."""
    return vus * TARIF_VU + supp * TARIF_SUPP

if __name__ == "__main__":
    print("=" * 94); print(" LE PRIX HYBRIDE — controle positif AVANT tout usage"); print("=" * 94)
    print("  prix = (ennemis qui voient) x %.2f  +  (suppression) x %.2f" % (TARIF_VU, TARIF_SUPP), flush=True)
    b = None
    try:
        b = NativeBridge(port=5801, timeout=120)
        scene(b, nrouge=20, dist=150); time.sleep(4)
        L = lire_prix(b)
        P = np.array([prix(v, s) for v, s in L])
        print("\n  %d hommes.  prix : min %.1f  mediane %.1f  max %.1f" % (len(P), P.min(), np.median(P), P.max()))
        eten = P.max(1) - P.min(1)
        print("  etendue du prix entre les 8 directions : mediane %.1f   min %.1f" % (np.median(eten), eten.min()))

        print("\n─── LE CONTROLE POSITIF — la question qui a tue `monde2` ───")
        r = b.query('HMT_D = ""; private _ens = (units HMT_GO select {alive _x});'
                    '{ private _u = _x; private _p = eyePos _u;'
                    '  private _l = getPosASL (leader HMT_GO);'
                    '  private _v = [(_l select 0) - (_p select 0), (_l select 1) - (_p select 1), 0];'
                    '  private _n = vectorMagnitude _v; if (_n < 1) then { _n = 1 };'
                    '  _v = _v vectorMultiply (25 / _n);'
                    '  private _vers = [(_p select 0) + (_v select 0), (_p select 1) + (_v select 1), 0];'
                    '  _vers set [2, (getTerrainHeightASL _vers) + 1.5];'
                    '  private _loin = [(_p select 0) - (_v select 0), (_p select 1) - (_v select 1), 0];'
                    '  _loin set [2, (getTerrainHeightASL _loin) + 1.5];'
                    + _vu_sqf('_vers').replace('_b', '_bv') +
                    _vu_sqf('_loin').replace('_b', '_bl') +
                    '  HMT_D = HMT_D + format ["%1,%2|", _bv, _bl];'
                    '} forEach (units HMT_GB select {alive _x});'
                    + E("HMTD %1 %2", "count (units HMT_GB select {alive _x})", "HMT_D"),
                    r"HMTD (\d+) (\S*)", want=1, timeout=120)
        if r:
            pa = [s.split(",") for s in r[0].group(2).split("|") if s]
            v = np.array([[float(a), float(c)] for a, c in pa if len([a, c]) == 2])
            d = v[:, 0] - v[:, 1]
            print("  ennemis qui voient — VERS %.2f   OPPOSE %.2f   ecart %+.2f" % (v[:, 0].mean(), v[:, 1].mean(), d.mean()))
            print("  part des hommes ou VERS > OPPOSE : %.1f %%   (monde2 rendait 50,5 %%)" % (100 * (d > 0).mean()))
            print("  part des hommes ou l ecart est NUL : %.1f %%" % (100 * (d == 0).mean()))
            print("\n  -> %s" % ("✅ LE PRIX SEPARE, dans le BON SENS : s approcher expose davantage."
                                 if (d > 0).mean() > 0.65 else
                                 "⚠️ separation faible ou ambigue — a instruire avant la greffe"))
    finally:
        if b:
            try: b.close()
            except Exception: pass
