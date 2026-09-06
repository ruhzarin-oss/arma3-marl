#!/usr/bin/env python3
"""pont_test — PYTHON PARLE-T-IL AU SERVEUR ARMA ? Trois questions, dans cet ordre.

⚠️ LA FAUTE DU PREMIER PASSAGE, ET ELLE ETAIT MIENNE : j interrogeais avec `diag_log`, qui
n ecrit QUE dans le fichier journal. Pour qu une ligne REVIENNE par le pont il faut passer par
`HMT_EMIT`, defini a l init comme { diag_log _this; "hmt_native" callExtension ("o|" + _this) }.
Le sens ALLER marchait depuis le debut — la preuve : `HMTNATIF_ARRIVE` est apparu dans le
journal apres un envoi Python. J ecoutais le mauvais canal au RETOUR.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

print("=" * 84); print(" PONT — Python parle-t-il au serveur Arma ?"); print("=" * 84)
try:
    b = NativeBridge(port=5801, timeout=15)
    print("  1. connexion au port 5801 ........... OUVERTE")
except Exception as e:
    print("  1. connexion ........................ ECHEC : %s" % e); sys.exit(1)

try:
    r = b.query('format ["HMTPING %1", 6*7] call HMT_EMIT;', r"HMTPING (\d+)", want=1, timeout=15)
    v = r[0].group(1) if r else None
    print("  2. aller-retour d un calcul ......... %s   (attendu 42)" % (v or "AUCUNE REPONSE"))
except Exception as e:
    print("  2. aller-retour ..................... ECHEC : %s" % e); v = None

try:
    r = b.query('format ["HMTMONDE %1 %2 %3", worldName, count allUnits, diag_fps] call HMT_EMIT;',
                r"HMTMONDE (\S+) (\d+) ([\d.]+)", want=1, timeout=15)
    if r:
        w, n, f = r[0].group(1), r[0].group(2), r[0].group(3)
        print("  3. l etat du monde .................. monde=%s  unites=%s  FPS=%s" % (w, n, f))
    else:
        print("  3. l etat du monde .................. AUCUNE REPONSE")
except Exception as e:
    print("  3. etat du monde .................... ECHEC : %s" % e)

print()
if v == "42":
    print("  ✅ LA LIAISON EST VIVANTE. Arma est mesurable depuis Python.")
    print("     Piste B n est plus « un serveur tourne » : c est « on peut mesurer ».")
else:
    print("  ⛔ la liaison ne rend pas — le pont ecoute mais ne repond pas.")
try: b.close()
except Exception: pass
