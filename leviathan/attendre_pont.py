#!/usr/bin/env python3
"""Attendre que le pont ACCEPTE une connexion, au lieu de dormir un temps devine.
Un sleep fixe a fait echouer le banc a 160 s : le serveur chargeait encore Altis."""
import socket, sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import theatre
T = theatre.use(sys.argv[1] if len(sys.argv) > 1 else 'altis')
t0 = time.time()
while time.time() - t0 < 420:
    try:
        s = socket.create_connection(('127.0.0.1', T.PORT), timeout=3); s.close()
        print('pont pret apres %d s' % (time.time() - t0)); sys.exit(0)
    except Exception:
        time.sleep(5)
print('pont JAMAIS pret apres 420 s'); sys.exit(1)
