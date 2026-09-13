#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-COLLISION-DE-NOMS
# Le controle d identite generique a REFUSE un episode valide : "azimut demande 2, joue 270".
# Il avait raison de refuser, et le defaut etait dans mon nommage. Le job appelle "azimut" le MODE
# du decideur (0, 1 ou 2) ; la ligne FINI appelait "azimut" l ANGLE retenu (270). Le controle a
# compare un mode a un angle.
# Lecon : une garde generique qui compare des champs par leur NOM exige que les noms soient uniques
# et qu ils designent la meme chose des deux cotes. Sinon elle fabrique des faux refus, et un faux
# refus coute un episode d une heure.
# Correction : dans la ligne FINI, "azimut" designe le mode, comme dans le job, et l angle retenu
# devient "azimut_joue". Ce nom ne peut se confondre avec aucun champ du job.
import sys
p = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/70_verdict.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
a = "|azimut_mode|%47|azimut|%48"
if a not in s:
    if "|azimut|%47|azimut_joue|%48" in s: print("  deja corrige"); sys.exit(0)
    print("  !! ancre absente"); sys.exit(1)
s2 = s.replace(a, "|azimut|%47|azimut_joue|%48", 1)
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"), t.count('"') % 2)
if bil(s) != bil(s2): print("  !! equilibre"); sys.exit(1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : 70_verdict : azimut = le mode (comme le job), azimut_joue = l angle retenu")
