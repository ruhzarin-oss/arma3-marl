"""
P3 -- LA POLITIQUE QUI CHOISIT SON ENTREE.

Revendication : la politique breche le mur AVEUGLE, pas celui qui est couvert.

Le monde est celui de P1/P2 -- meme fichier, meme empreinte, meme LOS 3D.
A chaque episode les defenseurs changent de place. Une politique qui
memoriserait "toujours l'entree n.3" ne peut donc pas gagner.

L'agent ne voit QUE les defenseurs qu'il a pu detecter depuis son point
d'approche. L'oracle, lui, les voit tous : il donne le plafond. Si l'oracle
ne bat pas le hasard, ce n'est pas la politique qu'on mesure, c'est un banc
casse -- et on le dit avant de regarder quoi que ce soit d'autre.
"""
import json
import math
import sys

import torch

sys.path.insert(0, "/home/younes/arma3-marl/p2")
import monde
import los_boites

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
torch.manual_seed(0)

B = 512          # episodes par lot
N_DEF = 8        # une escouade qui TIENT le batiment : 3 hommes pour six
                 # pieces ne couvrent rien, et la tache perd sa tension.
Z_TORSE = 1.50
ITER = 400


# ------------------------------------------------------------------ monde
def charger():
    b = json.load(open("batiment.json"))
    m = monde.charger_pour_gymnase("batiment.json")
    return b, m


def dans_polygone(pts, poly):
    """pts (M,2) -> booleen (M,). Lancer de rayon, vectorise."""
    x, y = pts[:, 0], pts[:, 1]
    dedans = torch.zeros(pts.shape[0], dtype=torch.bool, device=pts.device)
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cond = ((y0 > y) != (y1 > y))
        xint = (x1 - x0) * (y - y0) / (y1 - y0 + 1e-12) + x0
        dedans ^= cond & (x < xint)
    return dedans


def points_interieurs(poly, n, dev, marge=1.0):
    """Tirage par rejet a l'interieur de l'emprise, en s'ecartant des murs."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    out = []
    while sum(o.shape[0] for o in out) < n:
        c = torch.rand(n * 4, 2, device=dev)
        c[:, 0] = c[:, 0] * (max(xs) - min(xs)) + min(xs)
        c[:, 1] = c[:, 1] * (max(ys) - min(ys)) + min(ys)
        ok = dans_polygone(c, poly)
        # on s'ecarte des bords : le point doit rester dedans en reculant
        for dx, dy in ((marge, 0), (-marge, 0), (0, marge), (0, -marge)):
            d = c.clone()
            d[:, 0] += dx
            d[:, 1] += dy
            ok &= dans_polygone(d, poly)
        out.append(c[ok])
    return torch.cat(out)[:n]


RECULS = (1.2, 2.0, 3.0, 4.0)


def entrees_candidates(b, poly, dev, par_arete=2):
    """Les entrees possibles : des points juste A L'INTERIEUR de chaque mur.

    La porte declaree en fait partie -- c'est le bras "on entre par ou c'est
    prevu", celui que les defenseurs peuvent couvrir.
    """
    pts, etiq = [], []
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        if L < 3.0:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy, ux                    # rentrant (polygone en sens trigo)
        for k in range(par_arete):
            s = L * (k + 1) / (par_arete + 1)
            for r in RECULS:
                pts.append((x0 + ux * s + nx * r, y0 + uy * s + ny * r, Z_TORSE))
                etiq.append("breche_a%d_%d" % (i, k))
    for o in b["ouvertures"]:
        if o["type"] == "porte":
            cx, cy, _ = o["centre_m"]
            nx, ny, _ = o["normale"]
            for r in RECULS:
                pts.append((cx - nx * r, cy - ny * r, Z_TORSE))
                etiq.append("porte")
    return torch.tensor(pts, dtype=torch.float32, device=dev), etiq


# ------------------------------------------------------------------ episode
class Monde:
    def __init__(self):
        b, m = charger()
        self.b, self.boites = b, m["boites"]
        self.empreinte = m["empreinte"]
        self.poly = [tuple(p) for p in b["emprise_m"]]
        e0, t0 = entrees_candidates(b, self.poly, DEV)
        libre = self.en_espace_libre(e0).tolist()
        garde, vus, self.rejetees = [], set(), []
        for i, (t, ok) in enumerate(zip(t0, libre)):
            if t in vus:
                continue
            if ok:
                garde.append(i)
                vus.add(t)
        for t in dict.fromkeys(t0):
            if t not in vus:
                self.rejetees.append(t)
        self.entrees = e0[torch.tensor(garde, device=DEV)]
        self.etiq = [t0[i] for i in garde]
        self.K = self.entrees.shape[0]
        xs = [p[0] for p in self.poly]
        ys = [p[1] for p in self.poly]
        self.rayon = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.5 + 12.0

    def los(self, A, C):
        return los_boites.vue_degagee(self.boites, A, C, dev=DEV)

    def en_espace_libre(self, pts, d=0.5):
        """Un point ENTERRE dans un mur lit comme "personne ne le voit" --
        parfaitement sur, alors qu'il est simplement inatteignable. On exige
        qu'au moins une direction sorte librement sur 50 cm."""
        libre = torch.zeros(pts.shape[0], dtype=torch.bool, device=DEV)
        for dx, dy, dz in ((d, 0, 0), (-d, 0, 0), (0, d, 0),
                           (0, -d, 0), (0, 0, d), (0, 0, -d)):
            q = pts.clone()
            q[:, 0] += dx
            q[:, 1] += dy
            q[:, 2] += dz
            libre |= self.los(pts, q)
        return libre

    def poster(self, n, essais=12):
        """Des defenseurs POSTES : on RECULE depuis l'entree qu'ils tiennent.

        Esperer qu'un tirage uniforme tombe dans le bon local ne marche pas :
        une cloison derriere la porte suffit a former un sas ou aucun point
        n'est jamais tire, et cette entree devient eternellement sure --
        un artefact, pas une tactique.
        """
        cible = torch.randint(0, self.K, (n, N_DEF), device=DEV)
        e = self.entrees[cible.reshape(-1)]                    # (n*D,3)
        M = n * N_DEF
        pos = e.clone()
        pris = torch.zeros(M, dtype=torch.bool, device=DEV)
        for _ in range(essais):
            a = torch.rand(M, device=DEV) * 2 * math.pi
            d = 2.0 + torch.rand(M, device=DEV) * 6.0          # 2 a 8 m en retrait
            c = e.clone()
            c[:, 0] += torch.cos(a) * d
            c[:, 1] += torch.sin(a) * d
            dedans = dans_polygone(c[:, :2], self.poly)
            voit = self.los(c, e) & dedans
            neuf_ = voit & ~pris
            pos = torch.where(neuf_[:, None], c, pos)
            pris |= neuf_
            if pris.all():
                break
        # faute de poste valable, l'homme se tient sur l'entree meme
        return pos.reshape(n, N_DEF, 3), pris.float().mean().item()

    def tirer(self, n, sans_defenseurs=False):
        """Un lot d'episodes. Renvoie tout ce qu'il faut pour juger."""
        defs, self.taux_poste = self.poster(n)

        ang = torch.rand(n, device=DEV) * 2 * math.pi
        appro = torch.stack([self.rayon * torch.cos(ang),
                             self.rayon * torch.sin(ang),
                             torch.full((n,), Z_TORSE, device=DEV)], -1)

        # danger[n,K] : combien de defenseurs VOIENT chaque entree
        e = self.entrees[None, :, :].expand(n, self.K, 3).reshape(-1, 3)
        d_rep = defs[:, :, None, :].expand(n, N_DEF, self.K, 3)
        vu = torch.zeros(n, N_DEF, self.K, device=DEV)
        for j in range(N_DEF):
            vu[:, j, :] = self.los(d_rep[:, j].reshape(-1, 3), e).reshape(n, self.K).float()
        if sans_defenseurs:
            vu = torch.zeros_like(vu)
        danger = vu.sum(1)

        # detecte[n,D] : l'agent voit-il ce defenseur depuis son approche ?
        a_rep = appro[:, None, :].expand(n, N_DEF, 3).reshape(-1, 3)
        detecte = self.los(a_rep, defs.reshape(-1, 3)).reshape(n, N_DEF).float()
        if sans_defenseurs:
            detecte = torch.zeros_like(detecte)

        # ce que l'agent SAIT : la couverture due aux seuls defenseurs vus
        danger_su = (vu * detecte[:, :, None]).sum(1)
        dist = torch.linalg.norm(self.entrees[None, :, :2] - appro[:, None, :2], dim=-1)
        obs = torch.stack([danger_su / N_DEF, dist / (2 * self.rayon)], -1)  # (n,K,2)
        return obs, danger, danger_su, detecte


# ------------------------------------------------------------------ politique
class Politique(torch.nn.Module):
    def __init__(self, n_feat=2, h=32):
        super().__init__()
        self.f = torch.nn.Sequential(
            torch.nn.Linear(n_feat, h), torch.nn.Tanh(),
            torch.nn.Linear(h, h), torch.nn.Tanh(),
            torch.nn.Linear(h, 1))

    def forward(self, obs):
        return self.f(obs).squeeze(-1)          # un logit par entree


def entrainer(w, iters=ITER):
    pi = Politique().to(DEV)
    opt = torch.optim.Adam(pi.parameters(), lr=3e-3)
    ligne = torch.zeros((), device=DEV)
    for it in range(iters):
        obs, danger, _, _ = w.tirer(B)
        logits = pi(obs)
        dist = torch.distributions.Categorical(logits=logits)
        a = dist.sample()
        r = -danger.gather(1, a[:, None]).squeeze(1)        # 0 = personne ne te voit
        ligne = 0.9 * ligne + 0.1 * r.mean()
        perte = -(dist.log_prob(a) * (r - ligne)).mean() - 0.01 * dist.entropy().mean()
        opt.zero_grad()
        perte.backward()
        opt.step()
        if (it + 1) % 100 == 0:
            print("P3   iter %3d  recompense %.3f" % (it + 1, r.mean().item()))
    return pi


@torch.no_grad()
def juger(w, pi, n=4096, sans_defenseurs=False):
    obs, danger, _, _ = w.tirer(n, sans_defenseurs)
    a_pi = pi(obs).argmax(1)
    a_or = danger.argmin(1)                                  # oracle : tout voir
    a_ha = torch.randint(0, w.K, (n,), device=DEV)
    a_po = None
    if "porte" in w.etiq:
        a_po = torch.full((n,), w.etiq.index("porte"), device=DEV)

    def moy(a):
        return danger.gather(1, a[:, None]).mean().item()

    part_aveugle = (danger.gather(1, a_pi[:, None]).squeeze(1) == 0).float().mean().item()
    choix = torch.bincount(a_pi, minlength=w.K).float() / n
    return {
        "politique": moy(a_pi), "oracle": moy(a_or),
        "hasard": moy(a_ha),
        "porte": (moy(a_po) if a_po is not None else float("nan")),
        "part_entrees_aveugles": part_aveugle,
        "repartition": choix.cpu().tolist(),
    }


def main():
    w = Monde()
    print("P3 empreinte monde : %s" % w.empreinte)
    print("P3 entrees retenues : %d  %s" % (w.K, w.etiq))
    print("P3 entrees REJETEES (enterrees dans du solide) : %d  %s"
          % (len(w.rejetees), w.rejetees))
    if "porte" not in w.etiq:
        print("   NOTE: la PORTE elle-meme etait enterree -- c'etait bien un")
        print("         artefact de geometrie, pas une entree sure.")
    w.tirer(256)
    print("P3 defenseurs effectivement postes : %.1f %%" % (100 * w.taux_poste))
    _o, _d, _, _ = w.tirer(2048)
    print("P3 couverture : %.1f %% des entrees sont vues par au moins un homme"
          % (100 * (_d > 0).float().mean().item()))

    # --- controle du BANC avant tout : l'oracle doit battre le hasard ---
    pi0 = Politique().to(DEV)
    av = juger(w, pi0, n=4096)
    print("P3 avant entrainement : oracle %.3f | hasard %.3f | porte %.3f"
          % (av["oracle"], av["hasard"], av["porte"]))
    banc_ok = av["oracle"] < av["hasard"] - 0.05
    if not banc_ok:
        print("   CAUSE: l'information parfaite ne bat pas le hasard.")
        print("   Le banc ne peut RIEN mesurer. On s'arrete ici.")
        print("P3_VERDICT=TOMBE (banc invalide)")
        return

    pi = entrainer(w)
    ap = juger(w, pi, n=8192)
    sans = juger(w, pi, n=4096, sans_defenseurs=True)

    print("-" * 68)
    print("P3 danger moyen (0 = personne ne te voit entrer)")
    for k in ("oracle", "politique", "hasard", "porte"):
        print("     %-10s %.3f" % (k, ap[k]))
    print("P3 part d'entrees totalement aveugles : %.1f %%"
          % (100 * ap["part_entrees_aveugles"]))
    print("P3 repartition des choix : %s"
          % [round(v, 3) for v in ap["repartition"]])
    print("P3 sans defenseurs, danger politique = %.3f (doit etre 0)" % sans["politique"])

    gain = (ap["hasard"] - ap["politique"]) / max(ap["hasard"] - ap["oracle"], 1e-6)
    tests = [
        ("BANC 0  l'oracle bat le hasard                (ctrl banc)", banc_ok),
        ("P3   1  la politique bat le hasard",
         ap["politique"] < ap["hasard"] - 0.05),
        ("P3   2  la politique bat l'entree par la porte",
         (ap["porte"] != ap["porte"]) or ap["politique"] < ap["porte"] - 0.05),
        ("P3   3  elle ne memorise pas une entree unique (max < 60 %%)",
         max(ap["repartition"]) < 0.60),
        ("P3   4  sans defenseurs le danger est nul     (ctrl -)",
         sans["politique"] < 1e-6),
    ]
    ok = True
    for nom, passe in tests:
        print("   [%s]  %s" % ("OK   " if passe else "ECHEC", nom))
        ok = ok and passe
    print("P3 part du gain de l'oracle capturee : %.1f %%" % (100 * gain))
    print("P3_VERDICT=%s" % ("PASSE" if ok else "TOMBE"))


main()
