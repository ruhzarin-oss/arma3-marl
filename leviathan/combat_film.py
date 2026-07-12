#!/usr/bin/env python3
"""combat_film.py — SCENE FILMEE : une escouade commandee assaut une position defendue.

Pas de banc a pourcentages. On REGARDE, on juge a l'oeil :
  - l'escouade bondit et supprime comme de l'infanterie reelle ?
  - elle prend l'objectif VIVANTE ?

Executeur valide cette session : desiger (reveal + doTarget UNE fois) + IA LAMBS active + COMBAT/RED
-> feu AUTONOME (pas de micro-gestion, pas de doSuppressiveFire).
Base de feu (SW) fixe les defenseurs ; element de manoeuvre (SE) bondit sur l'objectif.
Zone NETTOYEE avant (anti-contamination du monde persistant). LOS verifiee. Defenseurs en couvert PARTIEL
(sacs de sable, crouch) pour SURVIVRE assez et qu'on voie le combat se developper.

Phases (sous-commande en argv) :
  setup   nettoie la zone + place la scene GELEE (personne ne tire) + pose les marqueurs + rapporte la LOS
  tp      teleporte les joueurs connectes au POINT DE VUE (invulnerables, spectateurs surs)
  go      ACTION : base de feu ouvre le feu (autonome) + defenseurs liberes + manoeuvre bondit sur l'objectif
  watch   boucle d'etat haut-niveau pour suivre (le vrai juge = l'oeil de Younes)
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

b = NativeBridge(port=5816)

# --- Geometrie de la scene (spot [5569,4683]->[5569,4738], LOS N-S deja VERIFIEE claire cette session) ---
OBJX, OBJY = 5569, 4738                                   # objectif (position defendue)
DEF   = [[5563, 4738], [5567, 4738], [5571, 4738], [5575, 4738]]   # defenseurs EAST (face sud)
BAGS  = []                                                # v1 : pas de sacs (ils coupaient la LOS) — LOS propre d'abord
BOF   = [[5563, 4683], [5566, 4683], [5569, 4683]]        # base de feu WEST (axe verifie) ~55 m
MAN   = [[5576, 4688], [5580, 4688], [5584, 4688], [5588, 4688]]   # manoeuvre (flanc SE) bondit vers l'objectif
VANT  = [5560, 4675]                                      # point de vue de Younes (derriere la base de feu)


def arr(points):
    return "[" + ",".join("[" + str(p[0]) + "," + str(p[1]) + ",0]" for p in points) + "]"


SETUP = ("[] spawn { "
    # purge scene precedente + contamination du monde (unites, sacs, murs dans 400 m)
    'if (!isNil "HMT_DEF") then { {deleteVehicle _x} forEach HMT_DEF }; '
    'if (!isNil "HMT_BOF") then { {deleteVehicle _x} forEach HMT_BOF }; '
    'if (!isNil "HMT_MAN") then { {deleteVehicle _x} forEach HMT_MAN }; '
    'if (!isNil "HMT_BAGS") then { {deleteVehicle _x} forEach HMT_BAGS }; '
    "{ deleteVehicle _x } forEach (nearestObjects [[4001,4040,0],[\"Man\",\"Land_BagFence_Long_F\",\"Wall\"],400]); "
    'for "_i" from 0 to 9 do { deleteMarker ("cf_"+str _i) }; deleteMarker "cf_obj"; deleteMarker "cf_vue"; '
    # sacs de sable (couvert partiel)
    "HMT_BAGS=[]; { private _b = createVehicle [\"Land_BagFence_Long_F\", _x, [], 0, \"CAN_COLLIDE\"]; _b setDir 0; HMT_BAGS pushBack _b; } forEach " + arr(BAGS) + "; "
    # defenseurs EAST : en couvert, crouch, tiennent la position, GELES (hold fire) jusqu'au GO
    "private _gd = createGroup east; HMT_DEF=[]; "
    "{ _gd createUnit [\"O_Soldier_F\", _x, [], 0, \"NONE\"]; private _u=(units _gd) select ((count units _gd)-1); _u setPosATL _x; "
    "_u setSkill 0.55; _u setDir 180; _u setUnitPos \"MIDDLE\"; _u setBehaviour \"COMBAT\"; _u setCombatMode \"BLUE\"; _u disableAI \"AUTOTARGET\"; _u disableAI \"PATH\"; _u allowDamage true; HMT_DEF pushBack _u; } forEach " + arr(DEF) + "; "
    # base de feu WEST : GELEE jusqu'au GO
    "private _gs = createGroup west; HMT_BOF=[]; "
    "{ _gs createUnit [\"B_soldier_F\", _x, [], 0, \"NONE\"]; private _u=(units _gs) select ((count units _gs)-1); _u setPosATL _x; "
    "_u setSkill 0.6; _u setUnitPos \"MIDDLE\"; _u setBehaviour \"COMBAT\"; _u setCombatMode \"BLUE\"; _u disableAI \"AUTOTARGET\"; _u disableAI \"PATH\"; _u allowDamage true; HMT_BOF pushBack _u; } forEach " + arr(BOF) + "; "
    # manoeuvre WEST : GELEE au point de depart jusqu'au GO
    "private _gm = createGroup west; HMT_MAN=[]; "
    "{ _gm createUnit [\"B_soldier_F\", _x, [], 0, \"NONE\"]; private _u=(units _gm) select ((count units _gm)-1); _u setPosATL _x; "
    "_u setSkill 0.6; _u setBehaviour \"AWARE\"; _u setCombatMode \"BLUE\"; _u disableAI \"AUTOTARGET\"; HMT_MAN pushBack _u; } forEach " + arr(MAN) + "; "
    "HMT_GD=_gd; HMT_GS=_gs; HMT_GM=_gm; "
    # marqueurs
    "createMarker [\"cf_obj\", [" + str(OBJX) + "," + str(OBJY) + ",0]]; \"cf_obj\" setMarkerType \"hd_objective\"; \"cf_obj\" setMarkerColor \"ColorRed\"; \"cf_obj\" setMarkerText \"OBJECTIF\"; "
    "createMarker [\"cf_vue\", [" + str(VANT[0]) + "," + str(VANT[1]) + ",0]]; \"cf_vue\" setMarkerType \"mil_dot\"; \"cf_vue\" setMarkerColor \"ColorBlue\"; \"cf_vue\" setMarkerText \"POINT DE VUE\"; "
    # rapport LOS : combien de la base de feu VOIENT un defenseur, + milieu du trajet manoeuvre -> defenseur
    "private _defAim = (aimPos (HMT_DEF select 0)); "
    "private _losBof = 0; { private _u=_x; if (count (lineIntersectsSurfaces [(eyePos _u), _defAim, _u, (HMT_DEF select 0)]) == 0) then { _losBof=_losBof+1 } } forEach HMT_BOF; "
    "private _mid = [5575, 4713, (getTerrainHeightASL [5575,4713])+1.4]; "
    "private _losMan = count (lineIntersectsSurfaces [_mid, _defAim, objNull, (HMT_DEF select 0)]) == 0; "
    "(format [\"HARMATTAN_CF ok def=%1 bof=%2 man=%3 losBof=%4 losMan=%5\", count HMT_DEF, count HMT_BOF, count HMT_MAN, _losBof, _losMan]) call HMT_EMIT; "
    "};")

TP = ('{ _x allowDamage false; _x setCaptive true; _x setPosATL [' + str(VANT[0]) + ',' + str(VANT[1]) + ',0]; } forEach allPlayers; '
      '(format ["HARMATTAN_TP joueurs=%1", count allPlayers]) call HMT_EMIT;')

GO = ("[] spawn { "
    # defenseurs : liberes, ils defendent
    '{ _x enableAI "AUTOTARGET"; _x setCombatMode "RED"; _x setBehaviour "COMBAT"; } forEach HMT_DEF; '
    # tout le monde se revele mutuellement
    "{ private _d=_x; { _d reveal [_x, 4] } forEach (HMT_BOF + HMT_MAN); } forEach HMT_DEF; "
    "{ private _a=_x; { _a reveal [_x, 4] } forEach HMT_DEF; } forEach (HMT_BOF + HMT_MAN); "
    # base de feu : EXECUTEUR VALIDE -> desiger UNE fois + IA active + RED -> feu autonome soutenu
    "{ private _u=_x; _u enableAI \"AUTOTARGET\"; _u setCombatMode \"RED\"; _u setBehaviour \"COMBAT\"; "
    "_u doTarget (HMT_DEF select (_forEachIndex mod (count HMT_DEF))); } forEach HMT_BOF; "
    # manoeuvre : bond sur l'objectif (waypoint MOVE FULL), IA active, RED
    "{ _x enableAI \"AUTOTARGET\"; _x setCombatMode \"RED\"; } forEach HMT_MAN; "
    "{ deleteWaypoint _x } forEach (waypoints HMT_GM); "
    "private _w = HMT_GM addWaypoint [[" + str(OBJX) + "," + str(OBJY) + ",0], 0]; _w setWaypointType \"MOVE\"; _w setWaypointSpeed \"FULL\"; _w setWaypointBehaviour \"AWARE\"; _w setWaypointCombatMode \"RED\"; "
    "{ _x doMove [" + str(OBJX) + "," + str(OBJY) + ",0] } forEach HMT_MAN; "
    "(format [\"HARMATTAN_GO action def=%1 bof=%2 man=%3\", count HMT_DEF, count HMT_BOF, count HMT_MAN]) call HMT_EMIT; "
    "};")

DIAG = ("private _b = HMT_BOF select 0; private _m = HMT_MAN select 0; private _d = HMT_DEF select 0; "
    "private _bmode = combatMode _b; private _bbeh = behaviour _b; private _bknows = _b knowsAbout _d; "
    "private _bat = _b checkAIFeature \"AUTOTARGET\"; private _bammo = _b ammo currentWeapon _b; "
    "private _mspd = speed _m; private _mwp = count (waypoints HMT_GM); private _players = count allPlayers; "
    "private _sim = simulationEnabled _b; "
    "(format [\"HARMATTAN_DG bmode=%1 bbeh=%2 bknows=%3 bAT=%4 bammo=%5 mspd=%6 mwp=%7 players=%8 sim=%9\", "
    "_bmode, _bbeh, round(_bknows*100)/100, _bat, _bammo, round _mspd, _mwp, _players, _sim]) call HMT_EMIT;")

WATCH = ("private _ma=0; private _mind=9999; "
    "{ if (alive _x) then { _ma=_ma+1; private _d=(getPosATL _x) distance2D [" + str(OBJX) + "," + str(OBJY) + "]; if (_d<_mind) then {_mind=_d} } } forEach HMT_MAN; "
    "private _ba=({alive _x} count HMT_BOF); private _da=0; private _dsup=0; "
    "{ if (alive _x) then { _da=_da+1; _dsup=_dsup max (getSuppression _x) } } forEach HMT_DEF; "
    "(format [\"HARMATTAN_W man=%1 mind=%2 bof=%3 def=%4 dsup=%5\", _ma, round _mind, _ba, _da, round(_dsup*100)]) call HMT_EMIT;")


def do_setup():
    r = b.query(SETUP, r"HARMATTAN_CF ok def=(\d+) bof=(\d+) man=(\d+) losBof=(\w+) losMan=(\w+)", want=1, timeout=25)
    if not r:
        print("SETUP : pas de reponse du pont (serveur/bridge up ?)", flush=True); return
    m = r[-1]
    losbof = int(m.group(4))
    print("=== SCENE EN PLACE (gelee) ===", flush=True)
    print("  defenseurs=%s  base_de_feu=%s  manoeuvre=%s" % (m.group(1), m.group(2), m.group(3)), flush=True)
    print("  LOS base_de_feu->defenseurs : %d/%s voient   |   LOS trajet_manoeuvre->defenseurs : %s" % (losbof, m.group(2), m.group(5)), flush=True)
    print("  Objectif marque 'OBJECTIF' | Point de vue marque 'POINT DE VUE' [%d,%d]" % (VANT[0], VANT[1]), flush=True)
    if losbof == 0:
        print("  ! base de feu AVEUGLE (0 LOS) — a ajuster avant le GO", flush=True)


def do_tp():
    r = b.query(TP, r"HARMATTAN_TP joueurs=(\d+)", want=1, timeout=15)
    n = r[-1].group(1) if r else "?"
    print("Teleporte %s joueur(s) au POINT DE VUE (invulnerables, spectateurs surs)." % n, flush=True)


def do_go():
    r = b.query(GO, r"HARMATTAN_GO action def=(\d+) bof=(\d+) man=(\d+)", want=1, timeout=20)
    if r:
        print(">>> ACTION — la base de feu ouvre le feu, la manoeuvre bondit sur l'objectif. REGARDE. <<<", flush=True)
    else:
        print("GO : pas de reponse du pont.", flush=True)


def do_watch(ticks=40):
    print("=== SUIVI (le vrai juge = ton oeil) ===", flush=True)
    for t in range(ticks):
        r = b.query(WATCH, r"HARMATTAN_W man=(\d+) mind=(\d+) bof=(\d+) def=(\d+) dsup=(\d+)", want=1, timeout=15)
        if not r:
            time.sleep(1.5); continue
        m = r[-1]; ma=int(m.group(1)); mind=int(m.group(2)); ba=int(m.group(3)); da=int(m.group(4)); dsup=int(m.group(5))
        print("  t=%2d | manoeuvre=%d/%d ->obj=%3dm | base_feu=%d/%d | defenseurs=%d/%d cloues=%3d%%"
              % (t, ma, len(MAN), mind, ba, len(BOF), da, len(DEF), dsup), flush=True)
        if ma == 0:
            print("  -> manoeuvre aneantie.", flush=True); break
        if mind < 8:
            print("  -> OBJECTIF ATTEINT par la manoeuvre.", flush=True); break
        if da == 0:
            print("  -> position ennemie nettoyee.", flush=True); break
        time.sleep(1.5)


FORCE = ('private _a0 = (HMT_BOF select 0) ammo currentWeapon (HMT_BOF select 0); '
    '{ _x doFire (HMT_DEF select 0); _x forceWeaponFire [currentWeapon _x, currentWeaponMode _x]; } forEach HMT_BOF; '
    '(format ["HARMATTAN_FF a0=%1", _a0]) call HMT_EMIT;')


def do_force():
    r = b.query(FORCE, r"HARMATTAN_FF a0=(\d+)", want=1, timeout=15)
    print("Tir force sur la base de feu (ammo avant=%s). Je verifie l'ammo apres via diag." % (r[-1].group(1) if r else "?"), flush=True)


def do_diag():
    r = b.query(DIAG, r"HARMATTAN_DG bmode=(\w+) bbeh=(\w+) bknows=([\d.]+) bAT=(\w+) bammo=(\d+) mspd=(-?\d+) mwp=(\d+) players=(\d+) sim=(\w+)", want=1, timeout=15)
    if not r:
        print("DIAG : pas de reponse.", flush=True); return
    m = r[-1]
    print("=== DIAG (base de feu / manoeuvre / serveur) ===", flush=True)
    print("  base de feu : combatMode=%s behaviour=%s AUTOTARGET=%s knowsAbout(def)=%s ammo=%s sim=%s"
          % (m.group(1), m.group(2), m.group(4), m.group(3), m.group(5), m.group(9)), flush=True)
    print("  manoeuvre   : vitesse=%s km/h  waypoints=%s" % (m.group(6), m.group(7)), flush=True)
    print("  joueurs connectes=%s" % m.group(8), flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "setup"
    {"setup": do_setup, "tp": do_tp, "go": do_go, "watch": do_watch, "diag": do_diag, "force": do_force}.get(cmd, do_setup)()
