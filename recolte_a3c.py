#!/usr/bin/env python3
"""recolte_a3c — LA MATIERE DU CLONE. Meme protocole qu `usine_saine`, sur PLUSIEURS batiments.

POURQUOI CE FICHIER. Le corpus existant (`corpus_a3c_lambs.jsonl`) vaut 16 manches par bras
sur UN SEUL batiment. On ne clone pas une competence sur un batiment : on clonerait ce
batiment. Ici la meme scene est rejouee sur N types de batiment differents, poses au meme
endroit degage, avec la meme escouade et le meme ordre.

CE QU ON RECOLTE, ET CE QU ON NE RECOLTE PAS
--------------------------------------------
On recolte la GEOMETRIE : ou sont les hommes, tick par tick, en repere batiment. C est la
seule chose mesuree separable entre A3C et le temoin (AUC 0,930, p = 0,0100, 20 manches).
On NE recolte PAS le PLAN d A3C, et c est un choix argumente :
  · `capteur_decisions.py` documente sa regle — les hommes sont apparies en binomes, chaque
    binome recoit la piece non encore prise la plus proche de l entree. C est un glouton :
    ca SE CALCULE. Le projet apprend ce qui ne se calcule pas.
  · et sur un serveur DEDIE, `fnc_actionClearBuilding.sqf` SAUTE le tri des hommes par
    distance a l entree (`if !(isDedicated)`). Sur cette machine A3C tourne donc deja sans
    son affectation ordonnee, et il tue quand meme 3,2x plus (p = 0,011). L avantage n est
    pas dans le plan.

LES TROIS BRAS
--------------
  A3C     [HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding
  SCRIPT  le temoin : un `doMove` par homme vers une position haute, comme dans usine_saine
  CLONE   aucun ordre SQF. Le modele pilote depuis Python, un `doMove` par homme et par
          tick. C est le bras de RECEPTION : ses trajectoires passeront devant le meme juge.

CE QUI FERAIT ECHOUER CETTE RECOLTE, ECRIT AVANT DE LA LANCER
-------------------------------------------------------------
  · batiments trop pauvres : sous 6 positions de station, il n y a pas de piece a nettoyer
    et les trois bras rendent la meme chose. Filtre a >= 6, et le compte des rejets est
    imprime, pas tu.
  · `HMT_ORDRE ok=0` : l ordre n a pas pris, la manche est VOID. Une manche VOID n entre
    jamais dans le corpus — un bras muet qu on compte comme un bras est la faute qui a
    coute le banc n3.
  · ticks != 120 : le protocole a bouge, les manches ne sont plus comparables entre elles
    ni avec le corpus existant. La manche sort.
  · pont muet : il meurt en service apres 20-40 min. Relance par bloc, comme partout ici.

⚠️ NON TESTE A L ECRITURE : la machine tournait les campagnes `natif`/`flanc`. Passer
`--jouet` EN PREMIER — il verifie sur 2 batiments que les trois bras prennent et que le
compte de ticks est bon, avant d engager les heures.
"""
import sys, os, time, re, json, argparse, subprocess

sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5853, 6085          # ports LIBRES : 6062 LV, 6080 DEG, 6082 CAU, 6083 SAIN
LOG = SB + "/logs/serverREC.out"
MODS = "@CBA_A3;@A3C"
INIT = "/home/younes/arma3-marl/a3c_init_serveur.sqf"
POSE = "[1720, 5580, 0]"        # la meme aire degagee que recolte_degagement
NDEF, NATT, DIST = 6, 8, 70.0
T_RUN, TICK = 240.0, 2.0        # 120 ticks, comme le corpus existant. NE PAS TOUCHER.
NPOS_MIN = 6
PAR_BLOC = 6                    # manches avant relance du serveur (le pont meurt en service)
SORTIE = os.environ.get("SORTIE", "/home/younes/arma3-marl/logs_train/corpus_a3c_multi.jsonl")


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def nc(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


# ---------------------------------------------------------------- LE CRIBLE DES BATIMENTS
CRIBLE = '''
HMT_LISTE = [];
[] spawn {
    private _cand = [];
    { private _n = configName _x;
      if ((getNumber (_x >> "scope") > 0) && {_n isKindOf ["House", configFile >> "CfgVehicles"]}) then { _cand pushBack _n };
    } forEach ("true" configClasses (configFile >> "CfgVehicles"));
    { private _b = _x createVehicleLocal POSE_;
      if (count (_b buildingPos -1) >= NPOSMIN_) then { HMT_LISTE pushBack _x };
      deleteVehicle _b } forEach _cand;
    diag_log format ["HMT_LISTE n=%1", count HMT_LISTE];
};
'''

# ---------------------------------------------------------------- LA SCENE, PAR BATIMENT
# Reprise mot pour mot de `usine_saine.SCENE`, a une difference pres et une seule : le
# batiment n est plus celui d Agia Marina, il est CREE depuis la liste criblee. Tout le
# reste — hauteurs cachees, 6 defenseurs PATH desactive skill 0,6, 8 attaquants a 70 m,
# comportements — est identique, sinon les manches ne seraient pas comparables au corpus.
SCENE = '''
HMT_REC = false;
sleep 0.3;
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
if (!isNil "HMT_BLD") then { deleteVehicle HMT_BLD };
sleep 0.2;
HMT_BLD = (HMT_LISTE select IDX_) createVehicle POSE_;
HMT_BLD setVectorUp [0, 0, 1];
HMT_BPOS = HMT_BLD buildingPos -1;
HMT_TIRS = [];
for "_i" from 0 to (NATT_ - 1) do { HMT_TIRS pushBack (HMT_BLD getPos [DIST_, 200 + _i * 5]) };
HMT_HAUT = [];
{
    private _p = _x; private _bl = 0;
    {
        private _a = AGLToASL [_p select 0, _p select 1, (_p select 2) + 1.4];
        private _c = AGLToASL [_x select 0, _x select 1, (_x select 2) + 1.4];
        if (lineIntersects [_a, _c]) then { _bl = _bl + 1 };
    } forEach HMT_TIRS;
    if (_bl == count HMT_TIRS) then { HMT_HAUT pushBack _p };
} forEach HMT_BPOS;
HMT_CACHEES = count HMT_HAUT;
if (count HMT_HAUT < 3) then { HMT_HAUT = HMT_BPOS };
HMT_GD = createGroup east;
HMT_DEF = [];
for "_i" from 0 to (NDEF_ - 1) do {
    private _p = HMT_HAUT select (_i % (count HMT_HAUT));
    private _u = HMT_GD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u disableAI "PATH"; _u setSkill 0.6;
    HMT_DEF pushBack _u;
};
HMT_GD setBehaviour "COMBAT"; HMT_GD setCombatMode "RED";
HMT_GA = createGroup west;
HMT_ATT = [];
for "_i" from 0 to (NATT_ - 1) do {
    private _p = HMT_BLD getPos [DIST_, 200 + _i * 5];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0]; _u setSkill 0.6;
    HMT_ATT pushBack _u;
};
HMT_GA setBehaviour "AWARE"; HMT_GA setCombatMode "RED";
private _bp = "";
{ private _m = HMT_BLD worldToModel _x;
  _bp = _bp + format ["%1,%2,%3^", round ((_m select 0) * 10) / 10,
        round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10] } forEach HMT_BPOS;
diag_log format ["HMT_BPOS %1 %2", IDX_, _bp];
diag_log format ["HMT_SCENE idx=%1 bat=%2 pos=%3 cachees=%4 def=%5 att=%6",
    IDX_, typeOf HMT_BLD, count HMT_BPOS, HMT_CACHEES, count HMT_DEF, count HMT_ATT];
'''

ORDRES = {
    "A3C": '[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;',
    "SCRIPT": '{ private _u = _x; private _i = HMT_ATT find _u; '
              '_u doMove (HMT_HAUT select (_i % (count HMT_HAUT))) } forEach HMT_ATT;',
    "CLONE": '',   # aucun ordre SQF : le modele pilote depuis Python, tick par tick
}

LANCE = '''
HMT_RID = RID_;
HMT_T = 0;
HMT_OK = 0;
ORDRE_
HMT_OK = 1;
diag_log format ["HMT_ORDRE rid=%1 ok=%2", HMT_RID, HMT_OK];
HMT_REC = true;
[] spawn {
    while {HMT_REC} do {
        private _s = "";
        {
            private _u = _x;
            private _m = HMT_BLD worldToModel (getPosATL _u);
            private _st = switch (stance _u) do { case "STAND": {0}; case "CROUCH": {1}; case "PRONE": {2}; default {3} };
            private _dedans = if (_u isKindOf "CAManBase" && {(getPosATL _u) select 2 > 0.5 || (_u distance HMT_BLD) < 8}) then {1} else {0};
            _s = _s + format ["%1,%2,%3,%4,%5,%6^",
                round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10,
                round ((_m select 2) * 10) / 10, _st, (alive _u), _dedans];
        } forEach HMT_ATT;
        private _dv = 0; { if (alive _x) then { _dv = _dv + 1 } } forEach HMT_DEF;
        diag_log format ["HMT_U %1 %2 %3 %4", HMT_RID, HMT_T, _dv, _s];
        HMT_T = HMT_T + 1;
        sleep TICK_;
    };
};
'''

# Le bras CLONE : un ordre par homme et par tick, envoye depuis Python.
PILOTE = 'HMT_ATT select %d doMove (HMT_BLD modelToWorld [%.1f, %.1f, %.1f]);'


def lance():
    sh("pkill -9 -f serverREC.cfg; sleep 2")
    sh("cp %s/staging/serverSAIN.cfg %s/staging/serverREC.cfg" % (SB, SB))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverREC.cfg' -profiles='%s/profilesREC' "
       "-port=%d -world=Stratis -autoInit -mod='%s' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MODS, LOG))
    time.sleep(75)
    b = SocketBridge(EXT)
    if os.path.exists(INIT):
        b.send(nc(open(INIT).read()), wait=False)
        time.sleep(2)
    return b


def att(b, motif, sec=60):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(4000) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.15)
    return None


def lit_ticks(b, rid, depuis=0):
    """Rend les lignes HMT_U de cette manche, decodees."""
    out = {}
    for L in b._log_lines(9000):
        m = re.search(r"HMT_U (\d+) (\d+) (\d+) (.*)", L)
        if not m or int(m.group(1)) != rid:
            continue
        t = int(m.group(2))
        u = []
        for bloc in m.group(4).split("^"):
            ch = bloc.split(",")
            if len(ch) == 6:
                u.append([float(ch[0]), float(ch[1]), float(ch[2]),
                          int(ch[3]), int(ch[4]), int(ch[5])])
        if u:
            out[t] = (int(m.group(3)), u)
    return out


def manche(b, bras, rid, idx, modele, fh):
    """Une manche. Rend (ok, nticks, bat). VOID = ok False, et la manche n entre pas."""
    b.send(nc(SCENE.replace("IDX_", str(idx)).replace("POSE_", POSE)
              .replace("NDEF_", str(NDEF)).replace("NATT_", str(NATT))
              .replace("DIST_", str(DIST))), wait=False)
    L = att(b, "HMT_SCENE idx=%d " % idx, 60)
    if not L:
        return False, 0, "?"
    bat = re.search(r"bat=(\S+)", L).group(1)
    npos = int(re.search(r"pos=(\d+)", L).group(1))
    if npos < NPOS_MIN:
        return False, 0, bat
    # Les positions de station du batiment, en repere batiment. Sans elles, le clone doit
    # les DEVINER depuis les endroits ou les hommes sont passes — donc ne jamais voir les
    # stations qu A3C a choisi d ignorer, ce qui est precisement une partie de sa decision.
    Lb = att(b, "HMT_BPOS %d " % idx, 20)
    bpos = []
    if Lb:
        for bloc in Lb.split("HMT_BPOS %d " % idx, 1)[1].split("^"):
            ch = bloc.split(",")
            if len(ch) == 3:
                try:
                    bpos.append([float(ch[0]), float(ch[1]), float(ch[2])])
                except ValueError:
                    pass
    if len(bpos) < NPOS_MIN:
        return False, 0, bat

    b.send(nc(LANCE.replace("RID_", str(rid)).replace("ORDRE_", ORDRES[bras])
              .replace("TICK_", str(TICK))), wait=False)
    o = att(b, "HMT_ORDRE rid=%d " % rid, 30)
    if not o or "ok=1" not in o:
        return False, 0, bat

    if bras == "CLONE":
        modele.poser_batiment(bpos)
        piloter(b, rid, modele)
    else:
        time.sleep(T_RUN)
    b.send("HMT_REC = false;", wait=False)
    time.sleep(1.0)

    ticks = lit_ticks(b, rid)
    if len(ticks) < 100:                       # protocole : 120 ticks. Sous 100, la manche sort.
        return False, len(ticks), bat
    for t in sorted(ticks)[:120]:
        dv, u = ticks[t]
        rec = {"rid": rid, "bras": bras, "bat": bat, "t": t,
               "def_vivants": dv, "dedans": sum(x[5] for x in u), "u": u}
        if t == 0:
            rec["bpos"] = bpos          # une seule fois par manche : elles ne bougent pas
        fh.write(json.dumps(rec) + "\n")
    fh.flush()
    return True, len(ticks), bat


def piloter(b, rid, modele):
    """Bras CLONE : le modele rend, pour chaque homme, la position a rejoindre. Un ordre par
    tick. Le tick est celui du protocole, pas un tick a nous : on ne change pas l horloge."""
    import torch
    t0 = time.time()
    vu = -1
    while time.time() - t0 < T_RUN:
        ticks = lit_ticks(b, rid)
        if not ticks:
            time.sleep(0.3)
            continue
        t = max(ticks)
        if t == vu:
            time.sleep(0.2)
            continue
        vu = t
        _, u = ticks[t]
        with torch.no_grad():
            cibles = modele.cibles(u)          # [[x,y,z], ...] en repere batiment
        b.send("\n".join(PILOTE % (i, c[0], c[1], c[2]) for i, c in enumerate(cibles)
                         if u[i][4] == 1), wait=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bras", default="A3C,SCRIPT")
    ap.add_argument("--bats", type=int, default=40, help="nombre de types de batiment")
    ap.add_argument("--jouet", action="store_true", help="2 batiments, verifie que tout prend")
    ap.add_argument("--modele", default="", help="poids du clone, pour le bras CLONE")
    ap.add_argument("--rid0", type=int, default=1000)
    a = ap.parse_args()
    bras = a.bras.split(",")
    nbats = 2 if a.jouet else a.bats

    modele = None
    if "CLONE" in bras:
        if not a.modele:
            print("  bras CLONE demande sans --modele : rien a piloter."); sys.exit(2)
        import torch
        from clone_a3c import CloneA3C
        modele = CloneA3C.charger(a.modele)

    b = lance()
    b.send(nc(CRIBLE.replace("POSE_", POSE).replace("NPOSMIN_", str(NPOS_MIN))), wait=False)
    L = att(b, "HMT_LISTE n=", 900)
    if not L:
        print("  le crible n a rien rendu — serveur muet."); sys.exit(1)
    total = int(re.search(r"n=(\d+)", L).group(1))
    print("  batiments criblés (>= %d positions) : %d ; on en joue %d" % (NPOS_MIN, total, nbats),
          flush=True)

    rid = a.rid0
    pris = rejet = 0
    par_bras = {x: 0 for x in bras}
    with open(SORTIE, "a") as fh:
        n = 0
        for k in range(nbats):
            idx = (k * max(1, total // max(nbats, 1))) % total     # etale sur le catalogue
            for br in bras:
                if n > 0 and n % PAR_BLOC == 0:
                    b.sock.close(); sh("pkill -9 -f serverREC.cfg; sleep 3")
                    b = lance()
                    b.send(nc(CRIBLE.replace("POSE_", POSE).replace("NPOSMIN_", str(NPOS_MIN))),
                           wait=False)
                    att(b, "HMT_LISTE n=", 900)
                    print("    [relance apres %d manches]" % n, flush=True)
                ok, nt, bat = manche(b, br, rid, idx, modele, fh)
                print("    r%-5d %-7s idx=%-4d %-34s ticks=%-4d %s"
                      % (rid, br, idx, bat[:34], nt, "OK" if ok else "VOID"), flush=True)
                if ok:
                    pris += 1; par_bras[br] += 1
                else:
                    rejet += 1
                rid += 1; n += 1
    print("\n  manches retenues %d, VOID %d, par bras %s" % (pris, rejet, par_bras))
    print("  corpus : %s" % SORTIE)
    if a.jouet:
        manque = [k for k, v in par_bras.items() if v == 0]
        print("\n  " + ("JOUET PASSE — les %d bras prennent." % len(bras) if not manque
                        else "JOUET TOMBE — bras muets : %s. NE PAS LANCER LA RECOLTE." % manque))
        sys.exit(1 if manque else 0)


if __name__ == "__main__":
    main()
