#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-TENIR-ARRET
#
# CORRECTIF PREPARE LE 09/09/2026, NON APPLIQUE : un run CHACAL etait en vol.
#
# ⛔ CE QU IL REPARE. CHACAL_TENIR et CHACAL_ARRET decident du bras joue, et
# n apparaissent NI dans « CHACAL|OK|socle » NI dans « CHACAL|FINI ». Consequences :
#   1. on ne peut pas prouver, a partir du RPT seul, quel bras a joue ;
#   2. un parametre qui ne MORDRAIT PAS - ecrit dans server.cfg, ignore par la
#      mission - passerait inapercu, et deux bras « differents » seraient en fait
#      le meme. C est exactement le piege du 08/09 avec CHACAL_BRAS.
# Le lanceur ecrit deja ces cles dans server.cfg ; ce qui manque est la preuve
# qu elles sont ARRIVEES jusqu a la mission et qu elles y ont ete LUES.
#
# ⚠️ A JOUER SEULEMENT MACHINE LIBRE. Il touche mission.Altis et lancer.sh :
#   - le lanceur redeploie mission.Altis vers MPMissions, et `mv` ECHOUE si un
#     serveur Arma tient le dossier ouvert (mesure du 08/09, 21h50) ;
#   - editer lancer.sh pendant qu il tourne decale les offsets lus par bash.
# Verifier d abord : ls /mnt/data/hmt/queue/en_cours/ et les arma3server vivants.
#
# USAGE :  python3 2026-09-09_journaliser_tenir_arret.py [racine_du_depot]
#          racine par defaut : /mnt/data/hmt/depot
# Idempotent : il se reconnait a son propre marqueur « |tenir|% » et ne repasse pas.
# APRES : bash -n bancs/chacal/lancer.sh, puis un episode de controle, puis commit.

import sys, os

RACINE = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
M = os.path.join(RACINE, "bancs/chacal/mission.Altis/chacal")

# (fichier, ancien, nouveau, marqueur d idempotence)
PATCHS = [
    # --- 1. la ligne socle porte les deux leviers
    (os.path.join(M, "00_socle.sqf"),
     b'|palier|%9|immortel|%10",',
     b'|palier|%9|immortel|%10|tenir|%11|arret|%12",',
     b'|immortel|%10|tenir|%11'),
    (os.path.join(M, "00_socle.sqf"),
     b'CHACAL_PALIER, CHACAL_IMMORTEL]) call CHACAL_LOG;',
     b'CHACAL_PALIER, CHACAL_IMMORTEL, CHACAL_TENIR, CHACAL_ARRET]) call CHACAL_LOG;',
     b'CHACAL_IMMORTEL, CHACAL_TENIR, CHACAL_ARRET])'),
    # --- 2. la ligne de verdict aussi. %24 = palier est deja pris, on continue a 25.
    (os.path.join(M, "70_verdict.sqf"),
     b'|ticks|%22|duree|%23",',
     b'|ticks|%22|duree|%23|tenir|%25|arret|%26",',
     b'|duree|%23|tenir|%25'),
    (os.path.join(M, "70_verdict.sqf"),
     b'CHACAL_TICK, round time, CHACAL_PALIER]) call CHACAL_LOG;',
     b'CHACAL_TICK, round time, CHACAL_PALIER, CHACAL_TENIR, CHACAL_ARRET]) call CHACAL_LOG;',
     b'CHACAL_PALIER, CHACAL_TENIR, CHACAL_ARRET])'),
    # --- 3. le controle d identite refuse l episode si le job et l en-tete divergent
    (os.path.join(RACINE, "bancs/chacal/lancer.sh"),
     b'python3 - "$OUT/resultat.json" "$G" "$PAL" "$BRAS_NOM" "$DEPART" <<\'PY\'\n'
     b'import json,sys\n'
     b'p,g,pal,bras,dep = sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]\n',
     b'python3 - "$OUT/resultat.json" "$G" "$PAL" "$BRAS_NOM" "$DEPART" "$TENIR" "$ARRET" <<\'PY\'\n'
     b'import json,sys\n'
     b'p,g,pal,bras,dep,tenir,arret = sys.argv[1:8]\n'
     b'def egal(a,b):\n'
     b'    # SQF rend les entiers sans decimale, mais on compare en nombre quand les\n'
     b'    # deux cotes sont numeriques : un "6" face a "6.0" n est pas un ecart de\n'
     b'    # mission, et un faux REFUS coute un episode de trois heures.\n'
     b'    try: return float(a)==float(b)\n'
     b'    except (TypeError,ValueError): return str(a)==str(b)\n',
     b'p,g,pal,bras,dep,tenir,arret = sys.argv[1:8]'),
    (os.path.join(RACINE, "bancs/chacal/lancer.sh"),
     b'for cle,attendu in (("graine",g),("palier",pal),("bras",bras),("depart",None)):\n'
     b'    if attendu is None: continue\n'
     b'    obtenu=str(e.get(cle,"?"))\n'
     b'    if obtenu!=str(attendu): ecarts.append(f"{cle} demande {attendu}, joue {obtenu}")\n',
     b'for cle,attendu in (("graine",g),("palier",pal),("bras",bras),("depart",None),("tenir",tenir),("arret",arret)):\n'
     b'    if attendu is None: continue\n'
     b'    obtenu=str(e.get(cle,"?"))\n'
     b'    if not egal(obtenu,attendu): ecarts.append(f"{cle} demande {attendu}, joue {obtenu}")\n',
     b'("tenir",tenir),("arret",arret)'),
    (os.path.join(RACINE, "bancs/chacal/lancer.sh"),
     b'print("  identite conforme au job : graine",g,"palier",pal,"bras",bras)',
     b'print("  identite conforme au job : graine",g,"palier",pal,"bras",bras,"tenir",tenir,"arret",arret)',
     b'"bras",bras,"tenir",tenir,"arret",arret)'),
]

faits, deja, rates = 0, 0, []
for chemin, avant, apres, marqueur in PATCHS:
    if not os.path.exists(chemin):
        rates.append("ABSENT " + chemin); continue
    with open(chemin, "rb") as f:
        t = f.read()
    if marqueur in t:
        deja += 1; print("DEJA   ", os.path.basename(chemin), marqueur[:40].decode(errors="replace")); continue
    n = t.count(avant)
    if n != 1:
        rates.append("MOTIF x%d dans %s : %s" % (n, chemin, avant[:60].decode(errors="replace")))
        continue
    with open(chemin, "wb") as f:
        f.write(t.replace(avant, apres))
    faits += 1; print("APPLIQUE", os.path.basename(chemin), marqueur[:40].decode(errors="replace"))

print("\n%d applique(s), %d deja en place, %d rate(s)" % (faits, deja, len(rates)))
for r in rates:
    print("  RATE:", r)
sys.exit(1 if rates else 0)
