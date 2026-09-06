#!/usr/bin/env python3
"""desaccord_maitre — LA LAME DE FABLE, APPLIQUEE AVANT DE DEPENSER TROIS HEURES.

« Avant d entrainer, mesure le taux de DESACCORD professeur<->temoin ; sans desaccord
frequent, il n y a pas de lecon. » D1 a echoue hier sur un signal redondant a 88 % avec le
navigateur, et c etait mesurable avant le premier gradient. On ne refait pas cette faute.

On mesure le desaccord du nouveau maitre (SHAMAL sans bounding, 84,6 %) contre TROIS choses :
  · la REFERENCE apprise `A` — c est elle que l eleve part de savoir imiter ;
  · l ANCIEN maitre (la greffe a 61,6 %) — pour situer les deux lecons l une par rapport a l autre ;
  · son propre CONTROLE S3 (cap au hasard) — il doit etre tres eleve, sinon le controle est mou.
Et sur la distribution d etats du MAITRE, puis sur celle de la REFERENCE : un desaccord qui
n existe que chez l un des deux ne s enseigne pas de la meme facon.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import prix_des_actions
from distillation import charger_maitre, MAITRE_SHAMAL, cible_shamal, K_TOP
from shamal_teacher import shamal_action

DEV = "cuda:0"
ref = charger_maitre()

def greffe(o, e):
    with torch.no_grad():
        lo, _ = ref(o)
        top = lo.topk(K_TOP, -1).indices
        p = prix_des_actions(e)
        p8 = torch.cat([p, p.mean(-1, keepdim=True).expand(p.shape[0], p.shape[1], 2)], -1)
        return torch.gather(top, 2, torch.gather(p8, 2, top).argmin(2, keepdim=True)).squeeze(2)

def argmax_ref(o, e):
    with torch.no_grad():
        lo, _ = ref(o)
    return lo.argmax(-1)

def mesure(pilote, nom_pilote, paires, n=256):
    """`pilote` conduit ; on compare les avis des deux membres de chaque paire au meme instant."""
    cpt = {k: [0, 0] for k in paires}
    for g in B.GRAINES_TEST[:3]:
        e = B.monde(n, g); o = e.reset()
        fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
        for t in range(B.PAS):
            viv = e._aalive() & ~fini.unsqueeze(1)
            for k, (fa, fb) in paires.items():
                a, b = fa(o, e), fb(o, e)
                cpt[k][0] += int(((a != b) & viv).sum()); cpt[k][1] += int(viv.sum())
            o, _, done, _ = e.step(pilote(o, e), auto_reset=False)
            fini |= done.bool()
            if bool(fini.all()): break
    print("  — distribution d etats : %s —" % nom_pilote)
    for k, (d, tt) in cpt.items():
        v = 100.0 * d / max(tt, 1)
        print("    %-42s %6.1f %%   %s" % (k, v, "LECON" if v >= 20 else "leçon faible" if v >= 5 else "PAS DE LECON"))
    return cpt

maitre = lambda o, e: cible_shamal(e)
paires = {
    "MAITRE 84,6 %  contre  reference A": (maitre, argmax_ref),
    "MAITRE 84,6 %  contre  greffe 61,6 %": (maitre, greffe),
    "MAITRE 84,6 %  contre  son controle S3": (maitre, lambda o, e: cible_shamal(e, hasard=True)),
    "greffe 61,6 %  contre  reference A  (D1 hier)": (greffe, argmax_ref),
}
print("=" * 92); print(" DESACCORD — y a-t-il une LECON a enseigner ?"); print("=" * 92)
mesure(maitre, "le MAITRE conduit (c est la distribution d entrainement)", paires)
print()
mesure(argmax_ref, "la REFERENCE conduit", paires)
print("\n  Rappel du 25/08 : D1 apprenait un signal en desaccord sur 12,4 % des pas seulement,")
print("  et il s est effondre sur la reference (il la suivait a 93-95 % la ou elle differait).")
