#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-CHIEN-ET-SEUIL
# Deux defauts de la meme famille que ceux d hier, trouves par Fable le 13/09.
#
# 1. LE CHIEN DE GARDE MORD EN PHASE 6. Sa boucle teste CHACAL_PHASE == 5 AVANT son sleep 10. Apres le
#    sommeil la phase peut valoir 6, et le corps s execute quand meme : il ordonne AWARE et un doMove
#    VERS LE SITE a des hommes qui decrochent. Mesure : 8 episodes sur 15 de la campagne en cours,
#    entre 1 et 7 secondes apres le debut de la phase 6. C est exactement le bug corrige le 12/09 pour
#    CHACAL_FIN, au meme endroit et dans la meme boucle - la garde avait ete posee pour une variable
#    et pas pour l autre.
#
# 2. LA PHASE 6 ATTEND UN HOMME QUI N EXISTE PAS. Sa condition de sortie exige que 6 hommes soient
#    arrives, sur un EFFECTIF de 10 et non sur les survivants. S il ne reste que 5 vivants, la
#    condition ne peut JAMAIS etre vraie : la phase brule son plafond entier, une vingtaine de minutes,
#    avant de conclure PLAFOND. C est la famille « critere hors d atteinte », celle de arret=5 et du
#    seuil 3 de la phase 3. Et l etiquette ment : EXFIL_MANQUEE pour un detachement qui a perdu ses
#    hommes, pas qui a rate son decrochage.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"), t.count('"') % 2)

# --- 1. le chien -------------------------------------------------------------
p = f"{M}/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "phase_quittee" in s:
    print("  00_socle : chien deja corrige")
else:
    a = """    while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
        sleep 10;
        if (count CHACAL_CIBLE_ASSAUT > 0 && { !isNull CHACAL_gAssaut }) then {"""
    if a not in s: print("  !! ancre chien absente"); sys.exit(1)
    n = """    while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
        sleep 10;
        // ! LA PHASE A PU CHANGER PENDANT LE SOMMEIL ( 13/09 ). Sans ce test, le chien ordonnait AWARE
        // et un doMove VERS LE SITE a des hommes qui decrochaient : 8 episodes sur 15, entre 1 et 7 s
        // apres le debut de la phase 6. C est le bug corrige le 12/09 pour CHACAL_FIN, dans cette meme
        // boucle - la garde avait ete posee pour une variable et pas pour l autre.
        if (CHACAL_FIN || { CHACAL_PHASE != 5 }) exitWith {
            (format ["CHACAL|E|chien_de_garde|%1|phase_quittee|%2|relances|%3", round (time * 100) / 100,
                CHACAL_PHASE, CHACAL_RELANCES_SOCLE]) call CHACAL_LOG;
        };
        if (count CHACAL_CIBLE_ASSAUT > 0 && { !isNull CHACAL_gAssaut }) then {"""
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 00_socle", bil(s), bil(s2)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : le chien lache prise quand la phase change")

# --- 2. le seuil de la phase 6 ------------------------------------------------
p = f"{M}/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "PERTES_EXCESSIVES" in s:
    print("  60_phases : seuil deja corrige")
else:
    a = """private _tE = time;
waitUntil { sleep 3;
    (count (CHACAL_FS select { alive _x && { (_x distance2D CHACAL_EXFIL_POINT) < 90 } }) >= (round (0.6 * CHACAL_EFFECTIF))) ||
    (count (CHACAL_FS select { alive _x }) == 0) || (time - _tE > _plafond) || CHACAL_FIN };"""
    if a not in s: print("  !! ancre attente absente"); sys.exit(1)
    n = """private _tE = time;
private _seuilExf = round (0.6 * CHACAL_EFFECTIF);
// ! LE CRITERE PORTE SUR L EFFECTIF, PAS SUR LES SURVIVANTS ( 13/09 ). S il reste moins d hommes
// vivants que le seuil, la condition de sortie ne peut JAMAIS etre vraie : la phase brulait son
// plafond entier, une vingtaine de minutes, pour conclure PLAFOND. C est un critere hors d atteinte,
// la meme famille que arret=5 et le seuil 3 de la phase 3. On sort tout de suite, et on le DIT.
waitUntil { sleep 3;
    (count (CHACAL_FS select { alive _x && { (_x distance2D CHACAL_EXFIL_POINT) < 90 } }) >= _seuilExf) ||
    (count (CHACAL_FS select { alive _x }) < _seuilExf) || (time - _tE > _plafond) || CHACAL_FIN };
private _vivExf = count (CHACAL_FS select { alive _x });
if (_vivExf < _seuilExf) then {
    (format ["CHACAL|E|exfil_impossible|%1|vivants|%2|seuil|%3|temps_ecoule|%4", round (time * 100) / 100,
        _vivExf, _seuilExf, round (time - _tE)]) call CHACAL_LOG;
};"""
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 60_phases", bil(s), bil(s2)); sys.exit(1)
    # l issue de phase doit distinguer les deux cas
    b = """[6, "EXFILTRATION", (if (CHACAL_EXFILTRES >= (round (0.6 * CHACAL_EFFECTIF))) then {"ATTEINT"} else {
    if (count (CHACAL_FS select { alive _x }) == 0) then {"DETRUIT"} else {"PLAFOND"} })] call CHACAL_fnc_finPhase;"""
    if b not in s2: print("  !! ancre finPhase absente"); sys.exit(1)
    c = """[6, "EXFILTRATION", (if (CHACAL_EXFILTRES >= _seuilExf) then {"ATTEINT"} else {
    if (count (CHACAL_FS select { alive _x }) == 0) then {"DETRUIT"} else {
    if (count (CHACAL_FS select { alive _x }) < _seuilExf) then {"PERTES_EXCESSIVES"} else {"PLAFOND"} } })] call CHACAL_fnc_finPhase;"""
    s3 = s2.replace(b, c, 1)
    if bil(s) != bil(s3): print("  !! equilibre finPhase", bil(s), bil(s3)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : 60_phases : sortie immediate si trop peu de vivants, issue PERTES_EXCESSIVES")

# --- 3. la cause du verdict ---------------------------------------------------
p = f"{M}/70_verdict.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "PERTES_EXCESSIVES" in s:
    print("  70_verdict : deja present")
else:
    a = """                CHACAL_CAUSE = if (_vivants == 0) then {"DETACHEMENT_DETRUIT"}
                    else { if (_actes < _objTotal) then {"CHARGES_INCOMPLETES"} else {"EXFIL_MANQUEE"} };"""
    if a not in s: print("  !! ancre cause absente"); sys.exit(1)
    n = """                // ! L ETIQUETTE MENTAIT ( 13/09 ). EXFIL_MANQUEE couvrait deux choses differentes :
                // un detachement qui n a pas rejoint le point de ramassage, et un detachement qui n a
                // plus assez d hommes pour le franchir. Le second n a pas rate son decrochage, il a
                // perdu ses hommes. On separe, sinon le goulot se lit a l envers.
                CHACAL_CAUSE = if (_vivants == 0) then {"DETACHEMENT_DETRUIT"}
                    else { if (_actes < _objTotal) then {"CHARGES_INCOMPLETES"} else {
                    if (_vivants < (round (0.6 * CHACAL_EFFECTIF))) then {"PERTES_EXCESSIVES"} else {"EXFIL_MANQUEE"} } };"""
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 70_verdict", bil(s), bil(s2)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 70_verdict : PERTES_EXCESSIVES separee de EXFIL_MANQUEE")
