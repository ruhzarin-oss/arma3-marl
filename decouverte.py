#!/usr/bin/env python3
"""decouverte — LA MÉTRIQUE DU NOUVEL OBJECTIF, et son PLANCHER DE BRUIT.

Déposé AVANT toute donnée : DEPOT_DECOUVERTE.md (49167d37197927d4).

  DÉCOUVERTE = nombre d ennemis LOCALISÉS (west knowsAbout > 1,5) qui ne l étaient pas au
  début de l épisode. Vérité-terrain GRATUITE : le serveur connaît toutes les positions.

⚠️ ENNEMIS RANDOMISÉS À CHAQUE ÉPISODE (anneau 200-500 m) — sinon on « découvre » une scène
   apprise par cœur. Exigence structurelle du dépôt.
⚠️ LA MORT EST UN COÛT, PLUS UN SCORE : on rend `découverte par homme perdu` à côté.
⚠️ Ce fichier ne compare RIEN. Il mesure le plancher de bruit et la recevabilité de la scène.
   Aucun seuil ne se dépose sans le couple « plancher mesuré · n requis » (règle 3).
"""
import sys, math, time, json, hashlib
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
NB_ENN, NB_AMI, SEUIL = 12, 8, 1.5

def scene(b):
    """8 bleus, 12 ennemis DISPERSES DANS UN ANNEAU 200-500 m, positions retirees a chaque episode."""
    b.query('HMT_POS = [] call BIS_fnc_randomPos;'
            'HMT_POS = [HMT_POS, 0, 900, 15, 0, 0.3, 0] call BIS_fnc_findSafePos;'
            '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
            'HMT_GB = createGroup west; HMT_GO = createGroup east;'
            'for "_i" from 0 to %d do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*7-10, floor(_i/4)*7, 0], [], 0, "NONE"] };'
            'for "_i" from 0 to %d do {'
            '  private _a = random 360; private _r = 200 + random 300;'
            '  private _p = HMT_POS vectorAdd [_r * sin _a, _r * cos _a, 0];'
            '  _p = [_p, 0, 60, 6, 0, 0.4, 0] call BIS_fnc_findSafePos;'
            '  HMT_GO createUnit ["O_Soldier_F", _p, [], 0, "NONE"] };'
            '{ _x setSkill 0.6; _x allowFleeing 0 } forEach allUnits;'
            '{ _x setVariable ["hid", _forEachIndex] } forEach units HMT_GB;'
            'HMT_GB setBehaviour "AWARE"; HMT_GB setCombatMode "YELLOW"; HMT_GB setSpeedMode "NORMAL";'
            % (NB_AMI - 1, NB_ENN - 1) + E("HMTSC b=%1 o=%2", "count units HMT_GB", "count units HMT_GO"),
            r"HMTSC b=(\d+) o=(\d+)", want=1, timeout=60)

def mesure(b):
    """-> (ennemis localises, bleus vivants). knowsAbout est DE CAMP (fiche du dossier)."""
    r = b.query(E("HMTM loc=%1 viv=%2 pos=%3",
                  "{ (west knowsAbout _x) > %.1f } count (units HMT_GO)" % SEUIL,
                  "{alive _x} count (units HMT_GB)",
                  "round ((getPos leader HMT_GB) distance HMT_POS)"),
                r"HMTM loc=(\d+) viv=(\d+) pos=(\d+)", want=1, timeout=40)
    return tuple(int(g) for g in r[0].groups()) if r else (None, None, None)

# ─── LES CINQ EXECUTANTS NOMMES ⟨depot 8bf314554c2efdb8⟩ ────────────────────────────────
# C est le VOCABULAIRE que l officier aurait a comparer. Enumerables : la lecon RFT du dossier
# dit que le goulot est d ENUMERER les actions, pas de les faire proposer.
ORDRES = {
    "assaut":     '{ _x doMove (getPos leader HMT_GO) } forEach units HMT_GB;',
    "patrouille": 'private _i = 0; { _i = _i + 1; private _a = _i * 45 + (time * 6);'
                  '  _x doMove (HMT_POS vectorAdd [280 * sin _a, 280 * cos _a, 0]) } forEach units HMT_GB;',
    "eventail":   'private _i = 0; { _i = _i + 1; private _a = _i * 45;'
                  '  _x doMove (HMT_POS vectorAdd [380 * sin _a, 380 * cos _a, 0]) } forEach units HMT_GB;',
    "tenir":      '{ _x doMove (getPos _x); _x setUnitPos "MIDDLE" } forEach units HMT_GB;',
    "couvert":    '{ private _c = (nearestTerrainObjects [getPos _x, ["HILL","HIGH_ROCK","BUSH","TREE"], 220]);'
                  '  if (count _c > 0) then { _x doMove (getPos (_c select (floor (random (count _c))))) }'
                  '  else { _x doMove (getPos leader HMT_GO) } } forEach units HMT_GB;',
    # ⭐ LE TEMOIN QUI TUE LE THEATRE : memes ordres, meme cadence, DESTINATIONS AU HASARD.
    "hasard":     '{ private _a = random 360; private _r = 100 + random 350;'
                  '  _x doMove (HMT_POS vectorAdd [_r * sin _a, _r * cos _a, 0]) } forEach units HMT_GB;',
    "natif":      '',          # aucun ordre : l IA d Arma seule
}


def episode(b, bras, duree=360, pas=12):
    """`bras` : une cle d ORDRES, ou 'fige'."""
    scene(b); time.sleep(3)
    if bras == "fige":
        b.query('{ _x disableAI "PATH" } forEach units HMT_GB;' + E("HMTF %1", "1"), r"HMTF (\d+)", want=1, timeout=30)
    loc0, viv0, _ = mesure(b)
    sqf = ORDRES.get(bras, "")
    t0 = time.time()
    while time.time() - t0 < duree:
        if sqf:
            b.query(sqf + E("HMTO %1", "1"), r"HMTO (\d+)", want=1, timeout=30)
        time.sleep(pas)
    loc1, viv1, dpar = mesure(b)
    if loc1 is None: return None
    perdus = max(viv0 - viv1, 0)
    # ⚠️ un groupe VIDE rend des distances absurdes (30 488 m mesures) : `leader` est nul.
    return dict(decouverte=loc1 - loc0, perdus=perdus, vivants=viv1,
                par_perte=(loc1 - loc0) / max(perdus, 1),
                eloignement=(dpar if viv1 > 0 and dpar < 3000 else None))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--bras", default="natif"); ap.add_argument("--duree", type=int, default=360)
    a = ap.parse_args()
    H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_DECOUVERTE.md','rb').read()).hexdigest()[:16]
    print("=" * 92); print(" DÉCOUVERTE — plancher de bruit du bras `%s`  (dépôt %s)" % (a.bras, H))
    print("=" * 92, flush=True)
    print("  %d répétitions · 8 bleus · %d ennemis dans un anneau 200-500 m, RETIRÉS à chaque épisode"
          % (a.n, NB_ENN), flush=True)
    R = []; b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        for k in range(a.n):
            r = episode(b, a.bras, duree=a.duree)
            if not r: print("  %2d : pas de réponse" % k, flush=True); continue
            R.append(r)
            print("  %2d : découverte %2d/%d   perdus %d   vivants %d   éloignement %d m"
                  % (k, r["decouverte"], NB_ENN, r["perdus"], r["vivants"], r["eloignement"]), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass
    if len(R) >= 4:
        d = np.array([x["decouverte"] for x in R], float)
        m, s = d.mean(), d.std(ddof=1)
        print("\n─── LE PLANCHER DE BRUIT ───")
        print("  découverte : moyenne %.2f / %d   écart-type %.2f   étendue [%d ; %d]"
              % (m, NB_ENN, s, d.min(), d.max()))
        print("  pertes moyennes %.2f   découverte par homme perdu %.2f"
              % (np.mean([x["perdus"] for x in R]), np.mean([x["par_perte"] for x in R])))
        print("\n─── RECEVABILITÉ DE LA SCÈNE (critère déposé : natif entre 2 et 9 sur 12) ───")
        print("  -> %s" % ("✅ RECEVABLE" if 2 <= m <= 9 else
                           "⛔ SATURE EN BAS — élargir la durée ou resserrer l'anneau" if m < 2 else
                           "⛔ SATURE EN HAUT — éloigner ou disperser davantage"))
        print("\n─── LE SEUIL QUI EN DÉCOULE (règle 3) ───")
        for n in (2, 4, 8, 16, 32):
            print("     n = %-3d épisodes par bras -> détectable à partir de %+.2f découverte"
                  % (n, 2.8 * s / math.sqrt(n)))
        json.dump({"depot": H, "bras": a.bras, "n": len(R), "moyenne": m, "ecart_type": s,
                   "episodes": R}, open('/mnt/data/decouverte_%s.json' % a.bras, 'w'), indent=1)
    else:
        print("\n  trop peu d'épisodes valides")
