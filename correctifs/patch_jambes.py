#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-JAMBES
# TROISIEME PANNE D INSTRUMENT LUE COMME UN RESULTAT.
# La regle S3 du socle cloue l appui : disableAI "PATH" plus lambs_danger_disableAI. La phase 6 ne le
# libere QUE si CHACAL_APPUI_FIXE == 1. Avec socle=1 et appui_fixe=0 - le reglage de toutes les
# campagnes - l appui n est JAMAIS libere. Deux hommes sur dix ne peuvent pas marcher jusqu au point
# de ramassage, alors que le critere en exige six sur dix.
# Mesure dans les traces : les hommes 6 et 7 parcourent ZERO metre pendant la phase 6, dans 11
# episodes sur 12, pendant que les autres marchent 1000 a 2400 m. Et dans les echecs, TOUS les
# survivants mobiles etaient arrives : ce n etaient pas des exfiltrations manquees.
# Relecture hors ligne des 38 episodes : 18 succes reels, 28 projetes si l appui marchait, soit
# +26,3 points. Et les echecs qui restent sont 8 charges incompletes contre 2 exfiltrations : le
# goulot est l ASSAUT, pas le decrochage.
#
# Deux corrections, et la seconde compte autant que la premiere.
#  1. La phase 6 rend les jambes a TOUT LE MONDE, sans condition. On s exfiltre, on ne tient pas.
#  2. UNE GARDE : on compte les hommes vivants qui ne peuvent pas marcher, et on l ecrit. Aucune porte
#     du lecteur ne verifiait qu un homme vivant a des jambes - c est pourquoi ce defaut a traverse
#     quinze portes vertes.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"), t.count('"') % 2)

p = f"{M}/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "exfil_jambes" in s:
    print("  60_phases : deja present")
else:
    a = 'if (CHACAL_APPUI_FIXE == 1 && { !isNull CHACAL_gAppui }) then { { _x enableAI "PATH" } forEach (units CHACAL_gAppui) };'
    if a not in s: print("  !! ancre absente"); sys.exit(1)
    n = '''// ! ON REND LES JAMBES A TOUT LE MONDE, SANS CONDITION ( 13/09 ).
// L ancienne ligne ne liberait l appui QUE si CHACAL_APPUI_FIXE valait 1. Or le socle le cloue par sa
// regle S3, et toutes les campagnes tournaient avec socle=1 et appui_fixe=0 : l appui n etait JAMAIS
// libere. Mesure dans les traces : les hommes 6 et 7 parcourent ZERO metre pendant la phase 6 dans 11
// episodes sur 12, pendant que les autres marchent 1000 a 2400 m. Deux hommes sur dix ne pouvaient pas
// rejoindre le point de ramassage, alors que le critere en exige six sur dix.
// On s exfiltre, on ne tient pas : a la phase 6, plus personne n est cloue.
{
    if (!isNull _x) then {
        _x setVariable ["lambs_danger_disableGroupAI", false, true];
        { if (alive _x) then {
            _x enableAI "PATH"; _x enableAI "MOVE";
            _x setVariable ["lambs_danger_disableAI", false, true];
            _x forceSpeed -1;
        } } forEach (units _x);
    };
} forEach [CHACAL_gAssaut, CHACAL_gAppui, CHACAL_gBouchon, CHACAL_gReco, CHACAL_gFS];
// ! LA GARDE QUI MANQUAIT. Aucune porte du lecteur ne verifiait qu un homme VIVANT peut marcher, et
// c est pourquoi ce defaut a traverse quinze portes vertes et trois campagnes. On compte, et on ecrit.
CHACAL_SANS_JAMBES = 0;
{ if (alive _x && { !(_x checkAIFeature "PATH") }) then { CHACAL_SANS_JAMBES = CHACAL_SANS_JAMBES + 1 } } forEach CHACAL_FS;
(format ["CHACAL|E|exfil_jambes|%1|vivants|%2|sans_path|%3|seuil_exige|%4", round (time * 100) / 100,
    count (CHACAL_FS select { alive _x }), CHACAL_SANS_JAMBES, round (0.6 * CHACAL_EFFECTIF)]) call CHACAL_LOG;
if (CHACAL_SANS_JAMBES > 0) then {
    (format ["CHACAL|AVERT|exfil|hommes_vivants_sans_jambes|%1", CHACAL_SANS_JAMBES]) call CHACAL_LOG;
};'''
    s2 = s.replace(a, n, 1)
    if bil(s) != bil(s2): print("  !! equilibre 60_phases", bil(s), bil(s2)); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 60_phases : les jambes rendues sans condition, et la garde qui compte")

p = f"{M}/00_socle.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_SANS_JAMBES" in s:
    print("  00_socle : deja present")
else:
    a = "CHACAL_TIRS_APPUI = 0;"
    if a not in s:
        a = "CHACAL_RELANCES_SOCLE = 0; CHACAL_FUMIGENES = 0; CHACAL_ZONES = 0;"
    if a not in s: print("  !! ancre compteurs absente"); sys.exit(1)
    s2 = s.replace(a, a + "\nCHACAL_SANS_JAMBES = 0;   // hommes vivants incapables de marcher a l exfiltration - la garde du 13/09", 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE : 00_socle : compteur CHACAL_SANS_JAMBES")

p = f"{M}/70_verdict.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "|sans_jambes|" in s:
    print("  70_verdict : deja present")
else:
    a = "|azimut|%47|azimut_joue|%48"
    if a not in s: print("  !! ancre FINI absente"); sys.exit(1)
    s2 = s.replace(a, a + "|sans_jambes|%49", 1)
    b = "CHACAL_EXFIL, CHACAL_AZIMUT, CHACAL_AZIMUT_CHOISI]) call CHACAL_LOG;"
    if b not in s2: print("  !! ancre valeurs absente"); sys.exit(1)
    s3 = s2.replace(b, "CHACAL_EXFIL, CHACAL_AZIMUT, CHACAL_AZIMUT_CHOISI, CHACAL_SANS_JAMBES]) call CHACAL_LOG;", 1)
    if bil(s) != bil(s3): print("  !! equilibre 70_verdict"); sys.exit(1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s3)
    print("  PATCHE : 70_verdict : sans_jambes dans la ligne FINI")
