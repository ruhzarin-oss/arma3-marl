#!/usr/bin/env python3
"""champ2 — LE CHAMP GEOMETRIQUE, sur les primitives QUI REPONDENT.

Mesure du 27/08, deux hommes a 154 m :
  BIS_fnc_checkVisibility ... ERREUR SQF (n existe pas sous cette forme)
  checkVisibility moteur .... 0        <- peut etre VRAI, le relief coupe
  lineIntersectsSurfaces .... 1 obstacle
  terrainIntersectASL ....... 1        <- le relief coupe reellement
  knowsAbout ................ 3,98     <- c est MON `reveal`, pas une preuve de vue
                                          (knowsAbout est DE CAMP et ne decroit pas)
→ On batit sur `lineIntersectsSurfaces` et `terrainIntersectASL`, les deux primitives de
  l outillage MAISON (`bake_los`), pas sur une fonction qui rend nil.

LA QUESTION DE CE FICHIER, ET ELLE PRECEDE TOUT USAGE :
  ⭐ LE NOMBRE D OBSTACLES VARIE-T-IL D UNE DIRECTION A L AUTRE ?
  C est ca, la DISCONTINUITE du couvert — et c est exactement ce qui manquait a `monde2`,
  dont le controle positif rendait 50,5 % (le hasard) sur 16 797 cas.
  Si la geometrie ne varie pas non plus, le chantier n est pas le modele : c est la SCENE,
  qui se joue sur un terrain sans couvert exploitable.
"""
import sys, math, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from champ_hybride import scene
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))

SQF_CHAMP = (
    'HMT_R = "";'
    'private _ens = (units HMT_GO select {alive _x});'
    '{'
    '  private _u = _x; private _p = eyePos _u; private _ligne = "";'
    '  for "_d" from 0 to 7 do {'
    '    private _a = _d * 45;'
    '    private _c = [(_p select 0) + 25 * sin _a, (_p select 1) + 25 * cos _a, 0];'
    '    _c set [2, (getTerrainHeightASL _c) + 1.5];'
    '    private _bloques = 0;'
    '    { private _pe = eyePos _x;'
    '      if (terrainIntersectASL [_pe, _c]) then { _bloques = _bloques + 1 }'
    '      else { if (count (lineIntersectsSurfaces [_pe, _c, _x, _u]) > 0) then { _bloques = _bloques + 1 } };'
    '    } forEach _ens;'
    '    _ligne = _ligne + format ["%1;", (count _ens) - _bloques];'   # NOMBRE D ENNEMIS QUI VOIENT
    '  };'
    '  HMT_R = HMT_R + _ligne + "|";'
    '} forEach (units HMT_GB select {alive _x});'
)

def lire(b):
    r = b.query(SQF_CHAMP + E("HMTC %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTC (\d+) (\S*)", want=1, timeout=120)
    if not r: raise RuntimeError("le champ n a rien rendu")
    n, blob = int(r[0].group(1)), r[0].group(2)
    out = [[float(v) for v in seg.split(";") if v] for seg in blob.split("|") if seg]
    if n and not out: raise RuntimeError("%d hommes annonces, 0 lus" % n)
    return out

if __name__ == "__main__":
    print("=" * 94); print(" CHAMP GEOMETRIQUE — combien d ennemis VOIENT chaque candidat ?"); print("=" * 94)
    print("  primitives : terrainIntersectASL puis lineIntersectsSurfaces (outillage maison)", flush=True)
    b = None
    try:
        b = NativeBridge(port=5801, timeout=120)
        for essai, (nr, di) in enumerate(((20, 150), (20, 80), (12, 60))):
            scene(b, nrouge=nr, dist=di); time.sleep(4)
            C = np.array([c for c in lire(b) if len(c) == 8])
            if not len(C): print("  scene %d : rien lu" % essai); continue
            eten = C.max(1) - C.min(1)
            print("\n─── scene : %d rouges a %d m ───" % (nr, di))
            print("  ennemis qui voient un candidat : min %.1f  mediane %.1f  max %.1f sur %d"
                  % (C.min(), np.median(C), C.max(), nr))
            print("  ⭐ ETENDUE entre les 8 directions : mediane %.1f   max %.1f" % (np.median(eten), eten.max()))
            print("  part des hommes ou les 8 directions sont IDENTIQUES : %.0f %%"
                  % (100 * (eten == 0).mean()))
            print("  -> %s" % ("✅ LA GEOMETRIE DISCRIMINE : tourner change qui vous voit"
                               if np.median(eten) >= 1 else
                               "⛔ PLAT : a 25 m pres, le meme nombre d ennemis vous voit"), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass
