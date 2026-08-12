#!/usr/bin/env python3
"""demander.py — envoie du SQF a la campagne Antistasi par le pont, imprime la reponse.

Usage : python3 demander.py <fichier.sqf> [port] [attente_s]
Un seul client sur le pont a la fois : le close() est garanti par le finally.
"""
import sys, time, os
sys.path.insert(0, os.path.expanduser("~/arma3-marl"))
from arma_socket_bridge import SocketBridge

def sans_commentaires(txt):
    """compile ne passe pas par le preprocesseur : les // ne sont pas retires."""
    out = []
    for ligne in txt.splitlines():
        if ligne.strip().startswith("//"):
            continue
        out.append(ligne)
    return "\n".join(out)

sqf = sans_commentaires(open(sys.argv[1]).read())
port = int(sys.argv[2]) if len(sys.argv) > 2 else 5876
attente = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0

b = SocketBridge(port)
try:
    avant = len(b.lines)
    b.send(sqf, wait=True, timeout=20)
    t0 = time.time()
    while time.time() - t0 < attente:
        time.sleep(0.5)
    for ln in list(b.lines)[avant:]:
        print(ln[:400])
finally:
    b.sock.close()
