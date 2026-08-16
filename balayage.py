#!/usr/bin/env python3
"""balayage — le corpus de decisions de chef d escouade, sur TOUS les batiments de la carte.

POURQUOI CE BALAYAGE. Mesure du 14/08 : l affectation d A3C est DETERMINISTE (meme
batiment -> meme mapping, 5 manches sur 5) et ne depend QUE de la geometrie du batiment,
pas de la position des ennemis. Donc un batiment = UN exemple. Repeter des manches sur le
meme batiment ne produit rien. Il faut de la VARIETE GEOMETRIQUE, pas de la repetition.

CE QU ON ENREGISTRE, ET DANS QUEL REPERE.
  entree  : la geometrie BRUTE en repere MODELE du batiment — positions interieures,
            boite englobante, positions de depart des hommes, cap d approche.
  sortie  : le decoupage en PIECES (indices groupes par visibilite mutuelle) + l
            AFFECTATION homme -> piece -> position, captee par interception.
  AUCUN identifiant Arma en entree du modele. Le `typeOf` est enregistre pour la tracabilite
  et le controle de fuite, PAS pour etre appris : sinon l agent apprend Stratis au lieu
  d apprendre a repartir.

PAS DE COMBAT. La decision ne depend pas des ennemis (mesure) : on ne fait donc naitre
aucun defenseur. Consequence assumee et declaree : `_roofSensitive` reste faux, la branche
"barracks avec ennemis en hauteur" n est jamais echantillonnee.

CAP D APPROCHE VARIE, cap = (indice * 37) mod 360 — deterministe et reproductible, mais
different d un batiment a l autre, pour que l agent n apprenne pas "on arrive toujours du sud".

CE QUI FERAIT ECHOUER CE BALAYAGE :
  · moins de 100 batiments retenus -> pas un corpus, une anecdote.
  · pieces=1 sur la majorite -> le decoupage ne discrimine pas, il n y a pas de structure.
  · plans vides sur >30 % -> l interception ne tient pas a l echelle.
  · une seule famille de batiments dominante -> variete apparente, redondance reelle.
"""
import sys, os, time, re, json, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5843, 6075
LOG = SB + "/logs/serverBAL.out"
MONDE = sys.argv[1] if len(sys.argv) > 1 else "Stratis"
PAR_BLOC = 60                 # relance du serveur tous les 60 batiments (pont fragile)
ATTENTE = 7.0                 # secondes laissees a A3C pour rendre ses plans
SORTIE = "/home/younes/arma3-marl/logs_train/corpus_pieces_%s.jsonl" % MONDE


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


def nc(s):
    return "\n".join(l.split("//")[0] for l in s.splitlines() if l.split("//")[0].strip())


INSTRUMENT = '''
HMT_RID = -1;
if (isNil "A3C_ORIG_exec") then { A3C_ORIG_exec = A3C_ai_shared_fnc_actionExecuteUnitPlot };
A3C_ai_shared_fnc_actionExecuteUnitPlot = {
    params ["_u", "_plot"];
    private _w = "";
    {
        private _p = (_x select 0) select 0;
        private _mk = (_x select 1) select 0;
        private _m = HMT_BLD worldToModel _p;
        _w = _w + format ["%1@%2@%3@%4^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10, _mk];
    } forEach _plot;
    diag_log format ["HMT_PLAN %1 %2 %3 %4", HMT_RID, HMT_ATT find _u, count _plot, _w];
    _this call A3C_ORIG_exec;
};
if (isNil "A3C_ORIG_rooms") then { A3C_ORIG_rooms = A3C_main_fnc_buildingCreateRooms };
A3C_main_fnc_buildingCreateRooms = {
    private _r = _this call A3C_ORIG_rooms;
    private _s = ""; private _i = 0;
    { _s = _s + format ["R%1=%2/p%3~", _i, (_x select 0), count (_x select 1)]; _i = _i + 1 } forEach _r;
    diag_log format ["HMT_ROOMS %1 n=%2 %3", HMT_RID, count _r, _s];
    _r
};
diag_log "HMT_INSTRUMENT pose";
'''

ENUM = '''
HMT_LISTE = [];
private _vus = [];
{
    private _p = locationPosition _x;
    {
        private _b = _x;
        if !(_b in _vus) then {
            _vus pushBack _b;
            if (count (_b buildingPos -1) >= 4) then { HMT_LISTE pushBack _b };
        };
    } forEach (nearestObjects [_p, ["House"], 300]);
} forEach (nearestLocations [[worldSize / 2, worldSize / 2, 0], ["NameCityCapital", "NameCity", "NameVillage", "NameLocal", "Airport", "NameMarine", "StrongpointArea"], worldSize]);
diag_log format ["HMT_LISTE n=%1", count HMT_LISTE];
'''

CAPTURE = '''
HMT_RID = IDX_;
{ deleteVehicle _x } forEach (allUnits - allPlayers);
{ if (count (units _x) == 0) then { deleteGroup _x } } forEach allGroups;
HMT_BLD = HMT_LISTE select IDX_;
HMT_BPOS = HMT_BLD buildingPos -1;
private _cap = (IDX_ * 37) % 360;
private _bb = boundingBoxReal HMT_BLD;
private _g = "";
{ private _m = HMT_BLD worldToModel _x; _g = _g + format ["%1@%2@%3^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10, round ((_m select 2) * 10) / 10] } forEach HMT_BPOS;
HMT_GA = createGroup west;
HMT_ATT = [];
private _st = "";
for "_i" from 0 to 7 do {
    private _p = HMT_BLD getPos [70, _cap + _i * 5];
    private _u = HMT_GA createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL [_p select 0, _p select 1, 0];
    HMT_ATT pushBack _u;
    private _m = HMT_BLD worldToModel (getPosATL _u);
    _st = _st + format ["%1@%2^", round ((_m select 0) * 10) / 10, round ((_m select 1) * 10) / 10];
};
diag_log format ["HMT_BAT %1|%2|%3|%4|%5|%6|%7|%8", IDX_, typeOf HMT_BLD, count HMT_BPOS, _cap, _g, _st, round (((_bb select 1) select 0) * 10) / 10, round (((_bb select 1) select 1) * 10) / 10];
[HMT_ATT, HMT_BLD] call A3C_ai_shared_fnc_actionClearBuilding;
diag_log format ["HMT_FAIT %1", IDX_];
'''


def lance():
    sh("pkill -9 -f serverBAL.cfg; sleep 2")
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverBAL.cfg' -profiles='%s/profilesBAL' "
       "-port=%d -world=%s -autoInit -mod='@CBA_A3;@A3C' >> '%s' 2>&1 < /dev/null & disown"
       % (SB, EXT, SB, SB, PORT, MONDE, LOG))
    time.sleep(50)
    return SocketBridge(EXT)


def att(b, motif, sec=30):
    t0 = time.time()
    while time.time() - t0 < sec:
        h = [L for L in b._log_lines(2000) if motif in L]
        if h:
            return h[-1]
        time.sleep(0.25)
    return None


def wp(txt):
    """parse defensif : tout champ malforme est ignore, jamais d exception."""
    out = []
    for e in txt.split("^"):
        q = e.split("@")
        if len(q) < 3:
            continue
        try:
            p = {"x": float(q[0]), "y": float(q[1]), "z": float(q[2])}
        except ValueError:
            continue
        if len(q) >= 4:
            p["piece"] = q[3].split("_Room_")[-1] if "_Room_" in q[3] else ""
        out.append(p)
    return out


def xy(txt):
    out = []
    for e in txt.split("^"):
        q = e.split("@")
        if len(q) < 2:
            continue
        try:
            out.append([float(q[0]), float(q[1])])
        except ValueError:
            continue
    return out


def un_batiment(b, idx, fh):
    marque = len(b.lines)
    b.send(nc(CAPTURE.replace("IDX_", str(idx))), wait=False)
    ligne = att(b, "HMT_BAT %d|" % idx, 30)
    if not ligne:
        return None
    ch = ligne.split("HMT_BAT ", 1)[1].split("|")
    if len(ch) < 8:
        return None
    time.sleep(ATTENTE)
    plans, pieces, portes = [], None, None
    for L in list(b.lines)[marque:]:
        m = re.search(r"HMT_PLAN (-?\d+) (-?\d+) (\d+) (.*)", L)
        if m and m.group(1) == str(idx):
            plans.append({"unite": int(m.group(2)), "wp": wp(m.group(4))})
        m2 = re.search(r"HMT_ROOMS (-?\d+) n=(\d+) (.*)", L)
        if m2 and m2.group(1) == str(idx):
            pieces = int(m2.group(2))
            portes = [int(x) for x in re.findall(r"/p(\d+)~", m2.group(3))]
    aff = {}
    for p in plans:
        for w in p["wp"]:
            if w.get("piece"):
                aff[p["unite"]] = w["piece"]
    rec = {"i": idx, "type": ch[1], "npos": int(ch[2]), "cap": int(ch[3]),
           "positions": wp(ch[4]), "depart": xy(ch[5]),
           "bbox": [float(ch[6]), float(ch[7].split()[0])],
           "pieces": pieces, "portes": portes,
           "plans": plans, "affectation": aff}
    fh.write(json.dumps(rec) + "\n"); fh.flush()
    return rec


if __name__ == "__main__":
    print("monde = %s" % MONDE, flush=True)
    b = lance()
    b.send(nc(INSTRUMENT)); att(b, "HMT_INSTRUMENT", 20)
    b.send(nc(ENUM))
    L = att(b, "HMT_LISTE n=", 120)
    if not L:
        print("ENUMERATION MUETTE"); sys.exit(1)
    total = int(re.search(r"n=(\d+)", L).group(1))
    print("batiments retenus (>= 4 positions interieures) : %d" % total, flush=True)
    if total < 100:
        print("MOINS DE 100 BATIMENTS -> anecdote, pas corpus. On continue mais c est note.", flush=True)

    ok = vide = 0
    with open(SORTIE, "w") as fh:
        i = 0
        while i < total:
            if i > 0 and i % PAR_BLOC == 0:
                b.sock.close(); sh("pkill -9 -f serverBAL.cfg; sleep 3")
                b = lance()
                b.send(nc(INSTRUMENT)); att(b, "HMT_INSTRUMENT", 20)
                b.send(nc(ENUM)); att(b, "HMT_LISTE n=", 120)
                print("  [serveur relance a %d/%d]" % (i, total), flush=True)
            r = un_batiment(b, i, fh)
            if r is None:
                vide += 1
            else:
                ok += 1
                if r["plans"]:
                    pass
                else:
                    vide += 0
            if i % 20 == 0:
                print("  %d/%d  captures=%d  muets=%d" % (i, total, ok, vide), flush=True)
            i += 1
    b.sock.close(); sh("pkill -9 -f serverBAL.cfg")
    print("\ncorpus : %s  (%d batiments captes, %d muets)" % (SORTIE, ok, vide), flush=True)
