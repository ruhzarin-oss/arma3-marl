#!/usr/bin/env python3
"""tri_contradiction — LE SCORE NE SAIT PAS TRIER, L ACCORD SI ⟨Fable, 26/08⟩.

La greffe fait 61,6 % et E2 fait 61,7 % : un PLAFOND du gymnase est plausible vers 61-62.
Un eleve qui atteint 61 n a donc peut-etre rien appris du prix.

On ne juge plus le score. On juge l ACCORD AVEC LE MAITRE, et UNIQUEMENT sur les etats ou
le moins-cher-du-top-3 CONTREDIT l action la plus probable de A. Sur ceux-la, suivre A et
suivre le prix menent a des actions differentes — c est le seul endroit ou la question se pose.
"""
import sys, os, glob, json, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import prix_des_actions
from distillation import Eleve, charger_maitre, K_TOP

DEV = "cuda:0"
print("=" * 84); print(" TRI DE CONTRADICTION — l eleve suit-il A, ou suit-il le PRIX ?")
print("=" * 84)
maitre = charger_maitre()

def analyse(nom, el, avec_prix):
    acc_m = acc_a = n_contr = n_tot = 0
    for g in B.GRAINES_TEST:
        e = B.monde(256, g); o = e.reset()
        fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
        for t in range(B.PAS):
            with torch.no_grad():
                lo_a, _ = maitre(o)
                p = prix_des_actions(e)
                top = lo_a.topk(K_TOP, -1).indices
                p8 = torch.cat([p, p.mean(-1, keepdim=True).expand(p.shape[0], p.shape[1], 2)], -1)
                a_maitre = torch.gather(top, 2, torch.gather(p8, 2, top).argmin(2, keepdim=True)).squeeze(2)
                a_navig = lo_a.argmax(-1)                      # ce que A ferait, sans le prix
                lo_e, _ = el(o, p if avec_prix else None)
                a_eleve = lo_e.argmax(-1)
            viv = e._aalive() & ~fini.unsqueeze(1)
            contr = (a_maitre != a_navig) & viv               # LE PRIX CONTREDIT LE NAVIGATEUR
            n_contr += int(contr.sum()); n_tot += int(viv.sum())
            acc_m += int(((a_eleve == a_maitre) & contr).sum())
            acc_a += int(((a_eleve == a_navig) & contr).sum())
            with torch.no_grad():
                a = torch.distributions.Categorical(logits=lo_e).sample()
            o, _, done, _ = e.step(a, auto_reset=False)
            fini |= done.bool()
            if bool(fini.all()): break
    if n_contr == 0: print("  %-6s aucun etat de contradiction" % nom); return
    print("  %-6s contradictions %5.1f %% des pas | suit le MAITRE %5.1f %% | suit A %5.1f %%   -> %s"
          % (nom, 100 * n_contr / max(n_tot, 1), 100 * acc_m / n_contr, 100 * acc_a / n_contr,
             "SUIT LE PRIX" if acc_m > 1.6 * acc_a else "SUIT LE NAVIGATEUR (plafond, pas apprentissage)"
             if acc_a > 1.6 * acc_m else "indecis"))

e0 = B.monde(8, B.GRAINES_TRAIN[0]); e0.reset(); nobs = e0._obs().shape[-1]
for f in sorted(glob.glob("/mnt/data/eleve_*.pt")):
    b = os.path.basename(f)[6:-3]                              # ex "D1_0"
    et = b.split("_")[0]
    el = Eleve(nobs, avec_prix=(et == "D2")).to(DEV)
    try: el.load_state_dict(torch.load(f, map_location=DEV))
    except Exception as ex: print("  %-6s illisible (%s)" % (b, str(ex)[:30])); continue
    el.eval(); analyse(b, el, et == "D2")
print("\n  LECTURE : un eleve qui a INTERNALISE le prix suit le MAITRE sur ces etats.")
print("            un eleve qui a seulement touche le PLAFOND suit A.")
print("            D3 (cible au hasard) doit suivre NI l un NI l autre nettement.")
