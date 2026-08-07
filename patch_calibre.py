#!/usr/bin/env python3
"""patch_calibre.py — BRANCHER LA CALIBRATION SUR LA LOI DU MONDE.

La sortie du predicteur etait un SCORE de classement, prise pour une probabilite. Plancher a
5,53 % de mort par pas dans la sandbox : meme hors de tout cone, on mourait, donc sortir du
champ n achetait rien et seule la longueur du chemin comptait.

La calibration est ecrite et ses quatre portes passent (commit 0f98c2a) : transformation
MONOTONE, AUC intacte a 0,00015 pres, moyenne 9,73 % contre une base de 10,38 %, plancher
tombe de 0,98 % a 0,253 % de mort par pas.

On la branche a UN SEUL endroit : la loi de mort. Le champ observe et le scalaire de risque
gardent le score brut — un seul levier change, et c est la LOI, pas la perception.
"""
import pathlib

P = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = P.read_text(encoding='utf-8')

ANC = '''def p_mort_du_pas(p_xy, post_poids, idx):'''
NEUF = '''# LA CALIBRATION, ecrite le 07/08 apres reparation du decoupage (346 blocs de 100 s).
# Sans elle la sortie du predicteur est un SCORE, pas une probabilite : plancher a 5,53 % de
# mort par pas, et « hors de tout cone » n achete rien.
_cal = _np.load('/mnt/data/corpus/calibration_risque.npz')
CAL_X = torch.tensor(_cal['centres'], device=dev, dtype=torch.float32)
CAL_Y = torch.tensor(_cal['taux'], device=dev, dtype=torch.float32)
print(f"calibration chargee — {len(CAL_X)} noeuds, de {CAL_Y.min():.3%} a {CAL_Y.max():.1%}",
      flush=True)

def calibrer(s):
    """score -> probabilite de mourir a 30 s. Interpolation lineaire, monotone."""
    i = torch.searchsorted(CAL_X, s.contiguous().clamp(CAL_X[0], CAL_X[-1]))
    i = i.clamp(1, len(CAL_X) - 1)
    x0, x1 = CAL_X[i - 1], CAL_X[i]
    y0, y1 = CAL_Y[i - 1], CAL_Y[i]
    w = ((s.clamp(CAL_X[0], CAL_X[-1]) - x0) / (x1 - x0).clamp(min=1e-9)).clamp(0, 1)
    return y0 + (y1 - y0) * w

def p_mort_du_pas(p_xy, post_poids, idx):'''
assert t.count(ANC) == 1, "ancre p_mort_du_pas"
t = t.replace(ANC, NEUF, 1)

A2 = "    p30 = risque(p_xy, None, idx, post_poids).clamp(1e-6, 1 - 1e-6)"
N2 = ("    # LE SCORE DEVIENT UNE PROBABILITE. C est le seul endroit ou la calibration entre :\n"
      "    # le champ observe et le scalaire de risque gardent le score brut.\n"
      "    p30 = calibrer(risque(p_xy, None, idx, post_poids)).clamp(1e-6, 1 - 1e-6)")
assert t.count(A2) == 1, "ancre p30"
t = t.replace(A2, N2, 1)

if 'import numpy as _np' not in t:
    t = t.replace('import torch', 'import torch\nimport numpy as _np', 1)

P.write_text(t, encoding='utf-8')
print("calibration branchee sur la loi de mort — un seul levier change")
