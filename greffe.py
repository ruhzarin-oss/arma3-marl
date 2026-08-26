#!/usr/bin/env python3
"""greffe — LA MESURE À UN JOUR, IMPOSÉE PAR FABLE AVANT TOUT AUTRE RUN.

LA FAILLE QU'ELLE RÉPARE
  Mon contrôle positif était ancré sur la MAUVAISE LIGNE DE BASE. Le +20,4 points du prix
  a été mesuré au-dessus de la doctrine `frontal` à 12,8 %. La valeur du prix au-dessus
  d'un NAVIGATEUR à 49,6 % n'a jamais été mesurée. C'est elle qui décide de tout.

LE GESTE
  On prend la politique A FIGÉE. Au moment de décider, on filtre son choix par le prix :
  parmi ses trois actions les plus probables, on prend LA MOINS CHÈRE. Zéro apprentissage,
  zéro gradient, zéro paramètre nouveau. On juge sur les graines JAMAIS vues.

LA LECTURE, DÉPOSÉE AVANT LES CHIFFRES
  · greffe − témoin ≥ +5 pts -> il Y A de la marge au-dessus du navigateur ; l'apprentissage
    a échoué à la collecter ; le CRÉDIT est confirmé coupable et le façonnage est justifié.
  · greffe ≈ témoin          -> il n'y a RIEN à créditer au-dessus de la navigation ; le
    façonnage est sans objet ; la question quitte ce gymnase.

LE CONTRÔLE, SANS LEQUEL CE ZÉRO NE VAUDRAIT RIEN
  Une greffe au PRIX PERMUTÉ entre les 8 caps. Même geste, même nombre d'actions écartées,
  même distribution de prix — seule l'affectation prix↔cap est détruite. Si elle gagne
  autant, ce n'est pas le prix qui agit, c'est le fait de rabattre sur le top-3.
"""
import sys, math, json, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import prix_des_actions

DEV = "cuda:0"
CKPT = "/home/younes/arma3-marl/pol_1200_g0.pt"
K_TOP = 3          # parmi les 3 plus probables — la meme largeur que la regle scriptee

print("=" * 78); print(" LA GREFFE — le prix a-t-il de la marge au-dessus du NAVIGATEUR ?")
print("=" * 78)

pol = B.Politique(12).to(DEV)
pol.load_state_dict(torch.load(CKPT, map_location=DEV)); pol.eval()
print("\n  politique figee : %s  (aucun gradient, aucun parametre neuf)" % CKPT)


def joueur(mode, permute=False, g_perm=None):
    """mode 'temoin' : la politique telle quelle (echantillonnage, decision du 24/08).
       mode 'greffe' : parmi ses K_TOP plus probables, la MOINS CHERE."""
    def f(o, t, _e=None):
        with torch.no_grad():
            lo, v = pol(o)
            if mode == "temoin":
                return torch.distributions.Categorical(logits=lo).sample(), None, None
            top = lo.topk(K_TOP, dim=-1).indices                      # (N,A,K_TOP)
            p = prix_des_actions(_e)                                  # (N,A,8)
            if permute:
                p = p[..., g_perm]                                    # meme prix, autres caps
            # les actions 8 (tenir) et 9 (supprimer) n ont pas de prix de deplacement :
            # on leur donne le prix de la case ACTUELLE, c est a dire ne pas bouger.
            p8 = torch.cat([p, p.mean(-1, keepdim=True).expand(p.shape[0], p.shape[1], 2)], dim=-1)
            pt = torch.gather(p8, 2, top)
            choisi = torch.gather(top, 2, pt.argmin(2, keepdim=True)).squeeze(2)
            return choisi, None, None
    return f


def juge(nom, f):
    pr, tn, dg = [], [], []
    for g in B.GRAINES_TEST:
        e = B.monde(256, g)
        st, *_ = B.jouer(e, lambda o, t, _e=e: f(o, t, _e))
        pr.append(st["prise"]); tn.append(st["metres_tenus"]); dg.append(float(e.admg.mean()))
    m = lambda v: sum(v) / len(v)
    print("  %-30s prise %5.1f %%  [%.1f ; %.1f]   tenus %6.1f m   degats %.3f"
          % (nom, m(pr), min(pr), max(pr), m(tn), m(dg)))
    return m(pr), m(dg), pr


print("\n─── LE JUGEMENT (6 graines JAMAIS vues, decodeur = echantillonnage) ───")
t_pr, t_dg, t_all = juge("TEMOIN  (A figee)", joueur("temoin"))
g_pr, g_dg, g_all = juge("GREFFE  (top-3, le moins cher)", joueur("greffe"))
perm = torch.randperm(8, generator=torch.Generator().manual_seed(7)).to(DEV)
c_pr, c_dg, c_all = juge("CONTROLE (prix PERMUTE)", joueur("greffe", permute=True, g_perm=perm))

print("\n─── LECTURE, SELON LE CRITERE DEPOSE AVANT LES CHIFFRES ───")
print("  greffe - temoin   : %+.1f points   (seuil +5,0)" % (g_pr - t_pr))
print("  controle - temoin : %+.1f points   (doit rester proche de 0)" % (c_pr - t_pr))
print("  greffe - controle : %+.1f points   (c est LA marge attribuable au PRIX)" % (g_pr - c_pr))
print("  degats moyens     : temoin %.3f | greffe %.3f | controle %.3f" % (t_dg, g_dg, c_dg))
print("  appariement par graine (greffe - temoin) : %s"
      % " ".join("%+.1f" % (a - b) for a, b in zip(g_all, t_all)))
if g_pr - t_pr >= 5.0 and g_pr - c_pr >= 3.0:
    v = "MARGE TROUVEE -> le CREDIT est coupable, le faconnage est justifie"
elif g_pr - t_pr >= 5.0:
    v = "⚠️ la greffe gagne MAIS le controle aussi -> c est le rabattage sur le top-3, pas le prix"
else:
    v = "PAS DE MARGE au-dessus du navigateur -> le faconnage est sans objet, la question quitte ce gymnase"
print("\n  VERDICT : %s" % v)
json.dump({"temoin": t_all, "greffe": g_all, "controle": c_all,
           "degats": [t_dg, g_dg, c_dg], "verdict": v},
          open("/mnt/data/greffe_resultats.json", "w"), indent=1)
print()
