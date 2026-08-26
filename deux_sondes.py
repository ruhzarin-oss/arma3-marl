#!/usr/bin/env python3
"""deux_sondes — les deux verifications d une heure imposees par Fable AVANT tout depot.

SONDE 1 — LE CONTROLE DE LA GREFFE ETAIT BIAISE
  Ma permutation du prix etait tiree UNE FOIS et gardee fixe sur tout le banc. Elle portait
  donc un biais DIRECTIONNEL constant (favoriser toujours le meme cap peut aider ou nuire
  par pure geometrie), et le +10,9 en heritait. On la retire A CHAQUE DECISION.

SONDE 2 — LES DEUX JUGES SUR LA MEME POLITIQUE
  Mon bras A rend 49,6 % et l artefact du depot 39,3 %. Deux suspects : la loterie
  d entrainement (connue, classee) ou UN PROBLEME DE JUGE. On tranche en jugeant le MEME
  artefact avec les DEUX codes. S ils divergent sur la meme politique, le banc a un juge
  qui n imprime pas ce qu il calcule — et ce dossier a deja paye pour savoir ce que ca coute.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
import banc_raster as BR
from banc_raster import prix_des_actions

DEV = "cuda:0"; CKPT = "/home/younes/arma3-marl/pol_1200_g0.pt"; K_TOP = 3
pol = B.Politique(12).to(DEV)
pol.load_state_dict(torch.load(CKPT, map_location=DEV)); pol.eval()

print("=" * 78); print(" SONDE 1 — LE CONTROLE, PERMUTATION RETIREE A CHAQUE DECISION")
print("=" * 78)

def joueur(mode, perm=None):
    """perm : None = pas de permutation | 'fixe' = une seule pour tout | 'chaque' = a chaque pas"""
    fixe = torch.randperm(8, generator=torch.Generator().manual_seed(7)).to(DEV)
    def f(o, t, _e):
        with torch.no_grad():
            lo, v = pol(o)
            if mode == "temoin":
                return torch.distributions.Categorical(logits=lo).sample(), None, None
            top = lo.topk(K_TOP, dim=-1).indices
            p = prix_des_actions(_e)
            if perm == "fixe":
                p = p[..., fixe]
            elif perm == "chaque":
                # UNE PERMUTATION PAR HOMME ET PAR PAS : plus aucun biais directionnel
                N, A = p.shape[0], p.shape[1]
                idx = torch.argsort(torch.rand(N, A, 8, device=DEV), dim=2)
                p = torch.gather(p, 2, idx)
            p8 = torch.cat([p, p.mean(-1, keepdim=True).expand(p.shape[0], p.shape[1], 2)], -1)
            pt = torch.gather(p8, 2, top)
            return torch.gather(top, 2, pt.argmin(2, keepdim=True)).squeeze(2), None, None
    return f

def juge(nom, f):
    pr = []
    for g in B.GRAINES_TEST:
        e = B.monde(256, g)
        st, *_ = B.jouer(e, lambda o, t, _e=e: f(o, t, _e))
        pr.append(st["prise"])
    m = sum(pr) / len(pr)
    print("  %-38s %5.1f %%   [%.1f ; %.1f]" % (nom, m, min(pr), max(pr)))
    return m, pr

t, t_all = juge("TEMOIN (A figee, echantillonnage)", joueur("temoin"))
g, g_all = juge("GREFFE (top-3, le moins cher)", joueur("greffe"))
cf, _ = juge("CONTROLE permutation FIXE (mon erreur)", joueur("greffe", "fixe"))
cc, c_all = juge("CONTROLE permutation A CHAQUE PAS", joueur("greffe", "chaque"))

print("\n  greffe - temoin              %+6.1f" % (g - t))
print("  controle FIXE - temoin       %+6.1f   <- le chiffre biaise que j avais annonce" % (cf - t))
print("  controle A CHAQUE PAS - temoin %+4.1f   <- le bon" % (cc - t))
print("  MARGE ATTRIBUABLE AU PRIX    %+6.1f   (greffe - controle a chaque pas)" % (g - cc))
print("  appariement par graine       %s"
      % " ".join("%+.1f" % (a - b) for a, b in zip(g_all, c_all)))
print("  le biais directionnel valait %+.1f point" % (cf - cc))

print("\n" + "=" * 78); print(" SONDE 2 — LES DEUX JUGES, SUR LA MEME POLITIQUE")
print("=" * 78)
r_b, m_b = B.evaluer(pol, B.GRAINES_TEST, n=256)
p_b = sum(r_b["appris"]) / len(r_b["appris"])
# `banc_raster.evaluer` appelle pol(o, r) ; la Politique du depot ne prend que (o).
class _Enveloppe(torch.nn.Module):
    def __init__(self, p): super().__init__(); self.p = p
    def forward(self, o, r=None): return self.p(o)
p_r, t_r = BR.evaluer(_Enveloppe(pol).to(DEV), "A", B.GRAINES_TEST, n=256)
print("  juge de `boucle.evaluer`   : %5.1f %%   par graine %s"
      % (p_b, " ".join("%.1f" % x for x in r_b["appris"])))
print("  juge de `banc_raster.evaluer`: %5.1f %%" % p_r)
print("  ecart entre les DEUX JUGES sur la MEME politique : %+.1f point" % (p_r - p_b))
print("  -> %s" % ("les juges CONCORDENT : l ecart 49,6 / 39,3 est la LOTERIE D ENTRAINEMENT, classee"
                   if abs(p_r - p_b) < 4.0 else
                   "⚠️ LES JUGES DIVERGENT sur la meme politique : le banc a un probleme de JUGE"))
print()
