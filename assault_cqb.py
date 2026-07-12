#!/usr/bin/env python3
"""assault_cqb — valide le ROLE D'ASSAUT : K soldats, pathfinder Arma REACTIVE (doMove vers defenseurs dans
les batiments). Arma fait-il entrer + nettoyer ? Mesure defenseurs tues + assaillants perdus dans le temps."""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
NDEF = int(sys.argv[2]) if len(sys.argv) > 2 else 10
K = int(sys.argv[3]) if len(sys.argv) > 3 else 8
CX, CY = 20885, 16779
b = SocketBridge(PORT)
time.sleep(1)


def grab(tag):
    for ln in reversed(b._log_lines(5000)):
        m = re.search(r"%s (.+)" % tag, ln)
        if m:
            return m.group(1).strip()
    return None


# nettoie
b.send('if (!isNil "CQB_DEF") then { { deleteVehicle _x } forEach CQB_DEF }; if (!isNil "CQB_ASS") then { { deleteVehicle _x } forEach CQB_ASS }; CQB_DEF=[]; CQB_ASS=[];')
time.sleep(0.5)
# garnit les defenseurs dans les batiments
b.send('private _objs = (nearestObjects [[%d,%d,0], ["House","Building"], 110]) select { count (_x buildingPos -1) > 0 };'
       ' private _g = createGroup east; CQB_DEF=[];'
       ' for "_i" from 0 to %d do { private _bld=_objs select (_i %% count _objs); private _poss=_bld buildingPos -1;'
       '   private _u=_g createUnit ["O_Soldier_F",(_poss select (_i %% count _poss)),[],0,"NONE"];'
       '   _u setPosATL (_poss select (_i %% count _poss)); _u setUnitPos "UP"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setSkill 0.5; CQB_DEF pushBack _u; };'
       ' diag_log format ["GARR %%1", count CQB_DEF];' % (CX, CY, NDEF - 1))
time.sleep(1.5)
# element d'assaut : K soldats a la ligne d'approche, pathfinder Arma ACTIF (doMove)
b.send('private _ga = createGroup west; CQB_ASS=[];'
       ' for "_i" from 0 to %d do { private _u=_ga createUnit ["B_Soldier_F",[%d + (_i*3), %d, 0],[],0,"FORM"];'
       '   _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u enableAI "ALL"; _u setSkill 0.55; CQB_ASS pushBack _u; };'
       ' diag_log format ["ASS %%1", count CQB_ASS];' % (K - 1, CX - 12, CY - 100))
time.sleep(1.5)
print(">>> garnison:", grab("GARR"), "| assaut:", grab("ASS"), flush=True)
t0 = time.time()
for c in range(70):                                    # ~140s
    # repartition : assaillant i -> defenseur vivant (i mod n_vivants) -> couvre des batiments DISTINCTS (pas de cluster)
    b.send('private _live = CQB_DEF select {alive _x};'
           ' { private _u=_x; private _i=_forEachIndex; if (count _live > 0) then { private _tgt=_live select (_i % (count _live)); _u doMove (getPosATL _tgt); _u doTarget _tgt; }; } forEach (CQB_ASS select {alive _x});')
    if c % 5 == 0:
        b.send('diag_log format ["STAT t=%%1 defalive=%%2 assalive=%%3", %d, ({alive _x} count CQB_DEF), ({alive _x} count CQB_ASS)];' % int(time.time() - t0))
        time.sleep(0.4)
        s = grab("STAT")
        if s:
            print("  ", s, flush=True)
        da = grab("STAT")
        if da and "defalive=0" in da:
            print("  >>> COMPLEXE NETTOYE", flush=True); break
    time.sleep(1.6)
b.send('diag_log format ["FIN defalive=%1 assalive=%2", ({alive _x} count CQB_DEF), ({alive _x} count CQB_ASS)];')
time.sleep(0.6)
fin = grab("FIN")
m = re.search(r"defalive=(\d+) assalive=(\d+)", fin or "")
if m:
    da = int(m.group(1)); aa = int(m.group(2))
    print(">>> BILAN : garnison nettoyee %d/%d (%.0f%%) | assaillants survivants %d/%d" % (NDEF - da, NDEF, 100 * (NDEF - da) / NDEF, aa, K), flush=True)
print("ASSAULT_CQB DONE", flush=True)
