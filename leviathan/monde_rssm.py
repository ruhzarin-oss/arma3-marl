#!/usr/bin/env python3
"""monde_rssm.py — le MODELE DU MONDE : un etat latent recurrent qui apprend la dynamique d Arma.

Pourquoi celui-la. Nous avons passe des mois a entrainer dans un bac a sable ecrit a la main. Il
disait 96 % de reussite ou Arma en donne 0 sur 38. On a calibre ses PIECES sans jamais calibrer son
ISSUE. Un modele du monde APPREND la dynamique au lieu qu on la devine : c est la sortie de la
calibration a la pince. Precedent maison : un modele a un pas pilote en MPC a ECHOUE sur le
controle de vol ; le diagnostic etait qu il faut un modele latent RECURRENT et une politique
entrainee dans l imagination. Ce fichier est ce diagnostic mis en oeuvre.

Ce qui est volontairement absent, et pourquoi. Pas d encodeur convolutif : notre observation est une
poignee de nombres, pas des pixels — l essentiel de DreamerV3 ne nous sert a rien. Pas de tete de
recompense sur le corpus hors banc : il n y a pas d objectif la-bas, donc rien a predire ; on y
apprend des EVENEMENTS mesurables (mort, presence) et la recompense de la tache reste definie sur
le banc, recomposee dans l imagination.

Structure, dimensionnee pour 1 a 2 millions de pas de donnees, pas davantage :
  - encodeur PAR ENTITE partage, agrege par SOMME separement sur attaquants et defenseurs. Les
    defenseurs sont interchangeables : autant l encoder que le faire apprendre.
  - GRU deterministe 384 + latent stochastique 16 categorielles x 16 classes
  - tetes MLP 2x256 : decodeur (symlog), mort par entite, continuation, et « pris » (banc seul,
    masque ailleurs)
Environ deux millions de parametres.

Usage :
  monde_rssm.py --corpus banc --pas 20000 --graine 0 --sortie modele_banc_g0.pt
  monde_rssm.py --corpus mixte --pas 20000 --graine 0 --sortie modele_mixte_g0.pt
"""
import argparse, glob, hashlib, json, math, os, random, sys, time

import torch
import torch.nn as nn
import torch.nn.functional as F

A_MAX, D_MAX = 12, 8
F_ATT, F_DEF = 5, 4            # attaquant : x, y, vivant, tire, present | defenseur : x, y, vivant, present
ECHELLE = 100.0                # metres. Echelle LINEAIRE, pas de symlog : voir plus bas.
DIM_CTX = 6                    # 4 doctrines + rapport de force + drapeau hors banc
NUIT0 = '/mnt/data2/lab/replay/nuit0'
OUVERT = '/mnt/data2/lab/replay/openworld'
DOCTRINES = ['frontal', 'supfront', 'envelop', 'reckless']


# PAS DE SYMLOG SUR LES POSITIONS. Mesure du 31/07 : avec symlog, le modele redecrivait a 13 m une
# image qu il avait SOUS LES YEUX. La raison est que symlog est fait pour des grandeurs NON BORNEES
# (les recompenses de DreamerV3) et qu il ECRASE les grandes valeurs : dans une arene de 200 m, une
# erreur d un metre devenait numeriquement invisible face aux drapeaux vivant/mort, qui pesaient
# alors toute la perte. Nos positions sont bornees : l echelle lineaire est la bonne.
# Les deux fonctions restent, en identite, pour ne pas casser les appelants.


POIDS_MORT = 3.08          # mesure : 16,2 % des hommes presents sont morts a un instant donne


def _masque_presence(obs):
    """1 sur les nombres qui decrivent une entite REELLEMENT PRESENTE, 0 sur les places vides.
    Les places vides sont du remplissage, pas une observation : les inclure dilue le gradient et
    apprend au modele a declarer morts des hommes qui n existent pas."""
    B = obs.shape[0]
    a = obs[:, :A_MAX * F_ATT].view(B, A_MAX, F_ATT)
    d = obs[:, A_MAX * F_ATT:].view(B, D_MAX, F_DEF)
    ma = a[..., 4:5].expand(-1, -1, F_ATT).reshape(B, -1)
    md = d[..., 3:4].expand(-1, -1, F_DEF).reshape(B, -1)
    return torch.cat([ma, md], -1)


def symlog(x):
    return x


def symexp(x):
    return x


# ----------------------------------------------------------------------------- donnees
class Corpus:
    """Charge des episodes en sequences de longueur fixe. Le banc et le corpus hors banc entrent
    dans le MEME format : c est ce qui permet de melanger par minibatch."""

    def __init__(self, held_out=None, avec_ouvert=False, longueur=50):
        self.L = longueur
        self.banc, self.ouvert = [], []
        self._charger_banc(held_out)
        if avec_ouvert:
            self._charger_ouvert()

    # --- banc : episodes complets, objectif defini
    def _charger_banc(self, held_out):
        for f in sorted(glob.glob(os.path.join(NUIT0, 'n0_*.json'))):
            try:
                d = json.load(open(f))
            except Exception:
                continue
            m, meta = d.get('metrics', {}), d.get('_meta', {})
            if m.get('east_start') != 8 or m.get('steps', 0) < 5:
                continue
            mode = meta.get('mode')
            if held_out and mode == held_out:
                continue
            fob = d.get('fob')
            fr = d.get('frames', [])
            if not fob or len(fr) < 6:
                continue
            self.banc.append(self._episode_banc(fr, fob, mode, meta.get('A', 8),
                                                bool(m.get('took'))))

    def _episode_banc(self, frames, fob, mode, A, pris):
        fx, fy = fob[0], fob[1]
        T = len(frames)
        obs = torch.zeros(T, A_MAX * F_ATT + D_MAX * F_DEF)
        for t, fr in enumerate(frames):
            v = torch.zeros(A_MAX, F_ATT)
            for i, w in enumerate(fr.get('west', [])[:A_MAX]):
                v[i, 0] = (w[0] - fx) / ECHELLE
                v[i, 1] = (w[1] - fy) / ECHELLE
                v[i, 2] = float(w[2]) if len(w) > 2 else 1.0
                v[i, 3] = float((fr.get('firew') or [0] * A_MAX)[i]) if i < len(fr.get('firew') or []) else 0.0
                v[i, 4] = 1.0
            u = torch.zeros(D_MAX, F_DEF)
            for i, e in enumerate(fr.get('east', [])[:D_MAX]):
                u[i, 0] = (e[0] - fx) / ECHELLE
                u[i, 1] = (e[1] - fy) / ECHELLE
                u[i, 2] = float(e[2]) if len(e) > 2 else 1.0
                u[i, 3] = 1.0
            obs[t] = torch.cat([v.reshape(-1), u.reshape(-1)])
        ctx = torch.zeros(DIM_CTX)
        if mode in DOCTRINES:
            ctx[DOCTRINES.index(mode)] = 1.0
        ctx[4] = A / 12.0
        ctx[5] = 0.0                                     # 0 = banc
        return {'obs': obs, 'ctx': ctx, 'pris': float(pris), 'a_pris': 1.0}

    # --- corpus hors banc : flux continu, pas d objectif
    def _charger_ouvert(self):
        for st in sorted(glob.glob(os.path.join(OUVERT, 'inst*', '*', 'state.jsonl'))):
            ticks = []
            for l in open(st):
                try:
                    ticks.append(json.loads(l))
                except Exception:
                    pass
            if len(ticks) < self.L + 5:
                continue
            self.ouvert.extend(self._decouper_ouvert(ticks))

    def _decouper_ouvert(self, ticks, pas=40):
        """Fenetres a ensemble d entites CONSTANT. Une apparition ou une disparition COUPE : ce qui
        suit n est plus la meme scene. Une MORT ne coupe pas — c est la transition a apprendre."""
        out = []
        i = 0
        while i + self.L <= len(ticks):
            fen = ticks[i:i + self.L]
            ids0 = {e[0] for e in fen[0]['ents']}
            ok = all({e[0] for e in x['ents']} == ids0 for x in fen)
            if ok and len(ids0) >= 4:
                out.append(self._episode_ouvert(fen))
                i += pas
            else:
                i += 5
        return out

    def _episode_ouvert(self, fen):
        # centre la scene sur le barycentre initial : la position absolue sur la carte n a pas de
        # sens pour la dynamique, seule la geometrie relative en a.
        p0 = fen[0]['ents']
        cx = sum(e[1] for e in p0) / len(p0)
        cy = sum(e[2] for e in p0) / len(p0)
        T = len(fen)
        obs = torch.zeros(T, A_MAX * F_ATT + D_MAX * F_DEF)
        # camp 1 (WEST) -> emplacement attaquant, camp 0 (EAST) -> emplacement defenseur
        for t, x in enumerate(fen):
            v = torch.zeros(A_MAX, F_ATT)
            u = torch.zeros(D_MAX, F_DEF)
            iw = ie = 0
            for e in x['ents']:
                if e[5] == 1 and iw < A_MAX:
                    v[iw] = torch.tensor([(e[1] - cx) / ECHELLE, (e[2] - cy) / ECHELLE,
                                          float(e[4]), float(e[6]), 1.0])
                    iw += 1
                elif e[5] == 0 and ie < D_MAX:
                    u[ie] = torch.tensor([(e[1] - cx) / ECHELLE, (e[2] - cy) / ECHELLE,
                                          float(e[4]), 1.0])
                    ie += 1
            obs[t] = torch.cat([v.reshape(-1), u.reshape(-1)])
        ctx = torch.zeros(DIM_CTX)
        ctx[5] = 1.0                                     # 1 = hors banc
        return {'obs': obs, 'ctx': ctx, 'pris': 0.0, 'a_pris': 0.0}

    def sur_carte(self, dev):
        """Met le corpus ENTIER sur la carte, une fois. Sans ca, chaque minibatch etait fabrique en
        Python — 80 pas par minute, soit quatre heures pour un entrainement et vingt-cinq pour les
        six. Le goulot n etait pas le calcul mais la fabrication des lots.

        Chaque episode est decoupe d avance en fenetres de longueur L qui se recouvrent : tirer un
        lot devient une simple indexation."""
        fen_o, fen_c, fen_p, fen_m, fen_src = [], [], [], [], []
        for src, lst in ((0, self.banc), (1, self.ouvert)):
            for e in lst:
                T = e['obs'].shape[0]
                if T < self.L:
                    o = torch.cat([e['obs'], e['obs'][-1:].repeat(self.L - T, 1)])
                    deb = [0]
                    plein = o
                else:
                    plein = e['obs']
                    deb = list(range(0, T - self.L + 1, max(1, self.L // 4)))
                    # LA DERNIERE FENETRE DOIT ATTEINDRE LA FIN DE L EPISODE. Bug du 31/07 : avec
                    # des episodes de 60 pas et des fenetres de 50 commencant tous les 12, aucune
                    # fenetre n atteignait jamais la fin — le masque du verdict << pris >> valait
                    # zero partout, la tete n a JAMAIS ete entrainee, et sa perte affichait 0,0000,
                    # ce que j ai pris pour une reussite parfaite. Elle annoncait 100 % de prise
                    # partout la ou le reel allait de 14 a 33 %.
                    if (T - self.L) not in deb:
                        deb.append(T - self.L)
                for d in deb:
                    fen_o.append(plein[d:d + self.L])
                    fen_c.append(e['ctx'])
                    # « pris » ne se lit qu a la FIN d un episode : une fenetre du milieu n en
                    # porte pas le verdict, on la masque.
                    # LE VERDICT EST UNE PROPRIETE DE L EPISODE, pas de la fenetre finale. On le
                    # porte sur TOUTES les fenetres : la tete devra le PREVOIR depuis n importe
                    # quel instant, au lieu de le LIRE sur la photo d arrivee. Bug du 31/07 : elle
                    # n etait interrogee qu au dernier pas, donc depuis un etat qui avait deja vu
                    # l issue — en boucle ouverte elle annoncait 77 a 96 % la ou le reel allait de
                    # 14 a 33 %.
                    fen_p.append(e['pris'])
                    fen_m.append(e['a_pris'])
                    fen_src.append(src)
        self.O = torch.stack(fen_o).to(dev)
        self.C = torch.stack(fen_c).to(dev)
        self.P = torch.tensor(fen_p, device=dev)
        self.M = torch.tensor(fen_m, device=dev)
        src = torch.tensor(fen_src, device=dev)
        self.i_banc = (src == 0).nonzero(as_tuple=True)[0]
        self.i_ouvert = (src == 1).nonzero(as_tuple=True)[0]
        mo = self.O.element_size() * self.O.nelement() / 1e6
        print('  fenetres : %d banc + %d hors banc = %.0f Mo sur la carte'
              % (len(self.i_banc), len(self.i_ouvert), mo), flush=True)
        return self

    def lot(self, n, part_ouvert=0.0, dev='cpu'):
        """Un minibatch. part_ouvert = 0,5 realise le melange 50/50 PAR MINIBATCH : c est le ratio
        qui controle la distribution, pas la taille brute des deux corpus sur le disque."""
        if part_ouvert > 0 and len(self.i_ouvert) > 0:
            k = int(round(n * part_ouvert))
            ia = self.i_ouvert[torch.randint(len(self.i_ouvert), (k,), device=self.O.device)]
            ib = self.i_banc[torch.randint(len(self.i_banc), (n - k,), device=self.O.device)]
            idx = torch.cat([ia, ib])
        else:
            idx = self.i_banc[torch.randint(len(self.i_banc), (n,), device=self.O.device)]
        return self.O[idx], self.C[idx], self.P[idx], self.M[idx]


# ----------------------------------------------------------------------------- modele
class Encodeur(nn.Module):
    """Encodeur PAR ENTITE partage, agrege par somme separement sur chaque camp. Les defenseurs
    sont interchangeables : on encode cette invariance au lieu de la faire apprendre."""

    def __init__(self, h=128, sortie=256):
        super().__init__()
        self.att = nn.Sequential(nn.Linear(F_ATT, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU())
        self.def_ = nn.Sequential(nn.Linear(F_DEF, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU())
        # LA SOMME SEULE NE SUFFIT PAS. Elle rend les defenseurs interchangeables, ce qui est
        # voulu — mais on ne retrouve pas douze positions individuelles a partir d une somme, et le
        # decodeur doit precisement les rendre. Mesure du 31/07 sur le monde jouet : reconstruction
        # a ~28 m d erreur avec l observation SOUS LES YEUX, et le modele perdait contre l inertie.
        # On garde donc la somme, qui porte la structure, et on lui adjoint la vue BRUTE homme par
        # homme, qui porte l identite.
        plat = A_MAX * F_ATT + D_MAX * F_DEF
        self.fusion = nn.Sequential(nn.Linear(2 * h + plat + DIM_CTX, sortie), nn.SiLU())

    def forward(self, obs, ctx):
        B = obs.shape[0]
        a = obs[:, :A_MAX * F_ATT].view(B, A_MAX, F_ATT).clone()
        d = obs[:, A_MAX * F_ATT:].view(B, D_MAX, F_DEF).clone()
        ea = (self.att(a) * a[..., 4:5]).sum(1)
        ed = (self.def_(d) * d[..., 3:4]).sum(1)
        plat = torch.cat([a.reshape(a.shape[0], -1), d.reshape(d.shape[0], -1)], -1)
        return self.fusion(torch.cat([ea, ed, plat, ctx], -1))


class RSSM(nn.Module):
    """LATENT CONTINU, et non un tirage de des categoriel.

    DreamerV3 tire des des (32 categorielles x 32 classes) parce que son observation est une IMAGE :
    la precision n y compte pas, la multiplicite des futurs si. Notre observation est une poignee de
    coordonnees, et il faut de la PRECISION.

    Mesure du 31/07 sur le monde jouet, avec un latent de 16 des a 16 faces : 64 bits par pas, la
    ou decrire quarante positions au metre pres en demande environ trois cents. Et comme
    l observation n atteint la memoire du modele QU EN PASSANT par ce latent, tout le reste etait
    condamne : reconstruction a ~40 m d erreur avec l image sous les yeux, et le modele perdait
    contre l inertie sur des trajectoires rectilignes. Elargir l encodeur n avait rien change — le
    goulot n etait pas la.
    """

    def __init__(self, det=384, sto=64, h=256):
        super().__init__()
        self.det, self.sto = det, sto
        self.enc = Encodeur()
        self.gru = nn.GRUCell(self.sto + DIM_CTX, det)
        self.prior = nn.Sequential(nn.Linear(det, h), nn.SiLU(), nn.Linear(h, 2 * sto))
        self.post = nn.Sequential(nn.Linear(det + 256, h), nn.SiLU(), nn.Linear(h, 2 * sto))
        # voie directe encodeur -> decodeur : le latent stochastique n a pas a transporter seul
        # quarante nombres de position, il porte ce qui est INCERTAIN.
        f = det + self.sto
        self.dec = nn.Sequential(nn.Linear(f, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(),
                                 nn.Linear(h, A_MAX * F_ATT + D_MAX * F_DEF))
        self.morts = nn.Sequential(nn.Linear(f, h), nn.SiLU(), nn.Linear(h, A_MAX + D_MAX))
        self.cont = nn.Sequential(nn.Linear(f, h), nn.SiLU(), nn.Linear(h, 1))
        self.pris = nn.Sequential(nn.Linear(f, h), nn.SiLU(), nn.Linear(h, 1))

    def _loi(self, sortie):
        mu, ls = sortie.chunk(2, -1)
        # PLANCHER A 0,01 ET NON 0,1. Le plancher injecte un bruit irreductible dans le latent, et
        # le decodeur le repercute sur les positions. A 0,1 pour une echelle de 100 m, cela vaut
        # DIX METRES d imprecision imposee — exactement le plafond sur lequel le modele butait
        # (13,0 puis 10,1 puis 8,94 m a travers quatre architectures differentes). Ce n etait pas un
        # probleme d apprentissage : je lui avais interdit d etre plus precis.
        sigma = F.softplus(ls) + 0.01
        return mu, sigma

    def _ech(self, sortie):
        mu, sigma = self._loi(sortie)
        return mu + sigma * torch.randn_like(mu), (mu, sigma)

    def observer(self, obs, ctx, h):
        e = self.enc(obs, ctx)
        s, lpost = self._ech(self.post(torch.cat([h, e], -1)))
        lprior = self._loi(self.prior(h))          # la loi ENTIERE (moyenne, ecart-type)
        return s, lpost, lprior

    def avancer(self, h, s, ctx):
        return self.gru(torch.cat([s, ctx], -1), h)

    def imaginer(self, h):
        """Tirage depuis la loi A PRIORI : l etat suivant SANS regarder aucune observation.
        C est la seule facon honnete de derouler en boucle ouverte. Bug du 31/07 : l evaluation
        rebouclait par la loi a posteriori sur sa propre prediction, ce qui revient a redecrire le
        dernier passe au lieu de predire l avenir — le modele finissait entre << rien ne bouge >>
        et la verite, et perdait contre l inertie sur un monde jouet a trajectoire rectiligne."""
        s, _ = self._ech(self.prior(h))
        return s

    def tetes(self, h, s):
        f = torch.cat([h, s], -1)
        return self.dec(f), self.morts(f), self.cont(f), self.pris(f)


def kl(lp, lq, libre=1.0):
    """Divergence entre deux lois normales diagonales, avec un plancher de bits libres.
    Le plancher est PAR DIMENSION et non sur la somme : sur la somme, le modele pouvait tout
    ignorer en restant sous un seul nat au total."""
    mp, sp = lp
    mq, sq = lq
    d = (torch.log(sq / sp) + (sp ** 2 + (mp - mq) ** 2) / (2 * sq ** 2) - 0.5)
    return torch.clamp(d, min=libre / 64.0).sum(-1).mean()


def entrainer(a):
    torch.manual_seed(a.graine); random.seed(a.graine)
    dev = a.device
    print('=== corpus ===', flush=True)
    c = Corpus(held_out=a.held_out, avec_ouvert=(a.corpus == 'mixte'), longueur=a.longueur)
    print('  banc : %d episodes | hors banc : %d fenetres | held-out ecarte : %s'
          % (len(c.banc), len(c.ouvert), a.held_out), flush=True)
    if a.corpus == 'mixte' and not c.ouvert:
        sys.exit('REFUS : bras MIXTE demande mais le corpus hors banc est vide.')
    c.sur_carte(dev)
    m = RSSM().to(dev)
    n_par = sum(p.numel() for p in m.parameters())
    print('  parametres : %.2f M' % (n_par / 1e6), flush=True)
    opt = torch.optim.Adam(m.parameters(), lr=3e-4, eps=1e-5)
    part = 0.5 if a.corpus == 'mixte' else 0.0
    t0 = time.time()
    for pas in range(1, a.pas + 1):
        obs, ctx, pris, masq = c.lot(a.lot, part_ouvert=part, dev=dev)
        B, T, _ = obs.shape
        h = torch.zeros(B, m.det, device=dev)
        s = torch.zeros(B, m.sto, device=dev)
        p_rec = p_kl = p_mort = p_pris = 0.0
        for t in range(T):
            s, lpost, lprior = m.observer(obs[:, t], ctx, h)
            dec, mo, co, pr = m.tetes(h, s)
            # SOMME et non moyenne sur les dimensions. Bug du 31/07 : la reconstruction etait une
            # moyenne sur 92 nombres, donc 0,018, quand la divergence valait 0,66 — le terme qui
            # pousse a l OUBLI etait 37 fois plus lourd que celui qui pousse a DECRIRE.
            # L optimiseur a fait le calcul : il a tout oublie, c etait moins cher. Symptome
            # mesure : le modele predisait mieux a vingt pas (16 m) qu a un seul (72 m), parce
            # qu il recitait la moyenne au lieu de regarder ou sont les hommes.
            # La divergence se compte en nats : la reconstruction doit se sommer, pas se moyenner.
            # MASQUE DE PRESENCE. Les tenseurs ont douze places d attaquant alors qu un episode en
            # compte quatre ou huit : mesure du 31/07, 18,5 % des places sont VIDES et remplies de
            # zeros. On entrainait donc le modele a decrire du vide, et la tete des morts a declarer
            # morts des hommes qui n existent pas. Le vide n est pas une observation.
            _pres = _masque_presence(obs[:, t])
            p_rec = p_rec + (F.mse_loss(dec, symlog(obs[:, t]), reduction='none')
                             * _pres).sum(-1).mean()
            # POIDS RAMENES A NOTRE REGIME. Les 0,5 et 0,1 viennent de DreamerV3, ou la
            # reconstruction porte sur une IMAGE et vaut des milliers de nats : la divergence y pese
            # environ un milliesime de la reconstruction. Chez nous l observation fait 92 nombres et
            # la reconstruction vaut ~1,4 nat, donc la divergence a 2,2 pesait DIX FOIS PLUS que ce
            # qu elle doit peser. Mesure du 31/07 : le modele redecrivait a 10 m une image sous les
            # yeux, parce qu oublier restait plus rentable que decrire.
            p_kl = p_kl + 0.05 * kl((lpost[0].detach(), lpost[1].detach()), lprior) \
                        + 0.01 * kl(lpost, (lprior[0].detach(), lprior[1].detach()))
            vivant = torch.cat([obs[:, t].view(B, -1)[:, 2:A_MAX * F_ATT:F_ATT],
                                obs[:, t].view(B, -1)[:, A_MAX * F_ATT + 2::F_DEF]], -1)
            # PONDERATION DE LA CLASSE RARE. Mesure du 31/07 sur le vrai banc : 83,8 % des hommes
            # presents sont vivants a un instant donne, donc repondre << tout le monde vit >> suffit
            # a faire un bon score — et la perte tombait a 0,05, ce que j ai lu comme du talent. Le
            # modele sous-estimait alors les pertes de quarante a cinquante pour cent. Le poids 3,08
            # egalise les deux classes ; il est MESURE, pas choisi.
            _pv = torch.cat([obs[:, t].view(B, -1)[:, 4:A_MAX * F_ATT:F_ATT],
                             obs[:, t].view(B, -1)[:, A_MAX * F_ATT + 3::F_DEF]], -1)
            _poids = _pv * torch.where(vivant > 0.5, torch.ones_like(vivant),
                                       torch.full_like(vivant, POIDS_MORT))
            p_mort = p_mort + (F.binary_cross_entropy_with_logits(mo, vivant, reduction='none')
                               * _poids).sum(-1).mean()
            # interrogee A CHAQUE PAS, et non seulement au dernier : prevoir, pas lire.
            pp = F.binary_cross_entropy_with_logits(pr.squeeze(-1), pris, reduction='none')
            p_pris = p_pris + (pp * masq).sum() / masq.sum().clamp(min=1.0)
            h = m.avancer(h, s, ctx)
        perte = (p_rec + p_mort + p_pris) / T + p_kl / T
        opt.zero_grad(set_to_none=True)
        perte.backward()
        nn.utils.clip_grad_norm_(m.parameters(), 100.0)
        opt.step()
        if pas % 100 == 0 or pas == 1:
            print('  pas %6d | perte %8.4f | rec %7.4f | kl %7.4f | mort %6.4f | pris %6.4f | %5.1f min'
                  % (pas, float(perte), float(p_rec / T), float(p_kl / T), float(p_mort / T),
                     float(p_pris / T), (time.time() - t0) / 60), flush=True)
    emp = {}
    for f in ('CRITERES_TEST_VALEUR.md', 'CRITERES_PORTE.md'):
        p = os.path.join('/home/younes/arma3-marl/leviathan', f)
        if os.path.exists(p):
            emp[f] = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
    torch.save({'modele': m.state_dict(), 'corpus': a.corpus, 'graine': a.graine,
                'pas': a.pas, 'held_out': a.held_out, 'empreintes': emp,
                'n_banc': len(c.banc), 'n_ouvert': len(c.ouvert)}, a.sortie)
    print('ecrit : %s' % a.sortie)
    print('MODELE_DONE')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', choices=['banc', 'mixte'], default='banc')
    ap.add_argument('--pas', type=int, default=20000)
    ap.add_argument('--lot', type=int, default=32)
    ap.add_argument('--longueur', type=int, default=50)
    ap.add_argument('--graine', type=int, default=0)
    ap.add_argument('--held-out', default='envelop')
    ap.add_argument('--device', default='cuda:0')
    ap.add_argument('--sortie', default='modele.pt')
    entrainer(ap.parse_args())
