#!/usr/bin/env python3
"""lire_carte — CARTE TYPEE PAR EFFET + LECTEUR SPATIAL.

Criteres figes AVANT le run : leviathan/CRITERES_CARTE_TYPEE.md

Cinq canaux K x K autour de chaque agent, types par ce qu ils FONT :
  1 bloque le MOUVEMENT        hauteur du bati plein
  2 bloque le TIR et la VUE    bati plein + bas couvert (un muret arrete la balle, pas l homme)
  3 ennemi CONNU ou SOUPCONNE  FogCarte.threat : croyance qui VIEILLIT, jamais la verite terrain
  4 PRIX du danger             probabilite d etre touche dans cette cellule (LOS + arc compris)
  5 l OBJECTIF                 proximite de l objectif

Et le bras de controle qui tranche la question ouverte : les DEUX bras recoivent
EXACTEMENT le meme tenseur. Seul le reseau change.
  DENSE  la carte aplatie entre dans le perceptron actuel
  CONV   le meme vecteur, re-plie en (5, K, K) et lu par un convolutif
Si le dense suit, l architecture n etait pas le levier.

Usage : python lire_carte.py --graines 3 --rounds 150
"""
import sys
import os
import json
import math
import time
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
import torch
import torch.nn as nn
import terrain_gpu as TG
from assault_terrain import AssaultTerrain
from carte import FogCarte
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters

LEV = "/home/younes/arma3-marl/leviathan"
COURBE = LEV + "/courbe_toucher_juge.json"
SEC, TIR, DEG = 3.28, 1.15, 0.233          # conversions mesurees sur Arma le 26/07

ap = argparse.ArgumentParser()
ap.add_argument("--graines", type=int, default=3)
ap.add_argument("--rounds", type=int, default=150)
ap.add_argument("--K", type=int, default=8)
ap.add_argument("--ne", type=int, default=1024)
ap.add_argument("--eval", type=int, default=300)
ap.add_argument("--kc", type=int, default=9, help="cote de la carte (cellules)")
ap.add_argument("--empan", type=float, default=90.0, help="cote de la carte (metres)")
ap.add_argument("--device", default="cuda:0")   # cuda:0 = la 3090
ap.add_argument("--out", default="lire_carte.json")
ap.add_argument("--bras", default="tous", choices=["tous", "dense", "conv"],
                help="ne traiter qu un bras (pour lancer les cases en parallele)")
ap.add_argument("--graine", type=int, default=-1,
                help="ne traiter qu une graine ; -1 = toutes")
ap.add_argument("--sans_repere", action="store_true",
                help="sauter la contre-epreuve scriptee (faite une seule fois a part)")
a = ap.parse_args()
DEV = a.device
KC = a.kc
NCH = 5


# ---------------------------------------------------------------- la carte typee
class MondeCarte(AssaultTerrain):
    """Le banc fige, plus cinq canaux types par EFFET, aplatis a la fin de l observation.

    Rien n est retire : l observation existante est intacte, la carte s ajoute. Les deux
    bras lisent le MEME tenseur — c est ce qui permet d isoler l architecture.
    """

    def __init__(self, *args, **kw):
        self.kc = kw.pop("kc", 9)
        self.empan = kw.pop("empan", 90.0)
        super().__init__(*args, **kw)
        self.fog = FogCarte(self.N, self.scale, self.dev, G=28)
        self.obs_dim = self.obs_dim + NCH * self.kc * self.kc

    def reset(self, *args, **kw):
        o = super().reset(*args, **kw)
        self.fog.reset()
        return o

    def step(self, acts, auto_reset=True):
        self.fog.update(self)                       # la croyance se met a jour AVANT d etre lue
        return super().step(acts, auto_reset=auto_reset)

    def _cellules(self):
        """Les centres des K x K cellules autour de chaque agent, en coordonnees monde."""
        K, span, d, N, A = self.kc, self.empan, self.dev, self.N, self.A
        off = (torch.arange(K, device=d).float() / (K - 1) - 0.5) * span
        gx = (self.apx[..., None, None] + off[None, None, :, None]).expand(N, A, K, K)
        gy = (self.apy[..., None, None] + off[None, None, None, :]).expand(N, A, K, K)
        return gx.reshape(N, A * K * K), gy.reshape(N, A * K * K)

    def _carte_typee(self):
        N, A, K, S = self.N, self.A, self.kc, self.scale
        gx, gy = self._cellules()
        M = A * K * K

        # Les champs disponibles dependent du monde : le replica a `_solidhR`/`_lowhR`
        # (hauteurs de bati), le terrain procedural n'a que hm / cover / slope. On type
        # donc par EFFET a partir de ce qui EXISTE, sans inventer de champ.
        # --- 1 : BLOQUE LE MOUVEMENT : la pente (+ le bati plein s il y en a un)
        c1 = (TG.sample(self.slope, gx, gy, S) / 5.0).clamp(0.0, 1.0)
        if getattr(self, "_solidhR", None) is not None:
            c1 = torch.maximum(c1, (self._sample_field(self._solidhR, gx, gy) / 6.0).clamp(0.0, 1.0))
        # --- 2 : BLOQUE LE TIR ET LA VUE : le couvert, et tout relief qui depasse mon oeil.
        # Un muret arrete la balle sans arreter l homme -> ce canal n est pas le canal 1.
        c2 = TG.sample(self.cover, gx, gy, S).clamp(0.0, 1.0)
        hcell = TG.sample(self.hm, gx, gy, S)
        hmoi = TG.sample(self.hm, self.apx, self.apy, S)
        hmoi = hmoi.unsqueeze(-1).expand(N, A, K * K).reshape(N, M)
        c2 = torch.maximum(c2, ((hcell - hmoi) / 3.0).clamp(0.0, 1.0))
        if getattr(self, "_lowhR", None) is not None:
            c2 = torch.maximum(c2, (self._sample_field(self._lowhR, gx, gy) / 2.0).clamp(0.0, 1.0))
        # --- 3 : ENNEMI CONNU OU SOUPCONNE (croyance qui vieillit, PAS la verite)
        c3 = TG.sample(self.fog.threat, gx, gy, S).clamp(0.0, 1.0)
        # --- 4 : PRIX DU DANGER dans cette cellule
        c4 = self._prix(gx, gy).clamp(0.0, 1.0)
        # --- 5 : L OBJECTIF (il est en (0,0))
        c5 = (1.0 - (torch.sqrt(gx * gx + gy * gy) / S)).clamp(0.0, 1.0)

        m = torch.stack([c1, c2, c3, c4, c5], dim=1)          # (N, 5, A*K*K)
        m = m.view(N, NCH, A, K * K).permute(0, 2, 1, 3)       # (N, A, 5, K*K)
        return m.reshape(N, A, NCH * K * K)

    def _prix(self, gx, gy):
        """Ce que couterait d etre LA : somme, sur les defenseurs vivants, de la probabilite
        de toucher a cette distance, filtree par la ligne de vue et par l arc de tir.
        C est un PRIX, pas une consigne : le moins cher est toujours de fuir."""
        N, D, S = self.N, self.D, self.scale
        M = gx.shape[1]
        prix = torch.zeros(N, M, device=self.dev)
        eye = self._eye()
        if torch.is_tensor(eye):
            eye_c = eye.mean(1, keepdim=True).expand(N, M)
        else:
            eye_c = eye
        for di in range(D):
            bx = self.dpx[:, di:di + 1].expand(N, M)
            by = self.dpy[:, di:di + 1].expand(N, M)
            vivant = self._dalive()[:, di:di + 1].float().expand(N, M)
            los = self._losc(self.hm, gx, gy, bx, by, S, eye_a=eye_c, eye_b=1.7)
            dist = torch.sqrt((gx - bx) ** 2 + (gy - by) ** 2)
            act = vivant.clone()
            if self.def_line and hasattr(self, "dface"):
                ang = torch.atan2(gx - bx, gy - by)
                adf = torch.atan2(torch.sin(ang - self.dface[:, di:di + 1]),
                                  torch.cos(ang - self.dface[:, di:di + 1]))
                act = act * (adf.abs() <= self._dfarc).float()
            if self.courbe is not None:
                p = self._p_balle(dist) * self.tir_par_pas * self.degat_par_impact
            else:
                p = self.hit * (dist < self.fire_range).float()
            prix = prix + act * los * p
        return prix

    def _obs(self):
        return torch.cat([super()._obs(), self._carte_typee()], dim=2)


def monde(seed, ne):
    return MondeCarte(num_envs=ne, A=4, D=8, seed=seed, device=DEV, max_steps=60,
                      postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                      def_rand=True, secure_task=True, secure_only=True,
                      courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                      degat_par_impact=DEG, arc_obs=True, champ_risque=False,
                      kc=KC, empan=a.empan)


# ---------------------------------------------------------------- les deux lecteurs
class NetCarte(nn.Module):
    """MEME entree que le dense. La difference est ici : les 5*K*K derniers nombres sont
    RE-PLIES en (5, K, K) et lus par un convolutif au lieu d etre vus comme un sac plat."""

    def __init__(self, O, nact, kc, hidden=512, layers=3, emb=128):
        super().__init__()
        self.kc = kc
        self.nmap = NCH * kc * kc
        self.obase = O - self.nmap
        self.conv = nn.Sequential(
            nn.Conv2d(NCH, 32, 3, padding=1), nn.ReLU(),
            nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(3), nn.Flatten(), nn.Linear(32 * 9, emb), nn.ReLU())
        body = []
        din = self.obase + emb
        for _ in range(layers):
            body += [nn.Linear(din, hidden), nn.ReLU()]
            din = hidden
        self.body = nn.Sequential(*body)
        self.pi = nn.Linear(hidden, nact)
        self.v = nn.Linear(hidden, 1)

    def _h(self, obs):
        sh = obs.shape[:-1]
        base = obs[..., :self.obase]
        mp = obs[..., self.obase:].reshape(-1, NCH, self.kc, self.kc)
        e = self.conv(mp).reshape(*sh, -1)
        return self.body(torch.cat([base, e], dim=-1))

    def a_logits(self, obs):
        return self.pi(self._h(obs))

    def value(self, obs):
        return self.v(self._h(obs)).squeeze(-1).mean(-1)


# ---------------------------------------------------------------- mesure
def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def part_angle_mort(e):
    if not hasattr(e, "dface"):
        return torch.zeros(e.N, device=DEV)
    ex = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2)
    ey = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    ed2 = torch.where(e._dalive().unsqueeze(1), ex * ex + ey * ey, BIG)
    km = ed2.argmin(2)
    bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km)
    df = torch.gather(e.dface, 1, km)
    az = torch.atan2(e.apx - bx, e.apy - by)
    rel = torch.atan2(torch.sin(az - df), torch.cos(az - df)).abs()
    dehors = (rel > e._dfarc).float() * e._aalive().float()
    return dehors.sum(1) / e._aalive().float().sum(1).clamp(min=1)


def evalue(net, seed, doctrine=None):
    e = monde(seed, a.eval)
    obs = e.reset(); N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=DEV)
    fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV); expo = torch.zeros(N, device=DEV)
    mort_cum = torch.zeros(N, device=DEV); nsteps = torch.zeros(N, device=DEV)
    frais = torch.zeros((), device=DEV); nfr = 0
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    lat_tot = torch.zeros((), device=DEV); lat_dist = torch.zeros((), device=DEV)
    for t in range(60):
        if doctrine == "frontal":
            act = cap(-e.apx, -e.apy)
        elif doctrine == "flanc":
            act = cap(-e.apx, -e.apy)
            d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
            fixe = torch.zeros(N, e.A, dtype=torch.bool, device=DEV); fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        else:
            with torch.no_grad():
                act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
        vivant = ~fini
        mort_cum = mort_cum + part_angle_mort(e) * vivant.float()
        nsteps = nsteps + vivant.float()
        # SENTINELLE d honnetete du canal 3 : on veut le PIC de croyance, pas la moyenne
        # sur 784 cellules (qui serait quasi nulle meme avec une carte parfaite).
        # Si ce pic reste a zero, le canal ennemi est MORT et l experience ne vaut rien.
        frais = frais + e.fog.threat.amax(dim=(1, 2)).mean(); nfr += 1
        _ax, _ay = e.apx.clone(), e.apy.clone()
        _dav = torch.sqrt(_ax ** 2 + _ay ** 2)
        obs, _, done, info = e.step(act, auto_reset=False)
        _ux = -_ax / _dav.clamp(min=1e-6); _uy = -_ay / _dav.clamp(min=1e-6)
        _lat = ((e.apx - _ax) * (-_uy) + (e.apy - _ay) * _ux).abs()
        _m = vivant.unsqueeze(1).float() * e._aalive().float()
        lat_tot = lat_tot + (_lat * _m).sum()
        lat_dist = lat_dist + (_lat * _dav * _m).sum()
        pris = pris | (info["took"] & vivant)
        pertes = torch.where(vivant, info["losses"].float(), pertes)
        expo = expo + info["exposed"] * vivant.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vivant, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)
    pr = float(pris.float().mean())
    pp = float(pertes[pris].mean()) if bool(pris.any()) else float("nan")
    return {"prise": pr, "pertes_par_prise": pp,
            "prise_a_pertes": (pr / pp) if (pp == pp and pp > 0) else float("nan"),
            "expo_par_metre": float((expo / gagne).mean()),
            "part_angle_mort": float((mort_cum / nsteps.clamp(min=1)).mean()),
            "pic_croyance_canal3": float(frais / max(nfr, 1)),
            "distance_du_detour": float(lat_dist / lat_tot.clamp(min=1e-6))}


def apprend(archi, seed, etiquette):
    e = monde(seed, a.ne)
    obs = e.reset(); O = obs.shape[-1]
    net = (NetCarte(O, e.n_actions, KC) if archi == "conv" else Net(O, e.n_actions)).to(DEV)
    npar = sum(p.numel() for p in net.parameters())
    print("    [%s g%d] O=%d  parametres=%.2f M" % (etiquette, seed, O, npar / 1e6), flush=True)
    opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    piste = []
    for r in range(1, a.rounds + 1):
        obs = ppo_iters(net, opt, e, obs, a.K, O)
        if r % 30 == 0 or r == a.rounds:
            m = evalue(net, seed + 1000)
            m["ronde"] = r
            piste.append(m)
            print("    [%s g%d] ronde %3d/%d : prise %5.1f%%  pertes/pr %.2f  PRISE-A-PERTES %5.2f  pic croyance %.3f"
                  % (etiquette, seed, r, a.rounds, 100 * m["prise"], m["pertes_par_prise"],
                     m["prise_a_pertes"], m["pic_croyance_canal3"]), flush=True)
            torch.save(net.state_dict(), "%s/carte_%s_g%d.pt" % (LEV, etiquette, seed))
    return piste


if __name__ == "__main__":
    if not os.path.exists(LEV + "/CRITERES_CARTE_TYPEE.md"):
        print("!! les criteres ne sont pas figes — ARRET.")
        sys.exit(2)
    t0 = time.time()
    print("=== CARTE TYPEE PAR EFFET + LECTEUR SPATIAL ===", flush=True)
    print("    banc fige A=4 D=8 | carte %dx%d sur %.0f m | 2 bras x %d graines x %d rondes"
          % (KC, KC, a.empan, a.graines, a.rounds), flush=True)
    res = {"reperes": {}, "bras": {"dense": [], "conv": []}}

    # CONTRE-EPREUVE : les doctrines scriptees doivent reproduire le banc fige.
    # En parallele on la fait UNE fois a part, pas six fois — elle ne depend pas du bras.
    for doc in (() if a.sans_repere else ("frontal", "flanc")):
        res["reperes"][doc] = evalue(None, 7, doctrine=doc)
        r = res["reperes"][doc]
        print("  repere scripte %-8s : prise %5.1f%%  pertes/pr %.2f  prise-a-pertes %5.2f"
              % (doc, 100 * r["prise"], r["pertes_par_prise"], r["prise_a_pertes"]), flush=True)
    if a.sans_repere:
        ok = True
        print("  (contre-epreuve sautee : faite a part)", flush=True)
    else:
        ef = res["reperes"]["frontal"]["prise"]; ec = res["reperes"]["flanc"]["prise"]
        ok = abs(ef - 0.193) <= 0.08 and abs(ec - 0.747) <= 0.08
        print("  CONTRE-EPREUVE (frontal 19,3 %% / crochet 74,7 %% a +-8 pts) : %s"
              % ("OK" if ok else "ECHEC — ON NE CONCLUT RIEN"), flush=True)
    json.dump(res, open(LEV + "/" + a.out, "w"), indent=1)
    if not ok:
        print("  l env a bouge : le run continue pour l information, le verdict est NUL.", flush=True)

    _bras = ("dense", "conv") if a.bras == "tous" else (a.bras,)
    for archi in _bras:
        print("", flush=True)
        print("  --- bras %s ---" % archi.upper(), flush=True)
        _graines = [a.graine] if a.graine >= 0 else [7 + g for g in range(a.graines)]
        for seed in _graines:
            try:
                piste = apprend(archi, seed, archi)
                res["bras"][archi].append({"graine": seed, "piste": piste,
                                           "fin": piste[-1] if piste else None})
            except Exception as x:
                print("    (graine %d echouee : %s)" % (seed, str(x)[:160]), flush=True)
            json.dump(res, open(LEV + "/" + a.out, "w"), indent=1)

    def moy(nom, cle):
        v = [b["fin"][cle] for b in res["bras"][nom] if b.get("fin") and b["fin"][cle] == b["fin"][cle]]
        return sum(v) / len(v) if v else float("nan")

    print("", flush=True)
    print("=== RESULTAT (moyenne des graines, fin d entrainement) ===", flush=True)
    print("  %-8s %9s %11s %15s %12s %11s" % ("bras", "prise", "pertes/pr", "PRISE-A-PERTES", "expo/m", "pic croyance"), flush=True)
    for n in ("dense", "conv"):
        print("  %-8s %8.1f%% %11.2f %15.2f %12.4f %11.3f"
              % (n, 100 * moy(n, "prise"), moy(n, "pertes_par_prise"), moy(n, "prise_a_pertes"),
                 moy(n, "expo_par_metre"), moy(n, "pic_croyance_canal3")), flush=True)
    pd = moy("dense", "prise_a_pertes"); pc = moy("conv", "prise_a_pertes")
    print("", flush=True)
    print("=== VERDICT (seuils figes CRITERES_CARTE_TYPEE) ===", flush=True)
    if pd == pd and pc == pc and pd > 0:
        ecart = (pc - pd) / pd
        print("  conv vs dense : %+.1f %% de prise-a-pertes" % (100 * ecart), flush=True)
        if ecart >= 0.15:
            print("  -> L ARCHITECTURE EST LE LEVIER : lire la carte en 2D paie.", flush=True)
        elif abs(ecart) < 0.08:
            print("  -> L ARCHITECTURE N EST PAS LE LEVIER : le dense suit. Piste fermee.", flush=True)
        else:
            print("  -> ZONE GRISE (entre 8 et 15 %) : non concluant, il faut plus de graines.", flush=True)
    else:
        print("  pas de prise-a-pertes exploitable dans un des bras.", flush=True)
    res["duree_min"] = (time.time() - t0) / 60.0
    json.dump(res, open(LEV + "/" + a.out, "w"), indent=1)
    print("-> %s/%s   (%.0f min)" % (LEV, a.out, res["duree_min"]), flush=True)
    print("CARTE_DONE", flush=True)
