#!/usr/bin/env python3
"""reprendre_banc3.py — reprend le banc n°3 la ou le serveur a plante.

Le serveur a asserte le 04/08 a 21h01 pendant la config 18. On ne rejoue pas les 17
configurations deja completes : on fabrique un jeu de donnees reduit aux configurations
qui manquent, et un banc qui GARDE LEUR NUMERO D'ORIGINE. Sans ca, la reprise ecrirait
« config 1 » pour la 18e et les deux moities du banc seraient impossibles a apparier.

Une configuration n'est reprise que si elle est INCOMPLETE. La 18 avait 2 bras sur 6 :
elle est rejouee en entier, et ses 2 bras orphelins seront ignores a l'analyse — un bras
joue sur une ligne defensive detruite depuis n'est pas comparable aux cinq autres.
"""
import json, re, sys, collections

DEPOT = '/home/younes/arma3-marl/bancs/arma/'
JOURNAUX = sys.argv[1:] or ['/mnt/data/harmattan-sandbox/logs/serverBA.out']
N_BRAS = 6

# ---- ce qui est deja fait -------------------------------------------------
vus = collections.defaultdict(set)
for j in JOURNAUX:
    for l in open(j, errors='ignore'):
        m = re.search(r'HMT\|ESC3\|essai\|(\d+)\|(\w+)\|', l)
        if m:
            vus[int(m.group(1))].add(m.group(2))

# ---- les donnees d'origine ------------------------------------------------
src = open(DEPOT + 'donnees_escouade3.sqf').read()
src = re.sub(r'//[^\n]*', '', src)
corps = src[src.index('=') + 1:].strip().rstrip(';')
data = json.loads(corps)
print(f"  donnees d'origine : {len(data)} configurations")

complets = sorted(c for c in vus if len(vus[c]) >= N_BRAS)
partiels = sorted(c for c in vus if 0 < len(vus[c]) < N_BRAS)
manquants = [i for i in range(1, len(data) + 1) if i not in complets]
print(f"  completes  : {len(complets)} {complets}")
print(f"  partielles : {partiels} (rejouees en entier)")
print(f"  a reprendre: {manquants}")
if not manquants:
    sys.exit("  rien a reprendre — le banc est complet.")

# ---- le jeu de donnees reduit, AVEC les numeros d'origine ------------------
sub = [data[i - 1] for i in manquants]
open(DEPOT + 'donnees_escouade3_reprise.sqf', 'w').write(
    "// genere par reprendre_banc3.py — NE PAS EDITER A LA MAIN\n"
    f"// reprise apres plantage serveur du 04/08 21h01 · configurations {manquants}\n"
    f"HMT_NUMS = {json.dumps(manquants)};\n"
    "HMT_DATA = " + json.dumps(sub, separators=(',', ':')) + ";\n")

# ---- le banc de reprise : le MEME code, deux lignes changees ---------------
b = open(DEPOT + 'banc_escouade3.sqf').read()
avant = b
b = b.replace('"donnees_escouade3.sqf"', '"donnees_escouade3_reprise.sqf"')
if b == avant:
    sys.exit("ECHEC : le nom du fichier de donnees n'a pas ete trouve dans le banc.")
# LE NUMERO DE CONFIGURATION VIENT DE HMT_NUMS, PAS D'UN COMPTEUR QUI REPART A 1.
avant = b
b = b.replace("        _n = _n + 1;\n", "        _n = HMT_NUMS select _forEachIndex;\n")
if b == avant:
    sys.exit("ECHEC : le compteur de configuration n'a pas ete trouve.")
b = b.replace("// banc_escouade3.sqf —",
              "// banc_escouade3_reprise.sqf — REPRISE apres plantage serveur (04/08 21h01).\n"
              "// Le code est IDENTIQUE au banc n°3 : seuls le fichier de donnees et la source\n"
              "// du numero de configuration changent. Le tag du journal reste ESC3 pour que\n"
              "// les deux moities se relisent ensemble.\n"
              "// banc_escouade3.sqf —", 1)
open(DEPOT + 'banc_escouade3_reprise.sqf', 'w').write(b)

print(f"\n  ecrit : {DEPOT}donnees_escouade3_reprise.sqf")
print(f"  ecrit : {DEPOT}banc_escouade3_reprise.sqf")
print(f"  {len(sub)} configurations x {N_BRAS} bras · duree ~{len(sub)*N_BRAS*47/60:.0f} min")
