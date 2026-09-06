#!/usr/bin/env python3
"""assemblage — LE TEMPS D ASSEMBLAGE D UNE FORME. Il dimensionne l hysteresis.

⟨Fable⟩ « L hysteresis se dimensionne sur la PHYSIQUE, pas sur le score. Mesure d abord le
TEMPS D ASSEMBLAGE : mediane pour que tous les hommes atteignent leur place. »

Sans ce chiffre, basculer toutes les 15 s reviendrait a n atteindre AUCUNE forme — le meme
piege que le `doMove` reemis en boucle, qui a handicape le banc d hier.

⚠️ L ANCRE ET LE CAP SONT DEPOSES ICI, ET SERONT LES MEMES POUR TOUS LES BRAS DE FORME :
   · CAP  : la formation FAIT FACE au barycentre de menace pondere par les voyants ;
            depart = cap courant si la menace est nulle. Derive du champ, zero reglage.
   · ANCRE: elle AVANCE vers le secteur LE MOINS VU, a vitesse constante. Une forme est une
            disposition RELATIVE : sans ancre qui bouge, un losange immobile ne decouvre rien
            et la brique mourrait d une cause etrangere a sa regle.
   · ECHELLE : SP=7 m, RR=24 m — les valeurs du catalogue, declarees et gelees.
"""
import sys, math, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from marge import scene, NB_ENN
import formations as F
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
SP, RR, TOL = 7.0, 24.0, 6.0        # espacement, rayon, tolerance d arrivee (m)

MENACE = ('private _ens = (units HMT_GO select {alive _x});'
          'private _viv = (units HMT_GB select {alive _x});'
          'private _cx = 0; private _cy = 0;'
          '{ _cx = _cx + (getPosASL _x select 0); _cy = _cy + (getPosASL _x select 1) } forEach _viv;'
          'private _n = count _viv; if (_n == 0) then { _n = 1 }; _cx = _cx / _n; _cy = _cy / _n;'
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
          '  HMT_R = HMT_R + format ["%1;", _b]; };'
          'HMT_R = HMT_R + format ["|%1,%2", round _cx, round _cy];')

def etat(b):
    r = b.query(MENACE + E("HMTX %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTX (\d+) (\S*)", want=1, timeout=90)
    if not r: return None, None
    sect, ctr = r[0].group(2).split("|")
    v = np.array([float(x) for x in sect.split(";") if x])
    cx, cy = (float(x) for x in ctr.split(","))
    return (v if len(v) == 8 else None), (cx, cy)

def cap_et_ancre(m, ctr):
    """CAP = face au barycentre de menace. ANCRE = vers le secteur LE MOINS VU. Deposes."""
    ang = np.radians(np.arange(8) * 45)
    if m.sum() <= 0:
        return 0.0, (ctr[0], ctr[1] + 60.0)
    sx = float((m * np.sin(ang)).sum()); sy = float((m * np.cos(ang)).sum())
    cap = math.degrees(math.atan2(sx, sy)) % 360          # convention du depot : atan2(dx, dy)
    d = int(np.argmin(m)); a = math.radians(d * 45)
    return cap, (ctr[0] + 60.0 * math.sin(a), ctr[1] + 60.0 * math.cos(a))

def places(nom, n, cap, ancre):
    """Positions ABSOLUES des n places. On utilise `formations.place` — la rotation DU CATALOGUE,
    celle qu emploie deja le gymnase — plutot qu une transcription maison qui pourrait deriver."""
    pos, _ = F.place(nom, n, (ancre[0], ancre[1]), math.radians(cap), SP, RR)
    return [(float(x), float(y)) for x, y in pos]


if __name__ == "__main__":
    print("=" * 92); print(" TEMPS D ASSEMBLAGE — il dimensionne l hysteresis"); print("=" * 92)
    print("  formes du catalogue disponibles : %s" % ", ".join(sorted(F.FORMATIONS)), flush=True)
    T = {}; b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        # ⚠️ `eventail` N EXISTE PAS au catalogue — c etait mon bras ad hoc du banc de marge.
        # Correspondance DECLAREE avant tout hachage : `eventail` = 8 hommes chacun sur son
        # secteur de 45°, c est litteralement `cercle` (perimetre 360°, chacun regarde dehors).
        for nom in ("colonne", "losange", "coin", "cercle", "ligne"):
            if nom not in F.FORMATIONS: print("  %s : absente du catalogue" % nom); continue
            T[nom] = []
            for sc in range(3):
                scene(b, sc); time.sleep(3)
                m, ctr = etat(b)
                if m is None: continue
                cap, ancre = cap_et_ancre(m, ctr)
                pl = places(nom, 8, cap, ancre)
                cmd = "".join('((units HMT_GB select {alive _x}) select %d) doMove [%.0f,%.0f,0];' % (i, x, y)
                              for i, (x, y) in enumerate(pl))
                b.query(cmd + E("HMTF %1", "1"), r"HMTF (\d+)", want=1, timeout=40)
                # ⚠️ On enregistre la COURBE, pas un booleen. Un instrument qui ne sait dire que
                # « non » ne dit pas POURQUOI : ici on saura si l assemblage sature, et a combien.
                q_n = E("HMTA %1 %2", "{ _x } count [" + ",".join(
                    '(((units HMT_GB select {alive _x}) select %d) distance2D [%.0f,%.0f,0]) < %.0f' % (i, x, y, TOL)
                    for i, (x, y) in enumerate(pl)) + "]",
                    "round (10 * ([" + ",".join(
                    '(((units HMT_GB select {alive _x}) select %d) distance2D [%.0f,%.0f,0])' % (i, x, y)
                    for i, (x, y) in enumerate(pl)) + "] call BIS_fnc_arithmeticMean))")
                t0 = time.time(); arrive = None; courbe = []
                while time.time() - t0 < 150:
                    time.sleep(5)
                    r = b.query(q_n, r"HMTA (\d+) (\d+)", want=1, timeout=40)
                    if not r: continue
                    n_ok, dm = int(r[0].group(1)), int(r[0].group(2)) / 10.0
                    courbe.append((round(time.time() - t0), n_ok, dm))
                    if arrive is None and n_ok >= 6: arrive = time.time() - t0
                    if arrive and time.time() - t0 > arrive + 5: break
                T[nom].append({"t": arrive, "courbe": courbe})
                nmax = max((c[1] for c in courbe), default=0)
                dfin = courbe[-1][2] if courbe else -1
                print("  %-9s sc%d : %-22s  max en place %d/8   distance finale %.0f m"
                      % (nom, sc, ("atteinte en %.0f s" % arrive) if arrive else "JAMAIS ATTEINTE",
                         nmax, dfin), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass
    if T:
        print("\n─── LE TEMPS D ASSEMBLAGE ───")
        tous = []; jamais = 0; total = 0
        for nom, v in T.items():
            ok = [e["t"] for e in v if e["t"]]
            nm = [max((c[1] for c in e["courbe"]), default=0) for e in v]
            total += len(v); jamais += len(v) - len(ok)
            print("  %-9s atteinte %d/%d   mediane %s   max en place (mediane) %.1f/8"
                  % (nom, len(ok), len(v), ("%.0f s" % np.median(ok)) if ok else "  —  ", np.median(nm)))
            tous += ok
        print()
        if not tous:
            print("  ⛔ AUCUNE FORME N EST JAMAIS ATTEINTE — sous le feu, un `doMove` ne pose pas")
            print("     une formation. L hysteresis ne peut pas se dimensionner sur un temps qui")
            print("     n existe pas, et la brique n a pas de socle : elle CHOISIRAIT des formes")
            print("     que l escouade n adopte jamais. Verdict a rendre AVANT toute campagne.")
            med = None
        else:
            med = float(np.median(tous))
            print("  ⭐ MEDIANE TOUTES FORMES : %.0f s   (%d/%d essais n aboutissent jamais)" % (med, jamais, total))
            print("  -> HYSTERESIS : bascule autorisee si la forme est ATTEINTE (6/8 a moins de")
            print("     %.0f m) OU apres %.0f s, ET le nouveau regime confirme sur DEUX lectures." % (TOL, med))
        json.dump({"par_forme": T, "mediane": med, "tol": TOL, "SP": SP, "RR": RR},
                  open('/mnt/data/assemblage.json', 'w'), indent=1)
