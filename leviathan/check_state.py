#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
q = ('(format ["HMT_STATE arm=%1 orch=%2 warm=%3 wread=%4 wtot=%5 wlive=%6 wmode=%7 players=%8",'
     '!(isNil "HMT_ARM"), (!(isNil "HMT_ORCH_SNAP") && !(isNil "HMT_TAC_DISPATCH") && !(isNil "HMT_ORCH_FEATS")),'
     '!(isNil "HMT_WARM"), !(isNil "HMT_WREAD"),'
     '(if (isNil "HMT_WPILOT") then {-1} else {count HMT_WPILOT}),'
     '(if (isNil "HMT_WPILOT") then {-1} else {{alive _x} count HMT_WPILOT}),'
     '(if (isNil "HMT_WAGENT_MODE") then {"nil"} else {str HMT_WAGENT_MODE}), count allPlayers]) call HMT_EMIT;')
r = b.query(q, r"HMT_STATE (.+)", want=1, timeout=15)
print(r[-1].group(1) if r else "pas de reponse du pont")
