#!/usr/bin/env python3
"""marge — LA MARGE DU CHOIX SUR ARMA, en BLOCS. Dépôt db3be24b0682814c.

⭐ LA RÉPARATION PRINCIPALE : 8 SCÉNARIOS GELÉS, tous les bras jouent LES MÊMES.
   Sans blocs, l oracle choisit PAR ÉPISODE et ramasse les épisodes chanceux de chaque bras :
   le max sur 7 bras d un bruit à écart-type 1,78 fabrique une marge de plusieurs points TOUT
   SEUL. C est le max-de-grille, déjà payé une fois. L appariement impossible au niveau des
   dés d Arma est possible au niveau des SCÈNES.

Les cinq autres réparations sont dans le code, chacune commentée à sa place.
"""
import sys, math, time, json, hashlib, argparse
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
NB_ENN, NB_AMI, SEUIL, DUREE, PAS = 12, 8, 1.5, 480, 15

# ─── LES ORDRES. Réparations 1, 2 et 4 : aucun ne lit `leader HMT_GO` (vérité-terrain que le
#     camp bleu n a pas) ; tous n émettent QUE si `unitReady` ; les cibles se TIENNENT.
CONNU = ('private _c = (units HMT_GO select {alive _x && (west knowsAbout _x) > 1.5});'
         'private _cible = if (count _c > 0) then { getPos (_c select 0) } '
         '                 else { HMT_POS vectorAdd [0, 400, 0] };')   # repli DÉCLARÉ : axe nord
ORDRES = {
    # `assaut` vise le DERNIER CONTACT CONNU DU CAMP, plus la vérité-terrain (réparation 1)
    "assaut":     CONNU + '{ if (unitReady _x) then { _x doMove _cible } } forEach units HMT_GB;',
    "patrouille": 'private _i = 0; { _i = _i + 1; if (unitReady _x) then {'
                  '  private _a = _i * 45 + (time * 4);'
                  '  _x doMove (HMT_POS vectorAdd [280 * sin _a, 280 * cos _a, 0]) } } forEach units HMT_GB;',
    "eventail":   'private _i = 0; { _i = _i + 1; if (unitReady _x) then {'
                  '  private _a = _i * 45;'
                  '  _x doMove (HMT_POS vectorAdd [380 * sin _a, 380 * cos _a, 0]) } } forEach units HMT_GB;',
    "tenir":      '{ _x setUnitPos "MIDDLE" } forEach units HMT_GB;',
    # le couvert est tiré UNE FOIS et gardé jusqu à l arrivée (réparation 4)
    "couvert":    '{ if (unitReady _x) then {'
                  '  private _o = (nearestTerrainObjects [getPos _x, ["HILL","HIGH_ROCK","BUSH","TREE"], 220]);'
                  '  if (count _o > 0) then { _x doMove (getPos (_o select (floor (random (count _o))))) } } }'
                  ' forEach units HMT_GB;',
    # ⭐ LE TÉMOIN ANTI-THÉÂTRE, RENFORCÉ : il TIENT sa destination jusqu à l arrivée (réparation 2)
    "hasard":     '{ if (unitReady _x) then { private _a = random 360; private _r = 150 + random 300;'
                  '  _x doMove (HMT_POS vectorAdd [_r * sin _a, _r * cos _a, 0]) } } forEach units HMT_GB;',
    "natif":      '',            # l IA d Arma seule
    "natif_bis":  '',            # ⭐ LE BRAS NUL : identique à `natif`, autre étiquette (réparation 5)
    "fige":       None,          # plancher : `disableAI PATH` (réparation 3 — le natif patrouille à 147 m)
}

def scene(b, graine):
    """⭐ SCÉNARIO GELÉ : la graine fixe les placements, donc tous les bras jouent LE MÊME."""
    b.query('HMT_POS = [] call BIS_fnc_randomPos;'
            'HMT_POS = [HMT_POS, 0, 900, 15, 0, 0.3, 0] call BIS_fnc_findSafePos;'
            '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
            'HMT_GB = createGroup west; HMT_GO = createGroup east;'
            'for "_i" from 0 to %d do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*7-10, floor(_i/4)*7, 0], [], 0, "NONE"] };'
            'for "_i" from 0 to %d do {'
            '  private _a = ((_i * 137 + %d * 53) mod 360);'
            '  private _r = 200 + ((_i * 71 + %d * 29) mod 300);'
            '  private _p = HMT_POS vectorAdd [_r * sin _a, _r * cos _a, 0];'
            '  _p = [_p, 0, 60, 6, 0, 0.4, 0] call BIS_fnc_findSafePos;'
            '  HMT_GO createUnit ["O_Soldier_F", _p, [], 0, "NONE"] };'
            '{ _x setSkill 0.6; _x allowFleeing 0 } forEach allUnits;'
            '{ _x setVariable ["hid", _forEachIndex] } forEach units HMT_GB;'
            'HMT_GB setBehaviour "AWARE"; HMT_GB setCombatMode "YELLOW"; HMT_GB setSpeedMode "NORMAL";'
            % (NB_AMI - 1, NB_ENN - 1, graine, graine)
            + E("HMTSC b=%1 o=%2", "count units HMT_GB", "count units HMT_GO"),
            r"HMTSC b=(\d+) o=(\d+)", want=1, timeout=60)

def vus(b):
    """DÉCOUVERTE, définition déposée mot pour mot : ennemis DISTINCTS dont le knowsAbout DE
    CAMP franchit 1,5, chacun compté UNE FOIS."""
    r = b.query(E("HMTM loc=%1 viv=%2", "{ (west knowsAbout _x) > 1.5 } count (units HMT_GO)",
                  "{alive _x} count (units HMT_GB)"), r"HMTM loc=(\d+) viv=(\d+)", want=1, timeout=40)
    return tuple(int(g) for g in r[0].groups()) if r else (None, None)

def episode(b, bras, graine):
    scene(b, graine); time.sleep(3)
    if bras == "fige":
        b.query('{ _x disableAI "PATH" } forEach units HMT_GB;' + E("HMTF %1", "1"), r"HMTF (\d+)", want=1, timeout=30)
    l0, v0 = vus(b)
    sqf = ORDRES.get(bras) or ""
    t0 = time.time()
    while time.time() - t0 < DUREE:
        if sqf:
            b.query(sqf + E("HMTO %1", "1"), r"HMTO (\d+)", want=1, timeout=30)
        time.sleep(PAS)
    l1, v1 = vus(b)
    if l1 is None: return None
    return dict(decouverte=l1 - l0, perdus=max(v0 - v1, 0), vivants=v1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--scenarios", type=int, default=8)
    ap.add_argument("--bras", nargs="+", default=list(ORDRES)); a = ap.parse_args()
    H = hashlib.sha256(open('/home/younes/arma3-marl/AMENDEMENT_BLOCS.md','rb').read()).hexdigest()[:16]
    print("=" * 96); print(" LA MARGE DU CHOIX SUR ARMA — EN BLOCS  (amendement %s)" % H); print("=" * 96)
    print("  %d scenarios GELES · %d bras · %d min l episode · seuil depose +1,44"
          % (a.scenarios, len(a.bras), DUREE // 60), flush=True)
    res = {br: {} for br in a.bras}; b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        for sc in range(a.scenarios):
            for br in a.bras:
                r = episode(b, br, sc)
                if not r: print("  sc%d %-10s : pas de reponse" % (sc, br), flush=True); continue
                res[br][sc] = r
                print("  sc%d %-10s : decouverte %2d/%d  perdus %d" % (sc, br, r["decouverte"], NB_ENN, r["perdus"]), flush=True)
            json.dump(res, open('/mnt/data/marge_blocs.json', 'w'), indent=1)
    finally:
        if b:
            try: b.close()
            except Exception: pass
    scs = sorted(set.intersection(*[set(v) for v in res.values() if v]) if any(res.values()) else [])
    if len(scs) >= 4:
        print("\n─── LA TABLE, PAR SCENARIO (tous les bras sur les MEMES placements) ───")
        print("  %-12s %s" % ("bras", " ".join("sc%d" % s for s in scs)))
        moy = {}
        for br in a.bras:
            if not res[br]: continue
            v = [res[br][s]["decouverte"] for s in scs]; moy[br] = np.mean(v)
            print("  %-12s %s   moyenne %.2f" % (br, " ".join("%3d" % x for x in v), moy[br]))
        oracle = np.mean([max(res[br][s]["decouverte"] for br in moy) for s in scs])
        fixe = max(moy.values()); nom = max(moy, key=moy.get)
        print("\n─── LE VERDICT ───")
        print("  ORACLE DU CHOIX (le meilleur bras par scenario) .. %.2f" % oracle)
        print("  MEILLEUR BRAS FIXE (`%s`) ................ %.2f" % (nom, fixe))
        print("  ⭐ MARGE DU CHOIX ......................... %+.2f   (seuil depose +1,44)" % (oracle - fixe))
        if "natif" in moy and "natif_bis" in moy:
            print("\n  BRAS NUL : natif %.2f contre natif_bis %.2f — ecart %+.2f"
                  % (moy["natif"], moy["natif_bis"], moy["natif_bis"] - moy["natif"]))
            if abs(moy["natif_bis"] - moy["natif"]) > 1.44:
                print("  ⛔ BANC NON SEPARANT : le bras NUL obtient un avantage. AUCUN VERDICT.")
                sys.exit(0)
        if "hasard" in moy:
            print("\n  contre le temoin `hasard` (%.2f) :" % moy["hasard"])
            for br in sorted(moy, key=moy.get, reverse=True):
                if br in ("hasard", "natif_bis"): continue
                print("     %-12s %+.2f  %s" % (br, moy[br] - moy["hasard"],
                      "bat le hasard" if moy[br] - moy["hasard"] > 1.44 else "NE LE BAT PAS — agitation"))
        print("\n  -> %s" % ("✅ L OFFICIER A UN METIER : la meilleure doctrine VARIE selon le scenario"
                             if oracle - fixe >= 1.44 else
                             "⛔ MARGE NULLE : une doctrine FIXE fait aussi bien que le choix parfait."
                             " L officier n a rien a decider sur Arma non plus — le 7B reste debranche."))
