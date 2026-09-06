#!/usr/bin/env python3
"""CORRECTION. La fenetre de 10 s n est pas une PERMISSION, c est une RESTRICTION.
`WhatFireResult` recalcule la visibilite COURANTE et refuse sous 0,63 (TargetFire.cpp:1203) ;
la fenetre de 10 s s AJOUTE a ce refus (l.1241). Les trois conditions sont ET, pas OU."""
import sys, shutil
P = "/home/younes/arma3-marl/assault_terrain.py"
s = open(P, encoding="utf-8").read()
OLD = """                    _frais = ((self.t.unsqueeze(1).float() - self.a_dernier_vu)
                              <= float(self.canal_mem_pas))
                    _visible_ok = self._canal_out["designe"] | (_frais & (self.a_dernier_vu > -1e8))
                    _elig = (active > 0) & _visible_ok & self._aalive()"""
NEW = """                    # ⛔ CORRECTION. J avais lu la fenetre de 10 s comme une PERMISSION
                    # (« le defenseur bat la derniere position connue »). LA SOURCE EN FAIT
                    # UNE RESTRICTION : `WhatFireResult` recalcule la visibilite COURANTE et
                    # refuse sous `MinVisibleFire` (TargetFire.cpp:1203), et la fenetre de
                    # 10 s S AJOUTE a ce refus (l.1241). Les trois conditions sont ET, pas OU.
                    # Consequence dure : il n existe AUCUN tir VISE sur un homme actuellement
                    # cache — ce que la porte `posError > 2*indirectHitRange` disait deja
                    # pour un fusil. Donc le +75 % d Arma 3 ne peut PAS venir de la, et
                    # c est une question de MESURE, pas de modele. Falsificateur au depot.
                    _frais = (((self.t.unsqueeze(1).float() - self.a_dernier_vu)
                               <= float(self.canal_mem_pas)) & (self.a_dernier_vu > -1e8))
                    _voit_assez = (_efrac >= self._CANAL.MIN_VISIBLE_FIRE)
                    _elig = ((active > 0) & self._canal_out["designe"]
                             & _voit_assez & _frais & self._aalive())"""
if NEW.split("\n")[-1] in s:
    print("  DEJA CORRIGE — rien fait."); sys.exit(0)
if s.count(OLD) != 1:
    sys.exit("ancre introuvable (%d) — RIEN N EST ECRIT" % s.count(OLD))
shutil.copy2(P, P + ".avantetrestriction")
open(P, "w", encoding="utf-8").write(s.replace(OLD, NEW))
print("  correction appliquee. Sauvegarde : assault_terrain.py.avantetrestriction")
