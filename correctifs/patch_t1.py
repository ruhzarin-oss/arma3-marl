#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-T1-ZONE
# Deux defauts vus au premier episode du tournoi (12/09, 03:53) :
#  1. T1 n avait AUCUNE cible au depart : il attend qu un defenseur se trahisse en tirant, or personne ne tire tant
#     que l assaut ne bouge pas. Mesure : t1_depart|premier_tir_appui|-1|attente|126. Le document de tactiques le
#     prevoyait : « defenseur non localise -> suppression de zone sur le QG et sur la position probable du FM ».
#  2. CHACAL_CIBLE_ASSAUT n existait pas encore quand le chien de garde demarrait : 24 erreurs sans consequence.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    if s.count(avant) != 1: print("  !! motif x%d : %s" % (s.count(avant), quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2): print("  !! equilibre : %s" % quoi); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2); print("  PATCHE :", quoi)
if "suppression_de_zone" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)
# 1. les variables existent des le socle
patch(f"{M}/00_socle.sqf", "CHACAL_RELANCES_SOCLE = 0; CHACAL_FUMIGENES = 0;",
      "CHACAL_RELANCES_SOCLE = 0; CHACAL_FUMIGENES = 0; CHACAL_ZONES = 0;\n"
      "CHACAL_CIBLE_ASSAUT = [];   // ! posee ici : le chien de garde demarrait avant son initialisation",
      "00_socle : variables posees avant tout spawn")
# 2. T1 : a defaut de cible connue, on arrose la zone
patch(f"{M}/00_socle.sqf",
      '''            if (count _cn > 0) then {''',
      '''            if (count _cn == 0) then {
                // ! AUCUN DEFENSEUR LOCALISE : suppression DE ZONE sur l objectif, comme le prevoit la doctrine.
                // Sans elle, T1 attend un ennemi qui n a aucune raison de tirer le premier, et l assaut part sans appui.
                if (time - _tSupp > 30) then {
                    _tSupp = time; CHACAL_ZONES = CHACAL_ZONES + 1;
                    private _z = if (!isNull CHACAL_PC) then { getPosATL CHACAL_PC } else { CHACAL_SITE };
                    { _x doWatch _z; _x doSuppressiveFire _z } forEach _app;
                    (format ["CHACAL|E|suppression_de_zone|%1|vers|%2|n|%3", round (time * 100) / 100, str _z, CHACAL_ZONES]) call CHACAL_LOG;
                };
            };
            if (count _cn > 0) then {''', "00_socle : T1 arrose la zone quand aucun defenseur n est connu")
# 3. le compteur de zones dans la ligne FINI
patch(f"{M}/70_verdict.sqf", '|relances|%38|fumigenes|%39",', '|relances|%38|fumigenes|%39|zones|%40",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", "CHACAL_RELANCES_SOCLE, CHACAL_FUMIGENES]) call CHACAL_LOG;",
      "CHACAL_RELANCES_SOCLE, CHACAL_FUMIGENES, CHACAL_ZONES]) call CHACAL_LOG;", "70_verdict : valeurs FINI")
