#!/usr/bin/env python3
"""sonde_pont — LE CONTROLE POSITIF DU PONT, celui que j aurais du ecrire en premier.

Avant de demander au pont de porter une scene de 21 hommes et une politique, on lui demande
de porter UNE ligne. S il ne sait pas faire l aller-retour sur `diag_log "PING"`, tout ce qui
suit est du bruit — et j ai passe une heure a chercher la panne dans la couture alors que la
question n avait jamais ete posee au bon niveau.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

EXT = 5830
b = SocketBridge(EXT)
print(f"  connecte au port {EXT}, compteur de depart n = {b.n}", flush=True)
time.sleep(2)
print(f"  lignes deja recues du pont : {len(b.lines)}", flush=True)
for L in list(b.lines)[-5:]:
    print("    <", L[:100], flush=True)

n = b.send('diag_log "HMT_PING_SONDE";', wait=False)
print(f"\n  envoye : commande n={n}", flush=True)
time.sleep(4)
recv = [L for L in b.lines if "HARMATTAN_RECV" in L or "HMT_PING" in L]
print(f"  lignes recues apres envoi : {len(b.lines)}", flush=True)
for L in list(b.lines)[-6:]:
    print("    <", L[:100], flush=True)
print(f"\n  ACCUSE / ECHO : {len(recv)} ligne(s)", flush=True)
print("  " + ("PASSE — le pont fait l aller-retour." if recv else
              "TOMBE — le pont N EST PAS bidirectionnel. Rien de ce qui suit ne vaut."), flush=True)
b.sock.close()
