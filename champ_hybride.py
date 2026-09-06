#!/usr/bin/env python3
"""champ_hybride — LE MOTEUR DIT OÙ, LES TARIFS MESURÉS DISENT COMBIEN.

⟨Fable, 27/08⟩ « Le champ spatial n a PAS a etre appris : le moteur le calcule exactement et
gratuitement. Ne jamais mettre dans un modele ce que le monde calcule exactement. »

  prix(candidat) = SOMME sur les ennemis connus de [ exposition geometrique ] x [ tarif mesure ]

· L EXPOSITION vient d ARMA : `checkVisibility` entre l oeil de l ennemi et le candidat.
  C est un CONTREFACTUEL — une position ou personne n est jamais alle — ce qu aucun corpus
  d etats reels ne peut porter. C est la raison structurelle pour laquelle `vue` par paire
  ne pouvait pas servir.
· LES TARIFS viennent des JOURNAUX, deja deposes (DEPOT_BARREAU.md) :
      supprime x29,81   knowsAbout>1 x2,77   vu x2,45
  et le tarif de distance vient de la courbe Arma du depot (le toucher decroit avec la portee).

ZERO ENTRAINEMENT. C est la structure exacte de `_champ_danger` du gymnase, qui etait calcule
par le code du monde et non appris — et qui valait +15,3 points en greffe.

⚠️ CE FICHIER NE MESURE RIEN ENCORE. Il construit le champ ET son CONTROLE POSITIF. La regle
16 gagne ses etages : audit des TRAITS avant d entrainer, controle du CHAMP avant de consommer
un run, bras nul pendant. `monde2` a echoue le premier etage sans un seul gradient.
"""
import sys, math, json, time
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))
TARIF_VU, TARIF_SUPP = 2.45, 29.81      # deposes le 26/08, mesures sur 432 transitions

def champ_sqf(nom_grp, rayon=25.0, ndir=8):
    """Le SQF qui calcule, POUR CHAQUE HOMME, l exposition de `ndir` candidats a `rayon` metres.

    `checkVisibility` rend la fraction visible entre deux points ASL : c est exactement la
    grandeur qu on veut, et c est le MOTEUR qui la donne. On sort DES NOMBRES uniquement
    (regle du pont : un champ vide desynchronise le compteur).
    """
    return (
        'HMT_R = "";'
        'private _ens = (units HMT_GO select {alive _x});'
        '{'
        '  private _u = _x; private _p = getPosASL _u;'
        '  private _ligne = "";'
        '  for "_d" from 0 to %d do {'
        '    private _a = _d * (360 / %d);'
        '    private _c = _p vectorAdd [%f * sin _a, %f * cos _a, 0];'
        '    _c set [2, (getTerrainHeightASL [_c select 0, _c select 1]) + 1.5];'
        '    private _expo = 0;'
        '    { private _v = [eyePos _x, _c] call BIS_fnc_checkVisibility;'
        '      if (isNil "_v") then { _v = 0 };'
        '      _expo = _expo + _v } forEach _ens;'
        '    _ligne = _ligne + format ["%%1;", round (1000 * _expo)];'
        '  };'
        '  HMT_R = HMT_R + _ligne + "|";'
        '} forEach (units %s select {alive _x});'
        % (ndir - 1, ndir, rayon, rayon, nom_grp)
    )

def lire_champ(b, ndir=8):
    r = b.query(champ_sqf("HMT_GB", ndir=ndir)
                + E("HMTCH %1 %2", "count (units HMT_GB select {alive _x})", "HMT_R"),
                r"HMTCH (\d+) (\S*)", want=1, timeout=60)
    if not r: raise RuntimeError("le champ n a rien rendu")
    n, blob = int(r[0].group(1)), r[0].group(2)
    out = []
    for seg in blob.split("|"):
        if not seg: continue
        vals = [v for v in seg.split(";") if v]
        out.append([float(v) / 1000.0 for v in vals])
    if n and not out: raise RuntimeError("%d hommes annonces, 0 lus" % n)
    return out

def scene(b, nrouge=20, dist=150):
    b.query('HMT_POS = [] call BIS_fnc_randomPos;'
            'HMT_POS = [HMT_POS, 0, 800, 12, 0, 0.25, 0] call BIS_fnc_findSafePos;'
            '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
            'HMT_GB = createGroup west; HMT_GO = createGroup east;'
            'for "_i" from 0 to 7 do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*6-9, floor(_i/4)*6, 0], [], 0, "NONE"] };'
            'for "_i" from 0 to %d do { HMT_GO createUnit ["O_Soldier_F", HMT_POS vectorAdd [(_i mod 6)*8-20, %d + floor(_i/6)*8, 0], [], 0, "NONE"] };'
            '{ _x setSkill 0.7; _x allowFleeing 0 } forEach allUnits;'
            '{ _x setUnitPos "DOWN"; _x disableAI "PATH" } forEach units HMT_GO;'
            'HMT_GB setBehaviour "COMBAT"; HMT_GB setCombatMode "RED"; HMT_GB setSpeedMode "FULL";'
            '{ _x reveal [leader HMT_GO, 4] } forEach units HMT_GB;'
            '{ _x reveal [leader HMT_GB, 4] } forEach units HMT_GO;'
            % (nrouge - 1, dist) + E("HMTSC %1", "count allUnits"), r"HMTSC (\d+)", want=1, timeout=45)

if __name__ == "__main__":
    print("=" * 92); print(" LE CHAMP HYBRIDE — le moteur dit OÙ, les tarifs disent COMBIEN"); print("=" * 92)
    print("  ⚠️ CONTRÔLE POSITIF DU CHAMP, avant tout usage (règle 16, étage 2)", flush=True)
    b = None
    try:
        b = NativeBridge(port=5801, timeout=60)
        scene(b); time.sleep(4)
        C = np.array([c for c in lire_champ(b) if len(c) == 8])
        print("\n  %d hommes, 8 directions, exposition geometrique par candidat" % len(C))
        print("  exposition : min %.3f  mediane %.3f  max %.3f" % (C.min(), np.median(C), C.max()))
        eten = (C.max(1) - C.min(1)) / np.maximum(C.mean(1), 1e-9)
        print("  etendue relative entre les 8 directions : mediane %.3f" % np.median(eten))
        print("\n─── LE CONTRÔLE POSITIF : le champ SÉPARE-T-IL ce qu on sait different ? ───")
        r = b.query('HMT_D = "";'
                    '{ private _p = getPosASL _x; private _l = getPosASL (leader HMT_GO);'
                    '  private _v = _l vectorDiff _p; private _n = vectorMagnitude _v;'
                    '  if (_n > 1) then { _v = _v vectorMultiply (25 / _n) };'
                    '  private _vers = _p vectorAdd _v; private _loin = _p vectorDiff _v;'
                    '  _vers set [2, (getTerrainHeightASL [_vers select 0, _vers select 1]) + 1.5];'
                    '  _loin set [2, (getTerrainHeightASL [_loin select 0, _loin select 1]) + 1.5];'
                    '  private _a = 0; private _c = 0;'
                    '  { _a = _a + ([eyePos _x, _vers] call BIS_fnc_checkVisibility);'
                    '    _c = _c + ([eyePos _x, _loin] call BIS_fnc_checkVisibility) } forEach (units HMT_GO select {alive _x});'
                    '  HMT_D = HMT_D + format ["%1,%2|", round (1000*_a), round (1000*_c)];'
                    '} forEach (units HMT_GB select {alive _x});'
                    + E("HMTD %1 %2", "count (units HMT_GB select {alive _x})", "HMT_D"),
                    r"HMTD (\d+) (\S*)", want=1, timeout=60)
        if r:
            pa = [s.split(",") for s in r[0].group(2).split("|") if s]
            v = np.array([[float(a) / 1000, float(c) / 1000] for a, c in pa])
            d = v[:, 0] - v[:, 1]
            print("  exposition VERS l ennemi %.3f   a l OPPOSE %.3f   ecart %+.3f"
                  % (v[:, 0].mean(), v[:, 1].mean(), d.mean()))
            print("  part des hommes ou VERS > OPPOSE : %.1f %%  (le hasard = 50 %%)" % (100 * (d > 0).mean()))
            print("\n  -> %s" % ("✅ LE CHAMP SEPARE, et dans le BON SENS. `monde2` rendait 50,5 %."
                                 if (d > 0).mean() > 0.65 else
                                 "⛔ il ne separe pas mieux que monde2 — le champ geometrique ne mord pas non plus"))
    finally:
        if b:
            try: b.close()
            except Exception: pass
