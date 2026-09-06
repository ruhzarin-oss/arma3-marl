#!/usr/bin/env python3
"""controle_issues — LE CHAMP PRICE-T-IL LES ENDROITS OU L ON ENCAISSE DU FEU ?

Protocole depose AVANT de jouer : DEPOT_CONTROLE_ISSUES.md (9ba69c0583e20b98).
La verite vient d une AUTRE MODALITE que les entrees du champ — c est ce qui distingue ce
controle de l ancien, circulaire.

UN SEUL JEU DE DEROULES REPOND AUX DEUX QUESTIONS :
  A. CONTROLE-ISSUES  — AUC du prix sur « cet homme encaisse du feu au pas suivant »,
     contre trois temoins : hasard · distance au plus proche ennemi · champ PERMUTE entre
     les hommes (bras nul).
  B. REPLICATION LATERALE — le contraste vers/oppose rejoue TEL QUEL a 60 et 80 m.

⚠️ SUIVI PAR IDENTIFIANT, jamais par position dans la liste : `units select {alive _x}` se
   reindexe quand un homme meurt. Troisieme instance de cette classe dans le dossier.
"""
import sys, math, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
TARIF_VU, TARIF_SUPP = 2.45, 29.81

VOIT = ('private _b = 0;'
        '{ private _pe = eyePos _x;'
        '  if !(terrainIntersectASL [_pe, %s]) then {'
        '    if (count (lineIntersectsSurfaces [_pe, %s, _x, _u]) == 0) then { _b = _b + 1 } };'
        '} forEach _ens;')

def scene(b, nrouge, dist):
    b.query('HMT_POS = [] call BIS_fnc_randomPos;'
            'HMT_POS = [HMT_POS, 0, 800, 12, 0, 0.25, 0] call BIS_fnc_findSafePos;'
            '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
            'HMT_GB = createGroup west; HMT_GO = createGroup east;'
            'for "_i" from 0 to 7 do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*6-9, floor(_i/4)*6, 0], [], 0, "NONE"] };'
            # ⭐ IDENTIFIANT PERSISTANT assigne a la creation : `getPlayerID` ne marche PAS sur
            # des unites IA (le premier lancement est mort dessus), et l index dans
            # `units select {alive _x}` se REINDEXE a chaque mort.
            '{ _x setVariable ["hid", _forEachIndex] } forEach units HMT_GB;'
            'for "_i" from 0 to %d do { HMT_GO createUnit ["O_Soldier_F", HMT_POS vectorAdd [(_i mod 6)*8-20, %d + floor(_i/6)*8, 0], [], 0, "NONE"] };'
            '{ _x setSkill 0.7; _x allowFleeing 0 } forEach allUnits;'
            '{ _x setUnitPos "DOWN"; _x disableAI "PATH" } forEach units HMT_GO;'
            'HMT_GB setBehaviour "COMBAT"; HMT_GB setCombatMode "RED"; HMT_GB setSpeedMode "FULL";'
            '{ _x reveal [leader HMT_GO, 4]; _x doMove (getPos leader HMT_GO) } forEach units HMT_GB;'
            '{ _x reveal [leader HMT_GB, 4] } forEach units HMT_GO;'
            % (nrouge - 1, dist) + E("HMTSC %1", "count allUnits"), r"HMTSC (\d+)", want=1, timeout=45)

def etat(b):
    """PAR IDENTIFIANT : id, voyants a la position actuelle, suppression, vie, distance au plus proche."""
    r = b.query('HMT_R = ""; private _ens = (units HMT_GO select {alive _x});'
                '{ private _u = _x; private _p = eyePos _u;'
                + (VOIT % ('_p', '_p')) +
                '  private _dm = 99999;'
                '  { private _d = _u distance _x; if (_d < _dm) then { _dm = _d } } forEach _ens;'
                '  HMT_R = HMT_R + format ["%1,%2,%3,%4,%5|",'
                '     (_u getVariable ["hid", -1]), _b, round (1000*(getSuppression _u)),'
                '     round (1000*(damage _u)), round _dm];'
                '} forEach (units HMT_GB select {alive _x});'
                + E("HMTE %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTE (\d+) (\S*)", want=1, timeout=90)
    if not r: raise RuntimeError("etat vide")
    out = {}
    for seg in [s for s in r[0].group(2).split("|") if s]:
        v = seg.split(",")
        if len(v) != 5: continue
        hid = int(float(v[0]))
        if hid < 0: continue
        out[hid] = dict(voit=float(v[1]), supp=float(v[2])/1000, dmg=float(v[3])/1000, dmin=float(v[4]))
    return out

def lateral(b):
    """LE CONTRASTE VERS/OPPOSE, rejoue TEL QUEL — replication, pas remplacement."""
    r = b.query('HMT_D = ""; private _ens = (units HMT_GO select {alive _x});'
                '{ private _u = _x; private _p = eyePos _u; private _l = getPosASL (leader HMT_GO);'
                '  private _v = [(_l select 0)-(_p select 0), (_l select 1)-(_p select 1), 0];'
                '  private _n = vectorMagnitude _v; if (_n < 1) then { _n = 1 };'
                '  _v = _v vectorMultiply (25/_n);'
                '  private _a1 = [(_p select 0)+(_v select 0), (_p select 1)+(_v select 1), 0];'
                '  _a1 set [2, (getTerrainHeightASL _a1)+1.5];'
                '  private _a2 = [(_p select 0)-(_v select 0), (_p select 1)-(_v select 1), 0];'
                '  _a2 set [2, (getTerrainHeightASL _a2)+1.5];'
                '  private _g = [(_p select 0)-(_v select 1), (_p select 1)+(_v select 0), 0];'
                '  _g set [2, (getTerrainHeightASL _g)+1.5];'
                + (VOIT % ('_a1', '_a1')).replace('_b', '_bv')
                + (VOIT % ('_a2', '_a2')).replace('_b', '_bl')
                + (VOIT % ('_g', '_g')).replace('_b', '_bg') +
                '  HMT_D = HMT_D + format ["%1,%2,%3|", _bv, _bl, _bg];'
                '} forEach (units HMT_GB select {alive _x});'
                + E("HMTL %1 %2", "count (units HMT_GB select {alive _x})", "HMT_D"),
                r"HMTL (\d+) (\S*)", want=1, timeout=90)
    if not r: return []
    return [[float(x) for x in s.split(",")] for s in r[0].group(2).split("|") if s and len(s.split(",")) == 3]

def auc(p, y):
    o = np.argsort(p, kind="stable"); z = np.array(y)[o]
    pos = z.sum(); neg = len(z) - pos
    if pos == 0 or neg == 0: return float("nan")
    return float((np.arange(1, len(z)+1)[z == 1].sum() - pos*(pos+1)/2) / (pos*neg))

if __name__ == "__main__":
    import hashlib
    H = hashlib.sha256(open('/home/younes/arma3-marl/DEPOT_CONTROLE_ISSUES.md','rb').read()).hexdigest()[:16]
    print("=" * 96); print(" CONTROLE-ISSUES — le champ price-t-il ou l on ENCAISSE DU FEU ?  (depot %s)" % H)
    print("=" * 96, flush=True)
    # ⭐ ON STOCKE LES COMPOSANTES SEPAREMENT : la lecture PRIMAIRE est le champ
    # GEOMETRIQUE SEUL sur les hommes NON SUPPRIMES (amendement du 27/08).
    # ⚠️ NE PAS reutiliser `VOIT` : c est le gabarit SQF au niveau module. La liste
    # de stockage l ecrasait, et `VOIT % (...)` tombait sur une liste.
    L_VOIT, L_SUPP, EVEN, DIST, LAT = [], [], [], [], {60: [], 80: []}
    b = None
    try:
        b = NativeBridge(port=5801, timeout=120)
        # 16 scenes a 80 m : la lecture primaire n avait que 29 evenements pour un
        # intervalle de ±0,182. Il en faut ~4x plus pour separer. 80 m est la scene
        # RECEVABLE au critere depose (mediane 13 voyants) et celle ou l ecart axial
        # existe chez 94 % des hommes.
        for dist, nr in [(80, 20)] * 16:
            scene(b, nr, dist); time.sleep(4)
            LAT[dist] += lateral(b)
            prec = etat(b)
            for pas in range(8):
                time.sleep(9)
                cur = etat(b)
                for k, v in prec.items():
                    if k not in cur: continue
                    encaisse = 1 if (cur[k]["supp"] > v["supp"] + 0.02 or cur[k]["dmg"] > v["dmg"] + 0.01) else 0
                    L_VOIT.append(v["voit"]); L_SUPP.append(v["supp"])
                    DIST.append(-v["dmin"]); EVEN.append(encaisse)
                prec = cur
            print("  scene %d m / %d rouges : %d observations cumulees, %d evenements"
                  % (dist, nr, len(EVEN), sum(EVEN)), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass

    V, SU, Y, D = np.array(L_VOIT), np.array(L_SUPP), np.array(EVEN), np.array(DIST)
    P = V * TARIF_VU + SU * TARIF_SUPP          # descriptif seulement, ne valide JAMAIS
    propre = SU <= 0.02                          # les hommes NON supprimes en k
    print("\n─── A · LE CONTROLE-ISSUES ───")
    print("  ⭐ LECTURE PRIMAIRE : champ GEOMETRIQUE SEUL, hommes NON SUPPRIMES (%d sur %d)"
          % (propre.sum(), len(Y)))
    print("  observations %d   evenements « encaisse du feu » %d   taux %.1f %%"
          % (len(Y), Y.sum(), 100*Y.mean() if len(Y) else 0))
    if Y.sum() >= 15 and Y.sum() < len(Y):
        rng = np.random.default_rng(5)
        perm = P[rng.permutation(len(P))]
        def lire(nom, msk):
            yy = Y[msk]
            if yy.sum() < 8 or yy.sum() == len(yy):
                print("  %s : SUSPENDU (%d evenements)" % (nom, yy.sum())); return None
            r2 = {"CHAMP geometrique": auc(V[msk], yy),
                  "temoin : distance au + proche": auc(D[msk], yy),
                  "bras NUL : champ permute": auc(V[msk][rng.permutation(int(msk.sum()))], yy),
                  "plancher : hasard": auc(rng.random(int(msk.sum())), yy),
                  "(descriptif) prix complet": auc(P[msk], yy)}
            print("\n  %s — %d observations, %d evenements" % (nom, msk.sum(), yy.sum()))
            for k2, v2 in r2.items(): print("     %-32s AUC %.4f" % (k2, v2))
            t2 = max(r2["temoin : distance au + proche"], r2["bras NUL : champ permute"], r2["plancher : hasard"])
            i2 = 1.96 * 0.5 / math.sqrt(max(yy.sum(), 1))
            print("     meilleur temoin %.4f  intervalle ±%.3f" % (t2, i2))
            print("     -> %s" % ("✅ LE CHAMP BAT SES TEMOINS" if r2["CHAMP geometrique"] > t2 + i2
                                  else "SUSPENDU : le n ne separe pas" if abs(r2["CHAMP geometrique"] - t2) < i2
                                  else "⛔ le champ NE BAT PAS ses temoins"))
            return r2
        res = lire("PRIMAIRE (non supprimes)", propre)
        if res is None: res = lire("SECONDAIRE (tous)", np.ones(len(Y), bool))
        tem = 0; ic = 0
        json.dump({"depot": H, "n": len(Y), "evenements": int(Y.sum()), "auc": res},
                  open('/mnt/data/controle_issues.json','w'), indent=1)
    else:
        print("  ⛔ VERDICT SUSPENDU : %d evenements, insuffisant pour une AUC." % Y.sum())

    print("\n─── B · REPLICATION DE L HYPOTHESE LATERALE ───")
    for d in (60, 80):
        A = np.array(LAT[d])
        if not len(A): continue
        print("  a %d m — voyants : VERS %.2f   OPPOSE %.2f   LATERAL %.2f   (n=%d)"
              % (d, A[:,0].mean(), A[:,1].mean(), A[:,2].mean(), len(A)))
        ax = A[:,0] - A[:,1]
        print("     ecart AXIAL (vers-oppose) %+.2f | part non nulle %.0f %%"
              % (ax.mean(), 100*(ax != 0).mean()))
    print("\n  rappel a 150 m : vers 0,12 · oppose 0,38 · 75 %% d ecart NUL")
