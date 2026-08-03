#!/usr/bin/env python3
"""reflexe.py — LA COUCHE REACTIVE (v6). Criteres CRITERES_V6_REFLEXE.md 4420f233b5b301be.

Un reflexe n est pas une decision rapide, c est une decision QU ON NE PREND PAS. La couche
s applique APRES la politique et peut passer outre. On n apprend plus a ne pas s exposer :
on ne le peut plus.

Le budget agit MECANIQUEMENT sur les seuils : meme avec des seuils tires au hasard, un petit
budget declenche le couvert et le decrochage plus tot. C est la que l ordre est cable dans le
corps, au lieu de dependre d une recompense lointaine — deux tentatives par la recompense ont
echoue (dose plate a 3,0 quel que soit le budget, mesure du 2026-07-29).

QUATRE REGLES, toutes tirees des politiques de reference qui atteignent 87,5 % :
    R1 couvert       exposition instantanee > seuil1        -> posture basse
    R2 decrochage    dose consommee > seuil2 * B            -> cap qui expose le moins
    R3 appui         a l arret ET a portee                  -> APPUI plutot que l inaction
    R4 franchissement distance objectif < seuil4            -> avancer, APPUI INTERDIT

R4 est la version mecanique d une mesure faite sur le vrai Arma : l ordre de tir de
suppression ARRETE l unite, et six semaines d enlisement venaient de la.

GARANTIE ANTI-IMMOBILITE, assertee et non esperee : au-dela de K pas consecutifs d action
stationnaire imposee, toutes les substitutions sont desactivees pour un pas.
"""
import math
import torch

HOLD, APPUI = 8, 9
POSTURE_BASSE = 12
K_STATIONNAIRE = 3          # au-dela, la politique reprend la main pour un pas
N_SEUILS = 4

# bornes des seuils effectifs, avant modulation par le budget
BORNES = [(0.05, 0.60),     # R1 : fraction d exposition instantanee
          (0.20, 0.95),     # R2 : fraction du budget consommee
          (0.0, 1.0),       # R3 : sans unite, sert de commutateur doux
          (10.0, 45.0)]     # R4 : metres


def modulation(B, B_max=4.2):
    """g(B), monotone croissante : un petit budget abaisse les seuils, donc declenche plus tot.
    C est le cablage de l ordre dans le corps. Bornee pour rester stable."""
    return (0.25 + 0.75 * (B / B_max).clamp(0.05, 1.0))


class CoucheReflexe:
    def __init__(self, N, A, device):
        self.dev = device
        self.compteur = torch.zeros(N, A, dtype=torch.long, device=device)

    def reset(self, idx=None):
        if idx is None:
            self.compteur.zero_()
        else:
            self.compteur[idx] = 0

    def applique(self, acts, seuils, m, actif=True, brut=False):
        """acts (N,A) proposees par la politique ; seuils (N,A,4) dans [0,1] emis par le reseau.
        Renvoie (actions_finales, taux_substitution)."""
        if not actif:
            return acts, torch.zeros((), device=self.dev)
        N, A = acts.shape
        B = m.Emax[:, None].expand(N, A)
        g = modulation(B)
        if brut:
            # CONTROLE NUL : les seuils sont utilises TELS QUELS, sans bornes ni modulation.
            # C est ainsi qu on les pousse a l infini pour prouver que la couche, eteinte,
            # reproduit EXACTEMENT la politique. Une couche qui ne prouve pas son inertie
            # ne peut pas prouver son effet.
            s = [seuils[..., i] for i in range(N_SEUILS)]
        else:
            s = [BORNES[i][0] + (BORNES[i][1] - BORNES[i][0]) * seuils[..., i] for i in range(N_SEUILS)]
            s = [s[i] * g if i in (0, 1, 3) else s[i] for i in range(N_SEUILS)]

        expo = m.env.last_exposed if hasattr(m.env, 'last_exposed') else torch.zeros_like(acts).float()
        dose = (m.expo_cum / m.Emax.clamp(min=1e-6))[:, None].expand(N, A)
        dist = torch.sqrt(m.env.apx ** 2 + m.env.apy ** 2)
        vivant = m.env._aalive()

        cap_obj = (torch.round(torch.atan2(-m.env.apx, -m.env.apy) / (math.pi / 4.0)).long() % 8)
        # le cap qui expose le moins : oppose a l objectif, approximation defendable et bornee
        cap_fuite = (cap_obj + 4) % 8

        final = acts.clone()
        stationnaire = torch.zeros_like(acts, dtype=torch.bool)

        # R3 appui : a l arret et a portee -> appuyer plutot que ne rien faire
        # R3 est branchee sur son seuil, sinon elle serait ineteignable et le
        # controle nul deviendrait impossible.
        r3 = (acts == HOLD) & (dist < m.env.fire_range * 0.9) & vivant & (s[2] > 0.5)
        final = torch.where(r3, torch.full_like(final, APPUI), final)
        stationnaire |= r3

        # R1 couvert : trop expose -> posture basse
        r1 = (expo > s[0]) & vivant
        final = torch.where(r1, torch.full_like(final, POSTURE_BASSE), final)
        stationnaire |= r1

        # R2 decrochage : budget entame au-dela du seuil -> s eloigner. C est un DEPLACEMENT.
        r2 = (dose > s[1]) & vivant
        final = torch.where(r2, cap_fuite, final)
        stationnaire &= ~r2

        # R4 franchissement : au contact, on avance et l appui est INTERDIT
        r4 = (dist < s[3]) & vivant
        final = torch.where(r4, cap_obj, final)
        stationnaire &= ~r4

        # GARANTIE : au-dela de K pas stationnaires imposes, la politique reprend la main
        self.compteur = torch.where(stationnaire, self.compteur + 1,
                                    torch.zeros_like(self.compteur))
        relache = self.compteur > K_STATIONNAIRE
        final = torch.where(relache, acts, final)
        self.compteur = torch.where(relache, torch.zeros_like(self.compteur), self.compteur)

        return final, (final != acts).float().mean()
