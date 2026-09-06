#!/usr/bin/env python3
"""LE FALSIFICATEUR DE LA LOI DE TIR — peut-on etre touche AU FUSIL en etant cache ?

Criteres : CRITERES_FALSIFICATEUR_VUE.md, ecrits avant tout chiffre.
Seuil pre-inscrit : > 10 % des impacts directs a visibilite < 0,63 tue la loi.

⚠️ Tout le SQF transmis est PURGE de commentaires : la mission l execute par `call compile`,
qui ne les retire pas — un seul `//` fait echouer le bloc en SILENCE.
⚠️ On n emet QUE des nombres : un champ vide desynchronise le compteur, cote serveur.
"""
# ⚠️ `AGLToASL (aimingPosition _x)` FAIT ECHOUER le bloc en silence (echelle ping2 :
# eyePos/eyePos rend 1, la variante aimingPosition ne rend RIEN). On lit oeil a oeil.
import sys, re, json, time
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
EPISODES = int(sys.argv[2]) if len(sys.argv) > 2 else 2
DUREE = int(sys.argv[3]) if len(sys.argv) > 3 else 180
SEUIL = 0.63
SORTIE = "/home/younes/arma3-marl/falsificateur_vue.json"


# ⚠️ `_this` EST DEJA le tableau des impacts (piege deja paye dans `generateur_engagements_v12`).
# Et on ne SUPPOSE PAS sa longueur : le premier jet lisait `select 10` (isDirect) sur un
# tableau qui n en a peut-etre que 9 -> l ecouteur mourait en silence, 0 impact sur 8 morts.
# On emet `count` a la place : la forme se LIT dans la donnee au lieu d etre devinee.
HMT_EH = (
 '{ { private _e = _x; private _vic = _e select 0; private _sh = _e select 1; '
 'if (!isNull _vic && {!isNull _sh} && {_vic != _sh}) then { '
 'private _d = _sh distance _vic; private _o = eyePos _sh; '
 'private _ray = [objNull, "VIEW"] checkVisibility [_o, eyePos _vic]; '
 'private _pied = getPosASL _vic; private _oeil = eyePos _vic; private _n = 0; '
 '{ private _k = _x; '
 'private _pt = [(_pied select 0) + _k * ((_oeil select 0) - (_pied select 0)), '
 '(_pied select 1) + _k * ((_oeil select 1) - (_pied select 1)), '
 '(_pied select 2) + _k * ((_oeil select 2) - (_pied select 2))]; '
 'if (([objNull, "VIEW"] checkVisibility [_o, _pt]) > 0.5) then { _n = _n + 1 }; '
 '} forEach [0.15, 0.4, 0.65, 0.9, 1]; '
 'private _frac = _n / 5; '
 'private _av = 0; if (alive _vic) then { _av = 1 }; '
 'HMT_HITS = HMT_HITS + 1; '
 'format ["HMTHIT %1 %2 %3 %4 %5", _d, _ray, _frac, _av, count _this] call HMT_EMIT; '
 '} } forEach _this; }'
)

b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter))

# ─────────────────────────── CONTROLE POSITIF DE LA SONDE ───────────────────────────
# Deux hommes a 50 m ; on lit checkVisibility a nu, puis avec un mur SOLIDE interpose.
CTRL = (
 '[] spawn { '
 'private _p = [23000,17400,0]; '
 'private _g1 = createGroup west; private _g2 = createGroup east; '
 'private _a = _g1 createUnit ["B_Soldier_F", _p, [], 0, "NONE"]; '
 'private _q = [(_p select 0) + 50, _p select 1, 0]; '
 'private _c = _g2 createUnit ["O_Soldier_F", _q, [], 0, "NONE"]; '
 'sleep 2; '
 'private _v1 = [objNull, "VIEW"] checkVisibility [eyePos _a, eyePos _c]; '
 'private _m = createVehicle ["Land_Cargo_House_V1_F", [((_p select 0) + 25), _p select 1, 0], [], 0, "CAN_COLLIDE"]; '
 'sleep 2; '
 'private _v2 = [objNull, "VIEW"] checkVisibility [eyePos _a, eyePos _c]; '
 'private _n = 0; if (alive _a) then { _n = _n + 1 }; if (alive _c) then { _n = _n + 1 }; '
 'format ["HMTCTRL %1 %2 %3", _v1, _v2, _n] call HMT_EMIT; '
 'deleteVehicle _m; deleteVehicle _a; deleteVehicle _c; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
)
# ⚠️ LE LIEU DU CONTROLE N EST PAS TIRE AU HASARD. Un premier jet le tirait par
# `BIS_fnc_randomPos` : deux hommes a 50 m se sont retrouves masques par le relief et le
# temoin + a rendu 0,000 — le controle a REFUSE de demarrer, ce qui est son role, mais un
# controle positif se pose sur un cas dont la reponse est CONNUE. On prend donc le banc plat
# deja certifie d Altis (23000,17400), celui de la courbe de toucher du 26/07.
r = b.query(CTRL, r"HMTCTRL ([-0-9.eE+]+) ([-0-9.eE+]+) ([0-9]+)", want=1, timeout=60)
if not r:
    sys.exit("  ⛔ le controle positif n a pas repondu — rien n est lu")
v_nu, v_mur, vivants = float(r[0].group(1)), float(r[0].group(2)), int(r[0].group(3))
print("\n  CONTROLE POSITIF DE `checkVisibility` (%d hommes poses)" % vivants)
print("    a nu, 50 m        : %.3f   (attendu >= %.2f)" % (v_nu, SEUIL))
print("    mur interpose     : %.3f   (attendu <  %.2f)" % (v_mur, SEUIL))
if vivants < 2 or not (v_nu >= SEUIL and v_mur < SEUIL):
    sys.exit("  ⛔ LA SONDE NE DISCRIMINE PAS — la mesure ne demarre pas.")
print("    ✔ la sonde separe le degage du masque")


# ─────────────── CONTROLE POSITIF DE L ECOUTEUR `HitPart` (regle 16, clause 1) ───────────────
# La scene precedente a rendu 8 morts et ZERO impact : l ecouteur etait aveugle et le banc
# l a dit. On ne relance donc rien sans avoir pose l ecouteur sur un cas ou les impacts sont
# CONNUS MASSIFS : un tireur a 40 m qui arrose une cible INVULNERABLE (allowDamage false,
# sinon elle tombe et son bras devient muet — piege deja paye le 28/07).
EH_CTRL = (
 '[] spawn { HMT_HITS = 0; '
 'private _p = [16000,16000,0]; '
 'for "_i" from 0 to 60 do { _p = [] call BIS_fnc_randomPos; '
 'if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
 'private _g1 = createGroup west; private _g2 = createGroup east; '
 'private _t = _g1 createUnit ["B_Soldier_F", _p, [], 0, "NONE"]; '
 'private _s = _g2 createUnit ["O_Soldier_F", [(_p select 0) + 40, _p select 1, 0], [], 0, "NONE"]; '
 '_t allowDamage false; _t disableAI "MOVE"; _s setSkill 0.5; '
 '_t addEventHandler ["HitPart", ' + HMT_EH + ']; '
 'sleep 2; _s reveal [_t, 4]; _s setBehaviour "COMBAT"; _s setCombatMode "RED"; '
 '_s doTarget _t; '
 'for "_i" from 0 to 20 do { _s doTarget _t; _s doFire _t; sleep 2; '
 'if (HMT_HITS > 2) exitWith {} }; '
 'format ["HMTEH %1", HMT_HITS] call HMT_EMIT; '
 'deleteVehicle _t; deleteVehicle _s; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
)
r = b.query(EH_CTRL, r"HMTEH (\d+)", want=1, timeout=90)
if not r:
    sys.exit("  ⛔ le controle de l ecouteur n a pas repondu")
n_eh = int(r[0].group(1))
formes = set()
for s_ in b._log_lines(5000):
    m = re.match(r"HMTHIT (?:[-0-9.eE+]+ ){4}(\d+)", s_.strip())
    if m:
        formes.add(int(m.group(1)))
print("\n  CONTROLE POSITIF DE L ECOUTEUR `HitPart`")
print("    impacts captes sur cible invulnerable a 40 m : %d" % n_eh)
print("    longueur du tableau HitPart observee : %s" % (sorted(formes) or "aucune"))
if n_eh < 1:
    sys.exit("  ⛔ L ECOUTEUR EST AVEUGLE — aucune mesure n est admissible.")
print("    ✔ l ecouteur voit ce qui est connu massif")

# ─────────────────────────────── LA SCENE ET SA CAPTURE ───────────────────────────────
SCENE = (
 '[] spawn { '
 'HMT_HITS = 0; HMT_FIN = 0; '
 'private _p = [16000,16000,0]; '
 'for "_i" from 0 to 60 do { _p = [] call BIS_fnc_randomPos; '
 'if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
 'private _gb = createGroup west; private _gr = createGroup east; '
 'private _dir = random 360; '
 'for "_i" from 0 to 7 do { private _u = _gb createUnit ["B_Soldier_F", '
 '[(_p select 0) + (_i % 4) * 6 - 9, (_p select 1) + floor (_i / 4) * 6, 0], [], 0, "NONE"]; '
 '_u setSkill 0.5; _u allowFleeing 0; }; '
 'private _q = [(_p select 0) + 220 * sin _dir, (_p select 1) + 220 * cos _dir, 0]; '
 'for "_i" from 0 to 7 do { private _u = _gr createUnit ["O_Soldier_F", '
 '[(_q select 0) + (_i % 4) * 6 - 9, (_q select 1) + floor (_i / 4) * 6, 0], [], 0, "NONE"]; '
 '_u setSkill 0.5; _u allowFleeing 0; }; '
 'sleep 3; '
 '{ private _v = _x; { _v reveal _x } forEach (units _gr) } forEach (units _gb); '
 '{ private _v = _x; { _v reveal _x } forEach (units _gb) } forEach (units _gr); '
 '{ _x addEventHandler ["HitPart", ' + HMT_EH + '] } forEach (units _gb + units _gr); '
 'private _u0 = (units _gb) select 0; '
 'private _mg = currentMagazine _u0; '
 'private _amm = getText (configFile >> "CfgMagazines" >> _mg >> "ammo"); '
 'format ["HMTAMMO %1 %2", '
 '(getNumber (configFile >> "CfgAmmo" >> _amm >> "indirectHitRange")), '
 '(getNumber (configFile >> "CfgAmmo" >> _amm >> "hit"))] call HMT_EMIT; '
 '{ _x setBehaviour "COMBAT"; _x setSpeedMode "FULL"; _x setCombatMode "RED" } forEach [_gb, _gr]; '
 '{ _x doMove (getPosATL (leader _gr)) } forEach (units _gb); '
 '{ _x doMove (getPosATL (leader _gb)) } forEach (units _gr); '
 'private _t0 = time; '
 'waitUntil { sleep 2; (time - _t0 > __DUREE__) or ({alive _x} count (units _gb) == 0) '
 'or ({alive _x} count (units _gr) == 0) }; '
 'format ["HMTEPI %1 %2 %3", HMT_HITS, ({alive _x} count (units _gb)), '
 '({alive _x} count (units _gr))] call HMT_EMIT; '
 '{ deleteVehicle _x } forEach (units _gb + units _gr); '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__DUREE__", str(DUREE))

hits, ammo_ihr, ammo_hit = [], [], []
for ep in range(EPISODES):
    t0 = time.time()
    n_avant = len(b._log_lines(50000))
    r = b.query(SCENE, r"HMTEPI (\d+) (\d+) (\d+)", want=1, timeout=DUREE + 90)
    if not r:
        print("  episode %d : PAS DE FIN — banc suspect, on s arrete" % ep); break
    nh, vb, vr = (int(r[0].group(i)) for i in (1, 2, 3))
    for s_ in b._log_lines(50000)[n_avant:]:
        m = re.match(r"HMTAMMO ([-0-9.eE+]+) ([-0-9.eE+]+)", s_.strip())
        if m:
            ammo_ihr.append(float(m.group(1))); ammo_hit.append(float(m.group(2)))
    for s in b._log_lines(50000)[n_avant:]:
        m = re.match(r"HMTHIT ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+)", s.strip())
        if m:
            hits.append([float(m.group(i)) for i in (1, 2, 3, 4, 5)])
    print("  episode %d : %d impacts · survivants %d bleus / %d rouges · %.0f s"
          % (ep, nh, vb, vr, time.time() - t0))
    if nh == 0 and vb == 8 and vr == 8:
        print("    ⛔ personne n a tire ET personne n est mort — le monde ne combat pas")
        break

# ───────────────────────────────── LE VERDICT ─────────────────────────────────
# L arme de l episode qualifie la serie : si son `indirectHitRange` vaut 0, tous ces impacts
# sont du tir VISE sans rayon d effet — exactement le cas que la loi declare impossible sur
# un homme cache. Et on ne juge que les victimes VIVANTES a l impact : cribler un cadavre
# couche derriere un buisson lirait une visibilite nulle et fabriquerait la falsification.
print("\n  MUNITION DES EPISODES : indirectHitRange %s · hit %s"
      % (sorted(set(ammo_ihr)) or "?", sorted(set(ammo_hit)) or "?"))
if not ammo_ihr or max(ammo_ihr) > 0.0:
    print("  ⛔ l arme a un RAYON D EFFET (ou n a pas ete lue) : ce banc ne teste pas le tir vise")
    fusil = []
else:
    fusil = [h for h in hits if h[3] == 1.0]
caches = [h for h in fusil if h[1] < SEUIL]
print("\n  " + "=" * 66)
print("  impacts releves ............. %d" % len(hits))
print("  dont victime VIVANTE a l impact %d" % len(fusil))
if not fusil:
    print("  ⛔ aucun impact de fusil : le banc ne peut RIEN dire.")
else:
    # ⚠️ DEUX INSTRUMENTS, UN SEUL EST LE BON. Le premier jet lisait un RAYON oeil-a-oeil ;
    # le moteur emploie une FRACTION DE CORPS (`Visibility(brain, ai)`), et c est a cette
    # grandeur-la qu appartient le seuil 0,63. Un rayon rend 0 pendant que la moitie du
    # torse est exposee. On rend les deux : leur ECART dit s il faut croire le verdict.
    parts = {}
    for nom, col in (("rayon oeil-a-oeil", 1), ("fraction de corps", 2)):
        sous = [h for h in fusil if h[col] < SEUIL]
        parts[nom] = len(sous) / len(fusil)
        vs = sorted(h[col] for h in fusil)
        print("  %-18s : %4d / %4d = %5.1f %% sous %.2f · mediane %.3f · p05 %.3f"
              % (nom, len(sous), len(fusil), 100 * parts[nom], SEUIL,
                 vs[len(vs) // 2], vs[max(0, int(0.05 * len(vs)))]))
    part = parts["fraction de corps"]
    caches = [h for h in fusil if h[2] < SEUIL]
    print("  le verdict porte sur la FRACTION DE CORPS (seuil pre-inscrit 10 %)")
    print("  " + "=" * 66)
    if part > 0.10:
        print("  ⛔ LA LOI EST FALSIFIEE : on est touche au fusil en etant cache.")
        print("     RV3 a change l equation -> la loi se RETIRE du gymnase, on ne la regle pas.")
    else:
        print("  ✔ LA LOI TIENT sur Arma 3 : pas de tir vise sur un homme cache.")
json.dump({"seuil": SEUIL, "hits": hits, "episodes": EPISODES, "duree_s": DUREE},
          open(SORTIE, "w"))
print("  ecrit : %s" % SORTIE)
b.sock.close()
