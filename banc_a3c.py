#!/usr/bin/env python3
"""banc_a3c — `A3C_ai_shared_fnc_actionClearBuilding` fait-il ENTRER des hommes
dans un batiment, sur un serveur dedie sans joueur ?

Harnais repris de banc_live.py, qui marche. Rien d invente ici.

CE QUI FERAIT ECHOUER CE BANC, ecrit avant le premier pas :
  · ordre_ok=false -> la fonction leve une erreur SQF. Verdict : inexploitable en l etat.
  · clearing=0     -> la fonction est passee sans marquer un seul homme (elle a filtre
                      tout le monde). Verdict : elle tourne mais ne mord pas.
  · dedans=0 SUR LES DEUX BRAS -> le banc ne sait pas mesurer une entree. Banc invalide,
                      pas un verdict sur A3C.
  · A <= B         -> A3C n apporte rien de plus qu un doMove par position interieure.
                      C est un resultat NEGATIF et il compte.

CONTROLE POSITIF (bras B) : chaque assaillant recoit un `doMove` vers une position
interieure distincte. C est ce qu un concepteur de mission ecrit a la main. Si le temoin
fait entrer autant d hommes, A3C ne vaut pas la dependance.

MONDE : Stratis, un batiment choisi par le jeu pour son nombre de positions interieures,
6 defenseurs dedans (PATH coupe = garnison qui ne sort pas), 8 assaillants a 60 m.
"""
import sys, os, time, re, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5840, 6072
LOG = SB + "/logs/serverA3C.out"
CX, CY = 1734.0, 5391.0        # meme zone certifiee que banc_live
NDEF, NATT, DIST = 6, 8, 60.0
T_RUN, PERIODE = 120.0, 6.0
BLOCS, PAR_BLOC = 3, 4         # 12 manches, 6 par bras


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


SCENE = ('''
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
HMT_C = [4000, 4000, 0];
{ if (toLower (text _x) == "agia marina") exitWith { HMT_C = locationPosition _x } } forEach (nearestLocations [[4000,4000,0], ["NameVillage","NameCity","NameCityCapital"], 12000]);
private _cands = nearestObjects [HMT_C, ["Land_i_Shop_01_V1_F"], 400];
HMT_BLD = if (count _cands > 0) then { _cands select 0 } else { objNull };
HMT_BPOS = HMT_BLD buildingPos -1;
HMT_GD = createGroup east;
HMT_DEF = [];
for "_i" from 0 to (NDEF_ - 1) do {
    private _p = HMT_BPOS select (floor (_i * (count HMT_BPOS) / NDEF_));
    private _u = HMT_GD createUnit ["O_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p;
    _u disableAI "PATH";
    _u setSkill 0.6;
    HMT_DEF pushBack _u;
};
HMT_GD setBehaviour "COMBAT"; HMT_GD setCombatMode "RED";
HMT_GA = createGroup west;
HMT_ATT = [];
for "_i" from 0 to (NATT_ - 1) do {
    private _p = HMT_BLD getPos [DIST_, 40 + _i * 7];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0];
    _u setSkill 0.6;
    HMT_ATT pushBack _u;
};
HMT_GA setBehaviour "AWARE"; HMT_GA setCombatMode "RED";
diag_log format ["A3C_SCENE bat=%1 bpos=%2 def=%3 att=%4", typeOf HMT_BLD, count HMT_BPOS, count HMT_DEF, count HMT_ATT];
''')

ORDRE_A = '''
HMT_OK = 0;
[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;
HMT_OK = 1;
diag_log format ["A3C_ORDRE bras=A ok=%1", HMT_OK];
'''

ORDRE_B = '''
HMT_OK = 0;
{
    private _u = _x;
    private _i = HMT_ATT find _u;
    _u doMove (HMT_BPOS select (_i % (count HMT_BPOS)));
} forEach HMT_ATT;
HMT_OK = 1;
diag_log format ["A3C_ORDRE bras=B ok=%1", HMT_OK];
'''

ETAT = '''
private _in = 0; private _cl = 0;
{
    private _u = _x;
    if (alive _u) then {
        private _c = 0;
        { if (_u distance _x < 2.2) then { _c = _c + 1 } } forEach HMT_BPOS;
        if (_c > 0) then { _in = _in + 1 };
        if (_u getVariable ["A3C_CLEARING", false]) then { _cl = _cl + 1 };
    };
} forEach HMT_ATT;
private _av = { alive _x } count HMT_ATT;
private _dv = { alive _x } count HMT_DEF;
diag_log format ["A3C_ETAT dedans=%1 clearing=%2 att=%3 def=%4", _in, _cl, _av, _dv];
'''


def sans_commentaires(s):
    """Le pont aplatit les \\n en \\x01 : un // avalerait tout le reste de la ligne."""
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


def scene_sqf():
    s = SCENE.replace("CX_", str(CX)).replace("CY_", str(CY))
    s = s.replace("NDEF_", str(NDEF)).replace("NATT_", str(NATT)).replace("DIST_", str(DIST))
    return sans_commentaires(s)


def lance_serveur():
    sh("pkill -9 -f serverA3C.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverA3C.cfg' -profiles='%s/profilesA3C' "
       "-port=%d -world=Stratis -autoInit -mod='@CBA_A3;@A3C' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(50)
    return SocketBridge(EXT)


def dernier(b, motif, n=400):
    hits = [L for L in b._log_lines(n) if motif in L]
    return hits[-1] if hits else None


def attendre(b, motif, secondes=15):
    t0 = time.time()
    while time.time() - t0 < secondes:
        L = dernier(b, motif)
        if L:
            return L
        time.sleep(0.3)
    return None


def manche(b, bras, idx):
    b.send(scene_sqf())
    sc = attendre(b, "A3C_SCENE", 20)
    if not sc:
        print("  manche %d [%s] : SCENE ABSENTE — abandon" % (idx, bras), flush=True)
        return None
    m = re.search(r"bat=(\S+) bpos=(\d+) def=(\d+) att=(\d+)", sc)
    time.sleep(2)
    b.send(sans_commentaires(ORDRE_A if bras == "A" else ORDRE_B))
    od = attendre(b, "A3C_ORDRE", 20)
    ok = bool(od and "ok=1" in od)
    pic_in = pic_cl = 0
    t0 = time.time()
    while time.time() - t0 < T_RUN:
        time.sleep(PERIODE)
        b.send(ETAT)
        L = attendre(b, "A3C_ETAT", 8)
        if not L:
            continue
        g = re.search(r"dedans=(\d+) clearing=(\d+) att=(\d+) def=(\d+)", L)
        if g:
            pic_in = max(pic_in, int(g.group(1)))
            pic_cl = max(pic_cl, int(g.group(2)))
    fin = re.search(r"dedans=(\d+) clearing=(\d+) att=(\d+) def=(\d+)", dernier(b, "A3C_ETAT") or "")
    att_v = int(fin.group(3)) if fin else -1
    def_v = int(fin.group(4)) if fin else -1
    r = dict(bras=bras, ordre_ok=ok, dedans=pic_in, clearing=pic_cl,
             att_vivants=att_v, def_vivants=def_v, bat=(m.group(1) if m else "?"),
             bpos=(int(m.group(2)) if m else 0))
    print("  manche %2d [%s] ordre_ok=%s dedans=%d clearing=%d att=%d/%d def=%d/%d (%s, %d pos)"
          % (idx, bras, ok, pic_in, pic_cl, att_v, NATT, def_v, NDEF, r["bat"], r["bpos"]), flush=True)
    return r


if __name__ == "__main__":
    res = []
    n = 0
    for bloc in range(BLOCS):
        print("\n=== bloc %d/%d : relance du serveur (le pont meurt apres 20-40 min) ==="
              % (bloc + 1, BLOCS), flush=True)
        b = lance_serveur()
        p0 = None
        b.send('private _sh = count (allVariables missionNamespace select {_x find "a3c_ai_shared_fnc_" == 0}); diag_log format ["A3C_PORTE0 shared=%1", _sh];')
        p0 = attendre(b, "A3C_PORTE0", 20)
        print("  %s" % (p0 or "PORTE0 MUETTE — le script de mission n a pas repondu"), flush=True)
        if not p0:
            b.sock.close(); continue
        for k in range(PAR_BLOC):
            n += 1
            bras = "A" if (n % 2 == 1) else "B"
            r = manche(b, bras, n)
            if r:
                res.append(r)
        b.sock.close()
        sh("pkill -9 -f serverA3C.cfg; sleep 3")

    print("\n\n================ RESULTAT ================", flush=True)
    for bras in ("A", "B"):
        v = [r for r in res if r["bras"] == bras]
        if not v:
            print("bras %s : aucune manche" % bras); continue
        nm = len(v)
        print("bras %s (%s) — %d manches" % (bras, "A3C actionClearBuilding" if bras == "A" else "temoin doMove", nm))
        print("   ordre sans erreur : %d/%d" % (sum(1 for r in v if r["ordre_ok"]), nm))
        print("   hommes entres (pic, moy) : %.2f / %d" % (sum(r["dedans"] for r in v) / nm, NATT))
        print("   marques A3C_CLEARING     : %.2f" % (sum(r["clearing"] for r in v) / nm))
        print("   assaillants vivants a la fin : %.2f / %d" % (sum(r["att_vivants"] for r in v) / nm, NATT))
        print("   defenseurs vivants a la fin  : %.2f / %d" % (sum(r["def_vivants"] for r in v) / nm, NDEF))
    import json
    json.dump(res, open("/home/younes/arma3-marl/logs_train/banc_a3c.json", "w"), indent=1)
    print("\ndetail : logs_train/banc_a3c.json", flush=True)
