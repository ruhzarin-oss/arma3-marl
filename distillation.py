#!/usr/bin/env python3
"""distillation — L ELEVE IMITE LE MAITRE-GREFFE.

Criteres deposes AVANT la premiere donnee : DEPOT_DISTILLATION.md (le banc imprime son hachage).

LE PRINCIPE. On a etabli que le coupable est l ATTRIBUTION DU CREDIT : +15,3 points sont
recoltables sans un seul gradient, et zero quand on pose la meme information dans l entree
d un apprenant. Alors on cesse de vouloir les lui faire DECOUVRIR : on les lui fait COPIER.
Le professeur donne une action cible A CHAQUE PAS, en supervise. Il n y a plus rien a crediter.

⚠️ LE PROFESSEUR EST UN DECODEUR, PAS UN AGENT. Il a besoin du prix a l execution. Tout
l objet est de produire un eleve qui n en a plus besoin — c est la porte G3.
"""
import os, sys, json, time, hashlib, argparse
import torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
import banc_raster as BR
from banc_raster import prix_des_actions, jouer_phi2

DEV = "cuda:0"
MAITRE = "/home/younes/arma3-marl/pol_1200_g0.pt"
K_TOP = 3
# ─── LE NOUVEAU MAITRE ⟨depot cee4a563999d5112, 26/08⟩ ────────────────────────────────
# La greffe faisait 61,6 % et exigeait le PRIX a l execution. La doctrine SHAMAL sans
# bounding fait **84,6 %** (etendue [79,3 ; 89,1], six graines) et n exige RIEN.
# Elle gagne en COMBATTANT : 2,68 survivants sur 4 contre 1,34 pour SHAMAL complet.
# Et son desaccord avec la reference sera MASSIF, ce qui est la condition qui manquait a D1
# (signal redondant a 88 % avec le navigateur — mesure du 26/08).
from shamal_teacher import shamal_action
MAITRE_SHAMAL = dict(drop_to=1, retreat=True, mode="assault", bounding=False, flank=True)
# ⭐ LE MAITRE v2 — 91,0 % [89,1 ; 94,1], survivants 3,17 sur 4.
# Mesure du 26/08 : rabattre les POSTURES sur TIRER gagne 6,4 points de plus (84,6 -> 91,0).
# Le controle qui rend ce chiffre lisible : les rabattre sur TENIR donne 0,7 % — ce n est
# donc pas « n importe quel remplacement marche », c est TIRER qui paie et S IMMOBILISER
# qui tue. Motif des trois gestes tombes : TOUT CE QUI FIGE UN HOMME COUTE
# (bond -37,0 · accroupissement -6,4 · tenir -83,9).
# Et il n emet plus QUE les 10 actions de la reference : le biais de vocabulaire disparait.
BRIDER_A_10 = True


class Eleve(nn.Module):
    """Meme squelette que la politique du depot. `avec_prix` ajoute les 8 prix a l entree."""
    def __init__(self, nobs, avec_prix=False, nh=128):
        super().__init__()
        self.avec_prix = avec_prix
        n = nobs + (8 if avec_prix else 0)
        self.f = nn.Sequential(nn.Linear(n, nh), nn.Tanh(), nn.Linear(nh, nh), nn.Tanh())
        self.pi = nn.Linear(nh, B.NA); self.v = nn.Linear(nh, 1)
    def forward(self, o, prix=None):
        x = torch.cat([o, prix], -1) if self.avec_prix else o
        h = self.f(x)
        return self.pi(h), self.v(h).squeeze(-1)


def charger_maitre():
    m = B.Politique(12).to(DEV)
    m.load_state_dict(torch.load(MAITRE, map_location=DEV)); m.eval()
    return m


def cible_shamal(e, hasard=False):
    """L action du NOUVEAU maitre : la doctrine scriptee a 84,6 %.
    `hasard` = LE CONTROLE : on garde la meme forme d ordre mais on tire le cap au hasard
    parmi les huit, en conservant les actions non directionnelles (tenir, tirer, postures).
    Il mesure ce que rapporte le seul fait d IMITER QUELQUE CHOSE DE COHERENT, sans le
    contenu tactique."""
    a = shamal_action(e, **MAITRE_SHAMAL)
    if BRIDER_A_10:
        a = torch.where(a >= 10, torch.full_like(a, 9), a)      # postures -> TIRER
    if not hasard:
        return a
    r = torch.randint(0, 8, a.shape, device=a.device)
    return torch.where(a < 8, r, a)          # les caps deviennent aleatoires, TIRER tient


def cible_du_maitre(maitre, o, e, hasard=False):
    """L action que le PROFESSEUR prendrait. `hasard` = le CONTROLE : on garde le rabattage
    sur le top-3 mais on tire dedans AU HASARD au lieu de prendre la moins chere."""
    with torch.no_grad():
        lo, _ = maitre(o)
        top = lo.topk(K_TOP, dim=-1).indices                       # (N,A,3)
        if hasard:
            j = torch.randint(0, K_TOP, top.shape[:2] + (1,), device=top.device)
            return torch.gather(top, 2, j).squeeze(2), None
        p = prix_des_actions(e)
        p8 = torch.cat([p, p.mean(-1, keepdim=True).expand(p.shape[0], p.shape[1], 2)], -1)
        pt = torch.gather(p8, 2, top)
        return torch.gather(top, 2, pt.argmin(2, keepdim=True)).squeeze(2), p


def distiller(eleve_type, graine, iters=600, n=256, lr=3e-4):
    """DAgger simplifie : l ELEVE conduit (donc la distribution d etats est la SIENNE), le
    MAITRE etiquette. Sans ca on n apprendrait que sur les etats du maitre, et l eleve
    derailerait des le premier ecart — c est la faute classique du clonage naif."""
    avec_prix = (eleve_type in ("D2",))
    hasard = (eleve_type in ("D3", "S3"))
    shamal = eleve_type.startswith("S")          # S = le maitre a 84,6 %, D = l ancienne greffe
    torch.manual_seed(graine)
    maitre = charger_maitre()
    e0 = B.monde(8, B.GRAINES_TRAIN[0]); e0.reset(); nobs = e0._obs().shape[-1]
    el = Eleve(nobs, avec_prix=avec_prix).to(DEV)
    opt = torch.optim.Adam(el.parameters(), lr=lr)
    perte_fn = nn.CrossEntropyLoss()
    print("    eleve %s graine %d — %d entrees%s, cible %s, %d parametres"
          % (eleve_type, graine, nobs, " + 8 prix" if avec_prix else "",
             ("SHAMAL 91,0 %% avec CAP AU HASARD (CONTROLE)" if hasard else "SHAMAL 91,0 %%") if shamal
             else ("AU HASARD dans le top-3 (CONTROLE)" if hasard else "la moins chere"),
             sum(p.numel() for p in el.parameters())), flush=True)
    for it in range(iters):
        e = B.monde(n, B.GRAINES_TRAIN[it % len(B.GRAINES_TRAIN)])
        o = e.reset(); pertes = []
        opt.zero_grad()
        fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
        for t in range(B.PAS):
            if shamal:
                y = cible_shamal(e, hasard=hasard); prix = None
            else:
                y, prix = cible_du_maitre(maitre, o, e, hasard=hasard)
            if prix is None and avec_prix: prix = prix_des_actions(e)
            lo, _ = el(o, prix if avec_prix else None)
            # ⚠️ NORMALISATION PAR HOMME-PAS VIVANT, pas par environnement. La version
            # precedente divisait par N au lieu de N x A : la perte affichait 9,3 la ou le
            # maximum theorique de 10 classes est ln(10)=2,303, et le gradient etait
            # multiplie par 4 — soit un pas d apprentissage effectif de 1,2e-3 sans que
            # personne ne l ait decide.
            viv = (~fini).float().unsqueeze(1).expand(e.N, e.A)
            ce = nn.functional.cross_entropy(lo.reshape(-1, B.NA), y.reshape(-1),
                                             reduction="none").reshape(e.N, e.A)
            l = (ce * viv).sum() / viv.sum().clamp(min=1) / B.PAS
            l.backward(); pertes.append(float(l) * B.PAS)
            # L ELEVE CONDUIT : on avance avec SON action, pas celle du maitre.
            with torch.no_grad():
                a = torch.distributions.Categorical(logits=lo).sample()
            o, _, done, _ = e.step(a, auto_reset=False)
            fini |= done.bool()
            if bool(fini.all()): break
        nn.utils.clip_grad_norm_(el.parameters(), 1.0)
        opt.step()
        if it % 100 == 0 or it == iters - 1:
            print("      it %4d  perte %.4f" % (it, sum(pertes) / len(pertes)), flush=True)
    return el


def juger(el, avec_prix, graines, n=256):
    pr, tn, dh, sv = [], [], [], []
    for g in graines:
        e = B.monde(n, g)
        def gele(o, t, _e=e):
            with torch.no_grad():
                lo, _ = el(o, prix_des_actions(_e) if avec_prix else None)
            return torch.distributions.Categorical(logits=lo).sample(), None, None
        st, *_ = jouer_phi2(e, gele, w_phi=0.0)
        pr.append(st["prise"]); tn.append(st["metres_tenus"])
        dh.append(st["danger_homme_pas"]); sv.append(st["survivants"])
    m = lambda v: sum(v) / len(v)
    return m(pr), m(tn), m(dh), m(sv), pr


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=600)
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--eleves", nargs="+", default=["D1", "D2", "D3"])
    ap.add_argument("--graines", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--sortie", default="/mnt/data/distillation.json")
    a = ap.parse_args()
    h = hashlib.sha256(open("/home/younes/arma3-marl/DEPOT_DISTILLATION.md", "rb").read()).hexdigest()[:16]
    print("=" * 82); print(" DISTILLATION DU MAITRE-GREFFE — criteres deposes, hachage %s" % h)
    print("=" * 82, flush=True)
    res = json.load(open(a.sortie)) if os.path.exists(a.sortie) else {"hachage": h, "faits": [], "eleves": {}}
    for et in a.eleves:
        for g in a.graines:
            mq = "%s:%d" % (et, g)
            if mq in res["faits"]: print("    -- %s deja fait" % mq, flush=True); continue
            t0 = time.time()
            el = distiller(et, g, iters=a.iters, n=a.n)
            torch.save(el.state_dict(), "/mnt/data/eleve_%s_%d.pt" % (et, g))
            p, t, d, s, par = juger(el, et == "D2", B.GRAINES_TEST, n=a.n)
            res["eleves"].setdefault(et, {"prise": [], "tenus": [], "danger_hp": [], "survivants": []})
            for k, v in (("prise", p), ("tenus", t), ("danger_hp", d), ("survivants", s)):
                res["eleves"][et][k].append(v)
            res["faits"].append(mq)
            print("    == ELEVE %s graine %d : PRISE %5.1f %%  [%.1f ; %.1f]  TENUS %6.1f m  "
                  "DANGER/hp %.4f  SURVIVANTS %.2f  (%.1f min)"
                  % (et, g, p, min(par), max(par), t, d, s, (time.time() - t0) / 60.0), flush=True)
            json.dump(res, open(a.sortie, "w"), indent=1)
    print("\n  ecrit dans %s" % a.sortie)
