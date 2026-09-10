#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-EXFIL-EFFECTIF
#
# CORRECTIF PREPARE LE 10/09/2026. A JOUER MACHINE LIBRE (redeploiement de mission.Altis).
#
# 1. LE SEUIL D EXFILTRATION SUIT L EFFECTIF.
#    La phase 6 attendait « 6 vivants au point d exfiltration », 6 en dur. Le verdict exige
#    0,6 x CHACAL_EFFECTIF. A vingt hommes la phase se fermait au sixieme arrive, le compteur
#    etait fige a 6 et l episode juge EXFIL_MANQUEE sur 17 vivants et 3 charges sur 3.
#    A dix hommes : round (0,6 x 10) = 6, comportement identique.
# 2. LA LIGNE FINI PORTE LES LEVIERS QU ELLE NE PORTAIT PAS : depart, effectif, appui_feu,
#    accessible, feu_avant. Journalises seulement, pas controles : depart 5 est un alias de 4 et un
#    faux REFUS couterait un episode. A passer APRES 2026-09-09_journaliser_tenir_arret.py.
import sys, os

RACINE = sys.argv[1] if len(sys.argv) > 1 else "/mnt/data/hmt/depot"
M = os.path.join(RACINE, "bancs/chacal/mission.Altis/chacal")

PATCHS = [
    (os.path.join(M, "60_phases.sqf"),
     b"< 90 } }) >= 6) ||",
     b"< 90 } }) >= (round (0.6 * CHACAL_EFFECTIF))) ||",
     b"< 90 } }) >= (round (0.6 * CHACAL_EFFECTIF))) ||"),
    (os.path.join(M, "60_phases.sqf"),
     b"(CHACAL_EXFILTRES >= 6)",
     b"(CHACAL_EXFILTRES >= (round (0.6 * CHACAL_EFFECTIF)))",
     b"(CHACAL_EXFILTRES >= (round (0.6 * CHACAL_EFFECTIF)))"),
    (os.path.join(M, "70_verdict.sqf"),
     b'|tenir|%25|arret|%26",',
     b'|tenir|%25|arret|%26|depart|%27|effectif|%28|appui_feu|%29|accessible|%30|feu_avant|%31",',
     b'|depart|%27|effectif|%28'),
    (os.path.join(M, "70_verdict.sqf"),
     b"CHACAL_PALIER, CHACAL_TENIR, CHACAL_ARRET]) call CHACAL_LOG;",
     b"CHACAL_PALIER, CHACAL_TENIR, CHACAL_ARRET, CHACAL_DEPART, CHACAL_EFFECTIF, CHACAL_APPUI_FEU, CHACAL_ACCESSIBLE, CHACAL_FEU_AVANT]) call CHACAL_LOG;",
     b"CHACAL_ARRET, CHACAL_DEPART, CHACAL_EFFECTIF"),
]

faits, deja, rates = 0, 0, []
for chemin, avant, apres, marqueur in PATCHS:
    t = open(chemin, "rb").read()
    if marqueur in t:
        deja += 1; print("DEJA    ", os.path.basename(chemin), marqueur[:50].decode()); continue
    n = t.count(avant)
    if n != 1:
        rates.append("MOTIF x%d dans %s : %s" % (n, os.path.basename(chemin), avant[:60].decode())); continue
    open(chemin, "wb").write(t.replace(avant, apres))
    faits += 1; print("APPLIQUE", os.path.basename(chemin), marqueur[:50].decode())
print("\n%d applique(s), %d deja en place, %d rate(s)" % (faits, deja, len(rates)))
for r in rates: print("  RATE:", r)
sys.exit(1 if rates else 0)
