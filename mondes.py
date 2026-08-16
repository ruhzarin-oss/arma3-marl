#!/usr/bin/env python3
import sys, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB="/mnt/data/harmattan-sandbox"; EXT,PORT=5844,6076
def sh(c): subprocess.run(["bash","-lc",c],check=False)
Q='''
private _s = "";
{
    private _n = configName _x;
    if (isNumber (_x >> "mapSize") && {getNumber (_x >> "mapSize") > 1000}) then {
        _s = _s + format ["%1:%2 ", _n, round (getNumber (_x >> "mapSize"))];
    };
} forEach ("true" configClasses (configFile >> "CfgWorlds"));
diag_log format ["HMT_MONDES %1", _s];
'''
sh("pkill -9 -f serverMON.cfg; sleep 2")
sh("cp /mnt/data/harmattan-sandbox/staging/serverBAL.cfg /mnt/data/harmattan-sandbox/staging/serverMON.cfg")
sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 "
   "-config='%s/staging/serverMON.cfg' -profiles='%s/profilesMON' -port=%d -world=Stratis -autoInit "
   "-mod='@CBA_A3;@A3C;@cup_terrains_core;@cup_terrains_maps' >> '%s/logs/serverMON.out' 2>&1 < /dev/null & disown"%(SB,EXT,SB,SB,PORT,SB))
time.sleep(70)
b=SocketBridge(EXT); time.sleep(3)
b.send("\n".join(l for l in Q.splitlines() if l.strip()))
L=None
for _ in range(60):
    h=[x for x in b._log_lines(600) if "HMT_MONDES" in x]
    if h: L=h[-1]; break
    time.sleep(0.5)
if L:
    ent=[e for e in L.split("HMT_MONDES",1)[1].split() if ":" in e]
    print("mondes jouables : %d"%len(ent))
    for e in sorted(ent, key=lambda x:-int(x.split(":")[1])): print("   %s"%e)
else: print("MUET")
b.sock.close(); sh("pkill -9 -f serverMON.cfg")
