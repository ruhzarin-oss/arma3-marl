#!/usr/bin/env python3
"""calibrer_connu — REGLER `feu_sur_connu` SUR UN VERDICT D ARMA, PAS AU JUGEMENT.

LE VERDICT QUI SERT D ANCRE, certifie sur 563 000 observations :

    ETRE VU TUE 2x PLUS FORT QUE VOIR NE PROTEGE — +75 % de mortalite pour un homme
    qui a ete vu, et l effet CROIT avec la distance.

C est un contraste INTERNE au monde : parmi les memes hommes, ceux qui ont ete vus meurent
75 % plus que ceux qui ne l ont pas ete. On le mesure donc ici de la meme facon, et on cherche
la valeur du bouton qui le reproduit.

⚠️ CE QUI FERAIT ECHOUER LA CALIBRATION — ecrit avant :
  · le monde de reference (bouton a zero) rend DEJA +75 % ou plus -> le bouton ne sert a rien
    et on ne l allume pas.
  · aucune valeur du bouton n atteint +75 % -> ce n est pas ce mecanisme qui manque, et on le
    dit au lieu de pousser le bouton jusqu a l absurde.
  · moins de 30 hommes dans l un des deux groupes -> contraste non lisible, on ne conclut pas.
"""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

CIBLE, EPISODES, PAS = 75.0, 512, 60


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def contraste(val, seed=7):
    """Le contraste se lit PAR OBSERVATION (homme x pas), comme Arma l a mesure sur
    563 000 d entre elles — et non en fin d episode, ou TOUT LE MONDE a fini par etre vu
    (2048 vus contre 0 non vus au premier essai : un contraste qui n existe pas)."""
    e = AssaultTerrain(num_envs=EPISODES, seed=seed, device="cuda:0", max_steps=PAS,
                       feu_de_zone=val, **MONDE_ARMA)
    e.reset()
    n_vu = n_non = m_vu = m_non = 0
    viv = e._aalive().clone()
    for t in range(PAS):
        e.step(cap(-e.apx, -e.apy), auto_reset=False)
        neuf = e._aalive()
        mort = viv & ~neuf                       # il est mort PENDANT ce pas
        # ETIQUETTE = VISIBILITE GEOMETRIQUE, relevee AVANT le bouton. Avec `last_exposed`,
        # qui derive du meme `los` que le bouton modifie, le contraste MONTAIT avec le
        # traitement (856 % puis 4086 %) : l etiquette bougeait avec l effet.
        expose = e._vu_geo > 0.5
        if expose is not None:
            vu = expose & viv
            pas_vu = ~expose & viv
            n_vu += int(vu.sum()); m_vu += int((mort & vu).sum())
            n_non += int(pas_vu.sum()); m_non += int((mort & pas_vu).sum())
        viv = neuf
    if n_vu < 30 or n_non < 30:
        return None, n_vu, n_non
    p_vu = m_vu / n_vu
    p_non = m_non / n_non
    if p_non <= 1e-9:
        return float("inf"), n_vu, n_non
    return 100.0 * (p_vu / p_non - 1.0), n_vu, n_non


print("\n  CALIBRATION DE `feu_de_zone` SUR LE VERDICT DES +75 %")
print("  " + "=" * 68)
print(f"    {'bouton':>8}{'surmortalite du VU':>22}{'n vus':>9}{'n non vus':>11}")
best, becart = None, 1e9
for v in (0.0, 0.02, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35, 0.50):
    s, nv, nn = contraste(v)
    if s is None:
        print(f"    {v:>8.2f}{'non lisible':>22}{nv:>9}{nn:>11}")
        continue
    marque = ""
    if abs(s - CIBLE) < becart:
        becart, best, marque = abs(s - CIBLE), v, "  <-"
    print(f"    {v:>8.2f}{s:>21.1f}%{nv:>9}{nn:>11}{marque}")
print("  " + "=" * 68)
if best is None:
    print("    AUCUNE VALEUR LISIBLE. On ne regle rien.")
else:
    s, _, _ = contraste(best)
    print(f"    Retenu : feu_de_zone = {best:.2f}  -> surmortalite {s:.1f} % "
          f"(Arma : {CIBLE:.0f} %)")
    if becart > 25:
        print("    ⚠ L ECART A LA CIBLE RESTE GRAND. Ce n est pas ce seul mecanisme qui")
        print("      manque : on le dit au lieu de pousser le bouton jusqu a l absurde.")
