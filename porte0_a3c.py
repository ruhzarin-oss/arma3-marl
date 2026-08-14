#!/usr/bin/env python3
"""porte0_a3c — A3C se charge-t-il sur un serveur DEDIE, sans joueur ?

CE QUI FERAIT ECHOUER CETTE PORTE, ecrit avant de la franchir :
  1. `isClass CfgPatches/A3C_CORE` faux  -> le mod n est pas monte du tout.
  2. shared=0                            -> A3C_Init.sqf n a pas tourne cote serveur,
                                            ou il sort avant la ligne 117.
  3. squad>0                             -> ANOMALIE : la barriere `isDedicated` de la
                                            ligne 121 n aurait pas joue, donc je n ai pas
                                            compris le fichier. Le resultat serait suspect.
  4. mcss=0                              -> actionClearBuilding ne peut pas tourner
                                            (4 dependances MCSS).
ATTENDU si ma lecture du code est juste : cls=true, shared~99, hc~76, rail~8, main~67,
squad=0, mcss~46.
"""
import sys, os, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"
EXT, PORT = 5840, 6072
LOG = SB + "/logs/serverA3C.out"


def sh(c):
    subprocess.run(["bash", "-lc", c], check=False)


PORTE0 = '''
private _all = allVariables missionNamespace;
private _sh = count (_all select {_x find "a3c_ai_shared_fnc_" == 0});
private _hc = count (_all select {_x find "a3c_ai_highcommand_fnc_" == 0});
private _ra = count (_all select {_x find "a3c_ai_rail_fnc_" == 0});
private _mn = count (_all select {_x find "a3c_main_fnc_" == 0});
private _sq = count (_all select {_x find "a3c_ai_squad_fnc_" == 0});
private _mc = count (_all select {_x find "mcss_fnc_" == 0});
private _cls = isClass (configFile >> "CfgPatches" >> "A3C_CORE");
private _cb = if (isNil "A3C_ai_shared_fnc_actionClearBuilding") then {"NIL"} else {"PRESENTE"};
private _pa = if (isNil "A3C_ai_shared_fnc_polygonAreaActionOn") then {"NIL"} else {"PRESENTE"};
diag_log format ["A3C_PORTE0 cls=%1 shared=%2 hc=%3 rail=%4 main=%5 squad=%6 mcss=%7 clearBuilding=%8 suppression=%9", _cls, _sh, _hc, _ra, _mn, _sq, _mc, _cb, _pa];
'''

if __name__ == "__main__":
    sh("pkill -9 -f serverA3C.cfg; sleep 2")
    os.makedirs(SB + "/logs", exist_ok=True)
    sh("rm -f '%s'" % LOG)
    print("lancement serveur dedie + @A3C ...", flush=True)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverA3C.cfg' -profiles='%s/profilesA3C' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@A3C' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(50)

    b = SocketBridge(EXT)
    print("pont TCP ouvert", flush=True)
    time.sleep(3)
    b.send(PORTE0)
    ligne = None
    for _ in range(30):
        hits = [L for L in b._log_lines(600) if "A3C_PORTE0" in L]
        if hits:
            ligne = hits[-1]; break
        time.sleep(0.5)
    print("\n>>> %s" % (ligne if ligne else "AUCUNE REPONSE — le script de mission n a pas repondu"), flush=True)
    b.sock.close()
    sh("pkill -9 -f serverA3C.cfg")
