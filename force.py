#!/usr/bin/env python3
"""force — UNE VRAIE FORCE QUI AVANCE. Quatre groupes, pas une escouade.

Ce qui est juge : la COORDINATION entre groupes, pas la forme d un groupe.
Ce qui compte (pivot assume) : AGIR, AVANCER, DECOUVRIR. Les morts sont rapportes mais ne
sont PAS le critere — c est la guerre.

LES BRAS
  masse     · les 4 groupes avancent EN MEME TEMPS vers l objectif.        <- le plancher
  bond      · 2 groupes avancent pendant que 2 tiennent en APPUI, a tour de role.  <- LA regle
  hasard    · meme alternance, mais QUI bouge est TIRE AU SORT.  <- anti-theatre : si `bond`
              ne bat pas ca, ce n est pas de la coordination, c est du mouvement alterne.
  bond_bis  · BRAS NUL : exactement `bond`, autre etiquette, lu en aveugle.

LA LECTURE PERDANTE, ECRITE AVANT LES DONNEES
  ⟨registre⟩ « TOUT CE QUI FIGE UN HOMME COUTE » — dose-reponse monotone mesuree. L appui
  FIGE la moitie de la force. `bond` peut donc perdre pour cette raison exacte, et ce sera une
  VRAIE reponse, pas un echec du banc : elle dira que l appui ne paie pas son immobilite.

ORDRE DE LECTURE, ECRIT AVANT LES DONNEES
  1. `hasard` — si `bond` ne le bat pas, rien d autre n est lu.
  2. le BRAS NUL est-il sous la MOITIE de l ecart observe ? sinon le banc s auto-invalide.
  3. `bond - masse` seulement alors.
"""
import sys, time, json, random
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
NG, PAR_G, NB_ENN = 4, 8, 24          # 4 groupes de 8 = 32 hommes ; 24 defenseurs
# ⚠️ MESURE DU 28/08, PREMIER EPISODE : 133 m parcourus en 300 s sur 700 — la force n atteint
# JAMAIS le contact, et le banc mesurait une marche d approche. Deux corrections dimensionnees
# sur ce chiffre, pas choisies : la distance tombe a ce qui est couvrable, et la relance
# s espace car re-emettre un `doMove` trop souvent CASSE le calcul de chemin (defaut deja paye
# sur le banc de marge, 12 s).
DEPART, DUREE, PAS = 350, 420, 40      # m de l objectif ; s d episode ; s entre deux relances
BRAS = ("masse", "bond", "hasard", "bond_bis")

def scene(b, graine):
    """SCENARIO GELE par la graine : tous les bras jouent le MEME. L objectif est un POINT,
    les defenseurs sont AUTOUR de lui — pas autour de nous : on ATTAQUE, on n est pas encercle."""
    g = ('HMT_OBJ = [] call BIS_fnc_randomPos;'
         'HMT_OBJ = [HMT_OBJ, 0, 900, 20, 0, 0.3, 0] call BIS_fnc_findSafePos;'
         'HMT_CAP = %d;'
         'HMT_DEP = HMT_OBJ vectorAdd [%d * sin HMT_CAP, %d * cos HMT_CAP, 0];'
         'HMT_DEP = [HMT_DEP, 0, 200, 15, 0, 0.4, 0] call BIS_fnc_findSafePos;'
         '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
         'HMT_GRP = []; HMT_GO = createGroup east;'
         'for "_g" from 0 to %d do {'
         '  private _gr = createGroup west;'
         '  private _o = HMT_DEP vectorAdd [(_g - 1.5) * 45 * cos HMT_CAP, -(_g - 1.5) * 45 * sin HMT_CAP, 0];'
         '  for "_i" from 0 to %d do {'
         '    private _u = _gr createUnit ["B_Soldier_F", _o vectorAdd [(_i mod 4)*6-9, floor(_i/4)*6, 0], [], 0, "NONE"];'
         '    _u setVariable ["hid", _g * 100 + _i] };'
         '  _gr setBehaviour "AWARE"; _gr setCombatMode "YELLOW"; _gr setSpeedMode "NORMAL";'
         '  HMT_GRP pushBack _gr };'
         'for "_i" from 0 to %d do {'
         '  private _a = ((_i * 137 + %d * 53) mod 360);'
         '  private _r = 40 + ((_i * 71 + %d * 29) mod 160);'
         '  private _p = HMT_OBJ vectorAdd [_r * sin _a, _r * cos _a, 0];'
         '  _p = [_p, 0, 40, 6, 0, 0.4, 0] call BIS_fnc_findSafePos;'
         '  HMT_GO createUnit ["O_Soldier_F", _p, [], 0, "NONE"] };'
         '{ _x setSkill 0.6; _x allowFleeing 0 } forEach allUnits;'
         'HMT_GO setBehaviour "COMBAT"; HMT_GO setCombatMode "RED";'
         % (graine * 37 % 360, DEPART, DEPART, NG - 1, PAR_G - 1, NB_ENN - 1, graine, graine))
    r = b.query(g + E("HMTSC b=%1 o=%2 d=%3",
                      "count (allUnits select {side _x == west})", "count units HMT_GO",
                      "round ((leader (HMT_GRP select 0)) distance2D HMT_OBJ)"),
                r"HMTSC b=(\d+) o=(\d+) d=(\d+)", want=1, timeout=90)
    return tuple(int(x) for x in r[0].groups()) if r else (0, 0, 0)

def avancer(b, gi):
    """Le groupe gi progresse vers l objectif. Rien d autre.
    ⚠️ HMT_OBJ est une POSITION, pas un objet : `getPosATL HMT_OBJ` est une erreur SQF, et une
    erreur SQF avale la requete ENTIERE -> le compteur COTE SERVEUR se desynchronise. C est ce
    qui a tue le run de 22h20 des l ordre 4."""
    return ('private _g = HMT_GRP select %d; if (count (units _g select {alive _x}) > 0) then {'
            '  { if (unitReady _x) then { _x doMove HMT_OBJ } } forEach (units _g select {alive _x});'
            '  _g setSpeedMode "FULL" };' % gi)

def appuyer(b, gi):
    """Le groupe gi TIENT et observe vers l objectif. C est ce qui FIGE — et qui coute."""
    return ('private _g = HMT_GRP select %d;'
            '{ if (alive _x) then { _x doWatch HMT_OBJ; doStop _x } } forEach (units _g);' % gi)

def mesure(b):
    """⚠️ TOUT TABLEAU PEUT ETRE VIDE. Un `arithmeticMean` sur un tableau vide leve une erreur
    SQF, l erreur avale la requete ENTIERE en silence, le pont n emet rien et le compteur —
    qui est COTE SERVEUR — se desynchronise DEFINITIVEMENT. C est ce qui a tue le premier run
    a 16h29 : quand les 32 hommes sont morts, la moyenne portait sur rien."""
    r = b.query('private _v = (allUnits select {side _x == west && alive _x});'
                'HMT_D = if (count _v > 0) then { round ((_v apply { _x distance2D HMT_OBJ }) call BIS_fnc_arithmeticMean) } else { -1 };'
                + E("HMTM v=%1 d=%2 a=%3",
                    "count (allUnits select {side _x == west && alive _x})",
                    "{ (west knowsAbout _x) > 1.5 } count (units HMT_GO)", "HMT_D"),
                r"HMTM v=(\d+) d=(\d+) a=(-?\d+)", want=1, timeout=60)
    return tuple(int(x) for x in r[0].groups()) if r else (None, None, None)


def episode(b, bras, graine):
    viv0, enn0, d0 = scene(b, graine)
    if viv0 < NG * PAR_G - 2: return None
    time.sleep(3)
    # ⚠️ `knowsAbout` est de CAMP, pas de soldat : il peut deja etre non nul au spawn. On lit
    # donc le GAIN de decouverte, jamais l etat — sinon on crediterait la manoeuvre de ce que
    # le camp savait avant qu elle commence. ⟨knowsabout-est-de-camp-pas-de-soldat⟩
    _, dec0, _ = mesure(b)
    dec0 = dec0 or 0
    rng = random.Random(hash((bras, graine)) & 0xffff)
    t0 = time.time(); tour = 0; hist = []
    while time.time() - t0 < DUREE:
        if bras == "masse":
            cmd = "".join(avancer(b, g) for g in range(NG))
        elif bras in ("bond", "bond_bis"):
            bouge = [(tour * 2) % NG, (tour * 2 + 1) % NG]        # 2 avancent, 2 appuient
            cmd = "".join(avancer(b, g) if g in bouge else appuyer(b, g) for g in range(NG))
        else:                                                     # hasard : meme alternance, tirage
            bouge = rng.sample(range(NG), 2)
            cmd = "".join(avancer(b, g) if g in bouge else appuyer(b, g) for g in range(NG))
        b.query(cmd + E("HMTO %1", "1"), r"HMTO (\d+)", want=1, timeout=60)
        tour += 1
        time.sleep(PAS)
        m = mesure(b)
        if m[0] is not None and m[2] >= 0: hist.append(m)
        if m[0] == 0: break        # force aneantie : l episode est fini, on ne mesure plus rien
    if not hist: return None
    viv, dec, dist = hist[-1]
    return {"graine": graine, "bras": bras, "decouverte": dec - dec0, "dec_spawn": dec0,
            "dec_fin": dec, "avance": d0 - dist,
            "vivants": viv, "dist_fin": dist, "tours": tour}

if __name__ == "__main__":
    GRAINES = list(range(int(sys.argv[1]) if len(sys.argv) > 1 else 6))
    print("=" * 92); print(" LA FORCE — 4 groupes x 8 hommes contre %d defenseurs, %d m a parcourir" % (NB_ENN, DEPART))
    print("=" * 92, flush=True)
    R = []; b = None
    try:
        b = NativeBridge(port=5801, timeout=120)
        for gr in GRAINES:
            ordre = list(BRAS); random.Random(gr).shuffle(ordre)   # ordre des bras BROUILLE par bloc
            for bras in ordre:
                e = episode(b, bras, gr)
                if e:
                    R.append(e)
                    print("  graine %d  %-9s : decouverte %+3d (spawn %2d -> %2d/%d)   avance %4d m   vivants %2d/%d"
                          % (gr, bras, e["decouverte"], e["dec_spawn"], e["dec_fin"], NB_ENN,
                             e["avance"], e["vivants"], NG * PAR_G), flush=True)
                else:
                    print("  graine %d  %-9s : episode INVALIDE (scene incomplete)" % (gr, bras), flush=True)
                json.dump(R, open('/mnt/data/force.json', 'w'), indent=1)
    finally:
        if b:
            try: b.close()
            except Exception: pass

    if not R: sys.exit("aucun episode")
    print("\n" + "=" * 92)
    par = {x: [e for e in R if e["bras"] == x] for x in BRAS}
    for k in ("decouverte", "avance", "vivants"):
        print("\n  %s" % k.upper())
        for x in BRAS:
            v = [e[k] for e in par[x]]
            if v: print("     %-9s moyenne %7.2f   (n=%d, ecart-type %.2f)" % (x, np.mean(v), len(v), np.std(v)))
    print("\n" + "─" * 92); print("  ORDRE DE LECTURE — ecrit avant les donnees")
    def moy(x, k): 
        v = [e[k] for e in par[x]]
        return float(np.mean(v)) if v else None
    for k in ("decouverte", "avance"):
        bd, ha, ma, nu = (moy(x, k) for x in ("bond", "hasard", "masse", "bond_bis"))
        if None in (bd, ha, ma, nu): continue
        print("\n  ── %s ──" % k)
        print("     1. bond - hasard   = %+6.2f   %s" % (bd - ha, "✅" if bd > ha else "⛔ RIEN D AUTRE N EST LU"))
        print("     2. bras nul |bond_bis - bond| = %6.2f   (moitie de |bond-masse| = %.2f)  %s"
              % (abs(nu - bd), abs(bd - ma) / 2, "✅" if abs(nu - bd) < abs(bd - ma) / 2 else "⛔ BANC AUTO-INVALIDE"))
        print("     3. bond - masse    = %+6.2f" % (bd - ma))
    json.dump(R, open('/mnt/data/force.json', 'w'), indent=1)
