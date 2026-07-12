#!/usr/bin/env python3
"""stress_bridge.py — reproduit la charge qui tuait le pont : un FLOT d'emissions massif cote Arma
pendant que Python NE LIT PAS (buffer socket se remplit). Ancien .so = send bloquant = crash. Nouveau = survit."""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)

# 1. version de l'extension (confirme que le nouveau .so est charge)
r = b.query('(format ["HMT_VER %1", "hmt_native" callExtension "version"]) call HMT_EMIT;', r"HMT_VER (.+)", want=1, timeout=10)
print("Extension chargee :", r[-1].group(1) if r else "?? (pas de reponse)")

# 2. FLOT : 4000 emissions de ~4 Ko cote Arma, aussi vite que possible
big = "X" * 4000
sqf = '[] spawn { for "_i" from 0 to 3999 do { (format ["HMT_FLOOD %1", _i]) call HMT_EMIT; (format ["HMT_PAD ' + big + '"]) call HMT_EMIT; }; };'
b.send(sqf)
print("Flot lance : 4000 x ~4 Ko = ~16 Mo. J'attends 7s SANS lire (le buffer socket doit deborder)...")
time.sleep(7)

# 3. le serveur/pont a-t-il SURVECU ? requete simple
r2 = b.query('(format ["HMT_ALIVE %1", round diag_frameNo]) call HMT_EMIT;', r"HMT_ALIVE (\d+)", want=1, timeout=15)
if r2:
    print(">>> SERVEUR VIVANT apres le flot (frame=%s) — le fix TIENT." % r2[-1].group(1))
else:
    print(">>> PAS DE REPONSE — pont/serveur tombe.")
