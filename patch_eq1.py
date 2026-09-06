#!/usr/bin/env python3
"""Branche le canal CWR dans assault_terrain.py. ETEINT PAR DEFAUT, non regressif.
Trois ancres exactes, sauvegarde `.avantcanal`, et il refuse si une ancre a bouge."""
import sys, shutil, os
P = "/home/younes/arma3-marl/assault_terrain.py"
s = open(P, encoding="utf-8").read()
if "canal_cwr" in s:
    print("  DEJA BRANCHE — rien fait."); sys.exit(0)

A = [
# ── 1. signature ────────────────────────────────────────────────────────────────
("cible_unique=True, feu_sur_connu=0.0, feu_de_zone=0.0, relief_stratis=False):",
 "cible_unique=True, feu_sur_connu=0.0, feu_de_zone=0.0, relief_stratis=False, canal_cwr=None):"),

# ── 2. validation en fin de __init__ ────────────────────────────────────────────
("        self._reset(torch.arange(num_envs, device=device))",
 """        # ─── EQUATION 1 : LE CANAL DE DETECTION DE `Target.cpp` (CWR/Poseidon, RV1) ───
        # Ce que ca change, et RIEN D AUTRE : la designation de cible passe de
        # `los > 0.5` (interrupteur binaire) a `sideAccuracy >= 1.5` (canal continu).
        # Pourquoi : dans la source, le couvert MULTIPLIE la vue, l ouie le traverse a
        # 90 %, et l ouie seule plafonne a 1,4 contre un seuil de camp a 1,5 — elle dit
        # « quelque chose est la », jamais « c est un ennemi ». Le gymnase, lui, rendait
        # la mortalite des jamais-vus EXACTEMENT NULLE ; Arma 3 mesure +75 %, pas l infini.
        # ⚠️ RV1 N EST PAS RV3 : c est une HYPOTHESE, une nuit Arma 3 la confirme ou la tue.
        # ETEINT PAR DEFAUT. `MONDE_ARMA` ne bouge pas : la batterie gelee n est pas touchee.
        self.canal = None
        if canal_cwr is not None:
            import canal_cwr as _CANAL
            self._CANAL = _CANAL
            # `provisoire()` porte deja la cle `mesure` : on ne le revalide pas, il a crie.
            self.canal = dict(canal_cwr) if "mesure" in canal_cwr else _CANAL.constantes(**canal_cwr)
            # Le canal a besoin d une FRACTION de corps visible — l analogue de
            # `Visibility(brain, ai)`. Sans replique, le gymnase ne sait produire qu un
            # `los` BINAIRE (terrain_gpu.los_clear rend 0 ou 1) et l equation perd son
            # objet : c est le mur 2,5D, pas un reglage. Donc on refuse.
            if not (self.replica and self.emergent_expo):
                raise ValueError(
                    "canal_cwr exige replica=True ET emergent_expo=True : l equation 1 porte sur "
                    "une FRACTION de corps visible, et sans replique le gymnase n a qu un los BINAIRE")
            if not self.cible_unique:
                raise ValueError("canal_cwr remplace la porte de designation de `cible_unique` : "
                                 "l activer sans cible_unique ne changerait rien (module inerte)")
        self._reset(torch.arange(num_envs, device=device))"""),

# ── 3. la porte de designation, dans step() ─────────────────────────────────────
("""            tir = active
            if self.cible_unique:
                _elig = (active > 0) & (los > 0.5) & self._aalive()""",
 """            tir = active
            _efrac = None
            if self.canal is not None:
                # LA DESIGNATION PASSE PAR LE CANAL. `_dans_f` est la porte de tir DEJA en
                # service (arc + detection) : on ne superpose pas les cosinus 15/45 de RV1,
                # ca compterait deux fois le meme effet.
                _efrac = self._body_exposure(self.apx, self.apy, self._eye(), bx, by)
                self._canal_out = self._CANAL.canal(_efrac, dist, self.canal, porte_cone=_dans_f)
            if self.cible_unique:
                _porte = (self._canal_out["designe"] if self.canal is not None else (los > 0.5))
                _elig = (active > 0) & _porte & self._aalive()"""),

# ── 4. la porte de tir relevee en float pour le canal ───────────────────────────
("""                active = active * _dans.float()     # hors cône ET sursis non ecoule = ne peut pas tirer""",
 """                _dans_f = _dans.float()
                active = active * _dans_f     # hors cône ET sursis non ecoule = ne peut pas tirer"""),

# ── 5. ne pas recalculer efrac deux fois ────────────────────────────────────────
("""            if self.emergent_expo and self.replica:                # EXPOSITION EMERGENTE : fraction du corps touchable = geometrie (couvert deja capture par les rayons)
                efrac = self._body_exposure(self.apx, self.apy, self._eye(), bx, by)""",
 """            if self.emergent_expo and self.replica:                # EXPOSITION EMERGENTE : fraction du corps touchable = geometrie (couvert deja capture par les rayons)
                efrac = _efrac if _efrac is not None else self._body_exposure(self.apx, self.apy, self._eye(), bx, by)"""),
]

# `_dans_f` doit exister meme quand def_line est eteint : on l initialise dans la boucle.
LOSL = "            los = self._losc(self.hm, self.apx, self.apy, bx, by, self.scale, eye_a=self._eye(), eye_b=1.7)"
A.append((
"""        for di in range(D):
            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)
""" + LOSL,
"""        for di in range(D):
            _dans_f = None      # porte de tir du defenseur, relevee pour le canal CWR
            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)
""" + LOSL))

for i, (old, new) in enumerate(A, 1):
    n = s.count(old)
    if n != 1:
        sys.exit("ANCRE %d introuvable ou ambigue (%d occurrences) — RIEN N EST ECRIT.\n---\n%s" % (i, n, old[:200]))
    s = s.replace(old, new)

shutil.copy2(P, P + ".avantcanal")
open(P, "w", encoding="utf-8").write(s)
print("  6 ancres appliquees. Sauvegarde : assault_terrain.py.avantcanal")
