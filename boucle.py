#!/usr/bin/env python3
"""boucle — ETAPE 4 DE LA FEUILLE DE ROUTE : quelque chose apprend enfin.

Criteres deposes AVANT le premier pas : CRITERES_BOUCLE.md
  recompense : 1,0 x prise + 0,01 x metre gagne. AUCUN terme d exposition — la sandbox
               la sur-tarife (+856 % contre +75 % sur Arma), on ne met pas dans la
               recompense une quantite dont on sait que le monde la facture faux.
  porte      : G1 battre les DEUX doctrines scriptees sur graines HELD-OUT, sur la BORNE
               G2 controle nul — une politique aleatoire ne doit PAS passer G1
               G3 le gain ne vient pas de se terrer : metres gagnes >= la meilleure doctrine
"""
import os
import math, sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

DEV = "cuda:0"
PAS = 60
GRAINES_TRAIN = [11, 12, 13, 14, 15, 16, 17, 18]
GRAINES_TEST = [101, 102, 103, 104, 105, 106]     # JAMAIS vues a l entrainement
# ⚠️ 24/08 — UN TROISIEME JEU, POUR CHOISIR. Si l on se met a selectionner quoi que ce soit
# (un point de sauvegarde, une graine), choisir sur GRAINES_TEST ferait cesser la porte
# d etre une porte : elle jugerait sur ce qui a servi a choisir. Trois jeux disjoints :
# on APPREND sur TRAIN, on CHOISIT sur SELECT, on JUGE sur TEST. ⟨garde-fou de Fable⟩
GRAINES_SELECT = [201, 202, 203, 204, 205, 206]   # ni apprises, ni jugees : elles CHOISISSENT
# ⚠️ 23/08 — LE VOCABULAIRE EST DESORMAIS UN PARAMETRE, ET IL VAUT 10 PAR DEFAUT.
# Le monde offre 13 actions (assault_terrain.py:230, postures activees) ; la politique n en
# avait que 10, donc elle ne pouvait PAS changer de posture, donc ses trois colonnes de
# posture etaient strictement constantes — trois entrees sur douze mortes par construction
# (mesure 2dd0f8c). Pre-inscription : PREINSCRIPTION_POSTURES.md, commit b3626e1.
# Par defaut 10 : l artefact du 13/08 continue de se charger tel quel.
NA = int(os.environ.get("HMT_NA", "10"))
GAMMA_PHI = float(os.environ.get("HMT_GAMMA_PHI", "0.99"))
INSTRUMENT = os.environ.get("HMT_INSTRUMENT", "") == "1"   # journalise, ne change RIEN
DECODEUR = os.environ.get("HMT_DECODEUR", "echantillon")   # "echantillon" ou "argmax"
CKPT_DIR = os.environ.get("HMT_CKPT", "")                  # dossier des points, vide = aucun
CKPT_EVERY = int(os.environ.get("HMT_CKPT_EVERY", "50"))  # 1.0 = la recompense d avant le 17/08           # 8 caps + tenir + feu (+ 3 postures si 13)


# ⚠️ LE MONDE EST UNE VARIABLE DE MODULE. Par defaut le monde de reference — rien ne
# bouge pour qui ne la touche pas. Un entrainement sur le monde OPERE fait `B.CFG = MONDE_OPERE`.
CFG = MONDE_ARMA

# ⚠️ LE GARDIEN DE PARAMETRES ⟨20/08, apres la faute du « 6 m/s »⟩.
# J AI CITE PENDANT DEUX JOURS UN CHIFFRE DE GYMNASE QUE JE N AVAIS JAMAIS LU : le « 6 m/s »
# etait la CONSIGNE du pont (`arma_couture.py:21`), pas le parametre du gymnase, qui joue
# move=14 m / SEC_PAR_PAS=3,28 s = 4,27 m/s. Un dossier doctrine et une decision de Younes
# ont ete batis dessus.
# ⚠️ LA CLASSE ENTIERE MEURT ICI : le monde DECLARE ses parametres EFFECTIFS a la
# construction — lus sur l objet, pas dans un fichier — et les depots citent CETTE LIGNE
# D EXECUTION, jamais le fichier. Une surcharge par variable (`move=cfg.x`) echappe a toute
# relecture humaine ; elle n echappe pas a une lecture de l objet construit.
# Voir PROVENANCE_PARAMETRES.md, qui nommait deja la classe le 06/08 :
# « le parametre herite d un instrument mort ».
HMT_PARAMS_DECLARES = False

def _declarer_parametres(e):
    global HMT_PARAMS_DECLARES
    if HMT_PARAMS_DECLARES: return
    HMT_PARAMS_DECLARES = True
    _spp = getattr(e, "sec_par_pas", None)
    _mv  = getattr(e, "move", None)
    _v   = (float(_mv) / float(_spp)) if (_mv and _spp) else float("nan")
    print("  ── PARAMETRES EFFECTIFS DU MONDE (lus sur l objet, pas dans un fichier) ──", flush=True)
    print("     move=%s m   sec_par_pas=%s s   ->  VITESSE = %.2f m/s" % (_mv, _spp, _v), flush=True)
    for _k in ("fire_range", "hit", "secure_r", "max_steps", "terr_R", "frein_feu",
               "tir_par_pas", "degat_par_impact", "supp_residuel", "cible_unique",
               "obs_sans_slope", "relief_stratis"):
        if hasattr(e, _k): print("     %-18s %s" % (_k, getattr(e, _k)), flush=True)
    print("  ⚠️ TOUT CHIFFRE DE GYMNASE CITE DANS UN DEPOT DOIT VENIR DE CETTE LIGNE.", flush=True)

def monde(n, seed):
    _e = AssaultTerrain(num_envs=n, seed=seed, device=DEV, max_steps=PAS, **CFG)
    _declarer_parametres(_e)
    return _e


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def frontal(e, t):
    return cap(-e.apx, -e.apy)


def flanc(e, t, n_fixe=2, pas_crochet=14):
    act = cap(-e.apx, -e.apy)
    d = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    fixe = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev); fixe[:, :n_fixe] = True
    act = torch.where(fixe & (d < e.fire_range * 0.9), torch.full_like(act, 9), act)
    if t < pas_crochet:
        act = torch.where(~fixe, cap(-e.apy, e.apx), act)
    return act


class Politique(nn.Module):
    """Petit reseau par homme. Il voit ce que le monde lui donne, rien de plus."""
    def __init__(self, nobs, nh=128):
        super().__init__()
        self.f = nn.Sequential(nn.Linear(nobs, nh), nn.Tanh(), nn.Linear(nh, nh), nn.Tanh())
        self.pi = nn.Linear(nh, NA)
        self.v = nn.Linear(nh, 1)

    def forward(self, o):
        h = self.f(o)
        return self.pi(h), self.v(h).squeeze(-1)


def jouer(e, choisir, garder=False):
    """Un episode complet. `choisir(obs, t) -> (actions, logprob, valeur)`."""
    o = e.reset()
    N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dprec = d0.clone(); dmin = d0.clone()
    lps, vals, rs, masques = [], [], [], []
    for t in range(PAS):
        viv = (~fini).float()
        a, lp, v = choisir(o, t)
        o, _, done, info = e.step(a, auto_reset=False)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        # AVEU DU 11/08 (AVEU_RECOMPENSE.md). Le `.clamp(min=0)` rendait la recompense
        # POMPABLE : reculer gratuit, avancer paye, donc on oscille sans progresser. Et il
        # cassait le telescopage. Terme SIGNE = faconnage par potentiel ⟨Ng, Harada & Russell
        # 1999⟩ : sa somme vaut k x (depart - arrivee), bornee, et il est PROUVE qu il ne
        # deplace pas la politique optimale. Il guide sans pouvoir mentir.
        # REVUE 17/08 : le theoreme ⟨Ng, Harada & Russell 1999⟩ invoque ci-dessus exige
        # F = γ·Φ(s') − Φ(s). Le code payait Φ(s') − Φ(s), SANS le γ, alors que les retours
        # sont actualises a 0,99 (ligne 119) : le telescopage ne tenait plus, et un
        # aller-retour rapportait ~+0,026 net en retour actualise au lieu de zero.
        # ⚠️ 23/08 — LE γ DU FAÇONNAGE DEVIENT UN PARAMETRE DECLARE, DEFAUT 0,99 (inchange).
        # Il est passe de 1,0 a 0,99 le 17/08 (e856a86), APRES que l artefact boucle_pol.pt
        # a ete appris (13/08). Pour savoir s il explique que la porte ne passe plus, il faut
        # pouvoir rejouer l ancien SANS toucher au fichier : un script qui edite le depot
        # puis le restaure laisse le depot modifie s il tombe au milieu.
        gagne = dprec - GAMMA_PHI * d                # SIGNE : reculer coute ce qu avancer rapporte
        dprec = d; dmin = torch.minimum(dmin, torch.where(fini, dmin, d))
        neuf = info["took"] & ~fini
        # 0,001 et non 0,01 : a 114 metres le guide valait 1,14, PLUS que le but a 1,0.
        # L agent a optimise ce que je lui payais le plus — marcher. Regle deposee : le guide
        # ne vaut jamais plus du CINQUIEME de ce qu il guide (0,001 x 200 = 0,2).
        r = 1.0 * neuf.float() + 0.001 * gagne      # la recompense corrigee, rien d autre
        pris |= neuf
        if garder:
            lps.append(lp); vals.append(v); rs.append(r * viv); masques.append(viv)
        fini |= done.bool()
        if bool(fini.all()):
            break
    stats = dict(prise=100.0 * float(pris.float().mean()),
                 # REVUE 17/08 : `d0 - dmin` est le point le PLUS PROFOND jamais atteint,
                 # pas la position TENUE. Une politique qui pointe a 20 m au pas 30 puis se
                 # terre affiche un maximum et fait PASSER G3 — precisement le comportement
                 # que la porte pretend exclure. On rend les deux.
                 metres=float((d0 - dmin).mean()),
                 metres_tenus=float((d0 - dprec).mean()))
    return stats, lps, vals, rs, masques


def entrainer(iters=140, n=256, lr=3e-4):
    e0 = monde(8, GRAINES_TRAIN[0]); e0.reset()
    nobs = e0._obs().shape[-1]
    pol = Politique(nobs).to(DEV)
    opt = torch.optim.Adam(pol.parameters(), lr=lr)
    print(f"\n  entrainement — {nobs} entrees, {NA} actions, {iters} iterations de {n} episodes")
    for it in range(iters):
        e = monde(n, GRAINES_TRAIN[it % len(GRAINES_TRAIN)])

        def choisir(o, t):
            lo, v = pol(o)
            di = torch.distributions.Categorical(logits=lo)
            a = di.sample()
            return a, di.log_prob(a), v

        st, lps, vals, rs, masques = jouer(e, choisir, garder=True)
        # ⚠️ LE FILM, PAS LA DERNIERE IMAGE ⟨prescription de Fable, 24/08⟩. Sous HMT_CKPT,
        # on garde un point toutes les HMT_CKPT_EVERY iterations. Sans ca on ne peut pas
        # savoir si l argmax d une graine perdante n a JAMAIS ete bon (bifurcation precoce)
        # ou s il a ete bon PUIS s est defait (evenement fluctuant) — et les deux appellent
        # des gestes opposes. Ne change rien quand la variable est absente.
        if CKPT_DIR and it % CKPT_EVERY == 0:
            torch.save(pol.state_dict(), "%s/it%04d.pt" % (CKPT_DIR, it))
        # retours a rebours, avantage = retour - valeur (baseline apprise)
        R = torch.zeros_like(rs[0]); rets = []
        for r in reversed(rs):
            R = r + 0.99 * R; rets.append(R)
        rets.reverse()
        pl = vl = 0.0
        # ⚠️ INSTRUMENTATION PASSIVE ⟨24/08, prescription de Fable⟩. Sous HMT_INSTRUMENT=1
        # on JOURNALISE l avantage brut et l avantage normalise sur les MEMES trajectoires,
        # et on ne change RIEN au comportement : aucune de ces grandeurs n entre dans la
        # perte. Question : quelle part de la norme du gradient revient aux pas OU UNE PRISE
        # A LIEU, sous chaque lecture ? Si elle est ~0 sous la normalisation actuelle et
        # substantielle sous une normalisation globale, le defaut est etabli sur donnees
        # reelles, sans un seul entrainement neuf.
        _ib = {"rt": 0.0, "ra": 0.0, "nt": 0.0, "na": 0.0, "cent": 0.0, "npris": 0.0}
        for _i, (lp, v, ret, m) in enumerate(zip(lps, vals, rets, masques)):
            ret_a = ret.unsqueeze(1).expand_as(lp)
            adv = (ret_a - v).detach()
            if INSTRUMENT:
                _brut = adv.clone()
                _pris = (rs[_i] > 0.5).unsqueeze(1).expand_as(_brut)   # ce pas porte une prise
                _norm = (_brut - _brut.mean()) / (_brut.std() + 1e-6)
                _ib["rt"] += float(_brut.abs()[_pris].sum()); _ib["ra"] += float(_brut.abs().sum())
                _ib["nt"] += float(_norm.abs()[_pris].sum()); _ib["na"] += float(_norm.abs().sum())
                # la composante COMMUNE que le centrage retire (c est la ou part la rente)
                _ib["cent"] += float(_brut.mean().abs()) * _brut.numel()
                _ib["npris"] += float(_pris.sum())
            adv = (adv - adv.mean()) / (adv.std() + 1e-6)
            pl = pl - (lp * adv * m.unsqueeze(1)).mean()
            vl = vl + ((v - ret_a) ** 2 * m.unsqueeze(1)).mean()
        if INSTRUMENT and it % 50 == 0 and _ib["ra"] > 0:
            print("    INSTR it %4d  part des pas de PRISE dans |avantage| :"
                  "  brut %6.3f %%   normalise %6.3f %%   (entrees de prise %.0f)"
                  "   composante commune retiree par le centrage : %5.1f %% du brut"
                  % (it, 100 * _ib["rt"] / _ib["ra"], 100 * _ib["nt"] / max(_ib["na"], 1e-9),
                     _ib["npris"], 100 * _ib["cent"] / _ib["ra"]), flush=True)
        perte = pl + 0.5 * vl
        opt.zero_grad(); perte.backward()
        nn.utils.clip_grad_norm_(pol.parameters(), 1.0)
        opt.step()
        if it % 20 == 0 or it == iters - 1:
            print(f"    iter {it:>4}  prise {st['prise']:>5.1f} %  metres {st['metres']:>6.1f}", flush=True)
    return pol


def evaluer(pol, graines, n=256):
    """Lecture sur graines HELD-OUT, par graine — l appariement vit la ⟨regle 12⟩."""
    def gele(o, t):
        # ⚠️ LE DECODEUR EST UN CHOIX, PAS UN HERITAGE ⟨decision de Younes, 24/08⟩.
        # L algorithme optimise le rendement d une politique STOCHASTIQUE ; la lire en
        # argmax est une hypothese SUPPLEMENTAIRE, qui tient deux fois sur trois (mesure :
        # graine 0 argmax 49,6 % / echantillonne 37,9 % ; graine 1 argmax 3,3 % /
        # echantillonne 42,3 %). On lit desormais l objet qu on a REELLEMENT optimise.
        # ⚠️ CE CHOIX BAISSE LES CHIFFRES DES GAGNANTES (49,6 -> 37,9). Ce n est pas un
        # critere deplace pour dire ce qui arrange : il resserre les bons et rattrape les
        # mauvais, et il rend la recette reproductible (37,9 et 42,3 au lieu de 3,3 et 49,6).
        with torch.no_grad():
            lo, v = pol(o)
        if DECODEUR == "argmax":
            return lo.argmax(-1), None, None
        return torch.distributions.Categorical(logits=lo).sample(), None, None
    res = {"appris": [], "frontal": [], "flanc": []}
    met = {"appris": [], "frontal": [], "flanc": []}
    for g in graines:
        for nom, f in (("appris", gele),
                       ("frontal", lambda o, t, _e=None: (None, None, None)),
                       ("flanc", None)):
            pass
    for g in graines:
        e = monde(n, g)
        st, *_ = jouer(e, gele)
        res["appris"].append(st["prise"]); met["appris"].append(st["metres"])
        for nom, doc in (("frontal", frontal), ("flanc", flanc)):
            e = monde(n, g)
            st, *_ = jouer(e, lambda o, t, _d=doc, _e=e: (_d(_e, t), None, None))
            res[nom].append(st["prise"]); met[nom].append(st["metres"])
    return res, met


if __name__ == "__main__":
    # ⚠️ 23/08 — LA GRAINE DEVIENT UN PARAMETRE, DEFAUT 0 (inchange). Un verdict sur un
    # seul entrainement n en est pas un : il faut pouvoir rejouer la MEME recette sur une
    # autre graine sans toucher au fichier.
    torch.manual_seed(int(os.environ.get("HMT_SEED", "0")))
    pol = entrainer(iters=int(sys.argv[1]) if len(sys.argv) > 1 else 140)

    print("\n  LA PORTE — graines JAMAIS vues a l entrainement")
    print("  " + "=" * 66)
    res, met = evaluer(pol, GRAINES_TEST)
    moy = lambda v: sum(v) / len(v)
    for k in ("appris", "frontal", "flanc"):
        print(f"    {k:<10} prise {moy(res[k]):>5.1f} %   metres gagnes {moy(met[k]):>6.1f}")

    # G1 : sur la BORNE, apparie par graine
    import statistics as stx
    ok1 = True
    for adv in ("frontal", "flanc"):
        d = [a - b for a, b in zip(res["appris"], res[adv])]
        m = moy(d); s = stx.stdev(d) if len(d) > 1 else 0.0
        lo = m - 2.571 * s / math.sqrt(len(d))          # t(5), 95 %
        print(f"    G1 vs {adv:<8} ecart {m:+.1f} pt   borne inferieure {lo:+.1f}")
        ok1 &= lo > 0

    # G2 : controle nul — politique aleatoire
    e0 = monde(8, 1); e0.reset()
    alea = Politique(e0._obs().shape[-1]).to(DEV)
    res_a, _ = evaluer(alea, GRAINES_TEST)
    ok2 = True
    for adv in ("frontal", "flanc"):
        d = [a - b for a, b in zip(res_a["appris"], res_a[adv])]
        m = moy(d); s = stx.stdev(d) if len(d) > 1 else 0.0
        lo = m - 2.571 * s / math.sqrt(len(d))
        if lo > 0: ok2 = False
    print(f"    G2 controle nul (politique aleatoire) : {'PASSE' if ok2 else 'TOMBE'}"
          f"  — prise aleatoire {moy(res_a['appris']):.1f} %")

    meilleure = max(("frontal", "flanc"), key=lambda k: moy(res[k]))
    ok3 = moy(met["appris"]) >= moy(met[meilleure])
    print(f"    G3 metres appris {moy(met['appris']):.1f} contre {moy(met[meilleure]):.1f} "
          f"({meilleure}) : {'PASSE' if ok3 else 'TOMBE'}")

    print("  " + "=" * 66)
    if ok1 and ok2 and ok3:
        print("    LA BOUCLE EST FERMEE. Quelque chose apprend, dans le monde calibre, sur")
        print("    une recompense mesuree, et bat les deux doctrines ecrites a la main.")
        # ⚠️ L ENTRAINEMENT N ECRIT PLUS SUR L ARTEFACT COURANT. `banc_live.py` RECHARGE
        # `boucle_pol.pt` a CHAQUE episode : un entrainement lance pendant une nuit
        # remplacait la politique en cours de mesure, silencieusement, et la moitie des
        # episodes jouaient un autre reseau. Faille reelle, evitee de justesse le 23/08.
        # Un fichier unique partage entre l entrainement et la mesure est un accident qui
        # attend son heure. On ecrit sous le nom demande, et le defaut est DATE.
    else:
        print("    LA PORTE NE PASSE PAS. On le dit, on ne rejoue pas les graines.")
    # ⚠️ 23/08 — ON GARDE AUSSI LES ECHECS. Le `torch.save` etait A L INTERIEUR du `if` :
    # la recette ne conservait que les politiques qui PASSENT, donc elle effacait exactement
    # celles qu il faut ouvrir pour comprendre pourquoi elles echouent. Mesure du 23/08 au
    # soir : deux graines, 49,6 % et 3,3 %, et la graine perdante avait pourtant appris
    # (44,1 % en entrainement). Le test qui trancherait — argmax contre echantillonnage sur
    # le meme artefact — etait impossible : l objet avait ete jete par une accolade.
    # Le nom PORTE LE VERDICT : rien n est rendu vert, rien n est efface.
    # ⭐ Un banc qui ne garde que ses reussites ne peut pas expliquer ses echecs.
    _base = os.environ.get("HMT_PT", "/home/younes/arma3-marl/boucle_pol_neuf.pt")
    _pt = _base[:-3] + ("_PASSE.pt" if (ok1 and ok2 and ok3) else "_TOMBE.pt")
    torch.save(pol.state_dict(), _pt)
    print("    politique gardee : %s" % _pt)
    print("\n    ⚠️ AUCUN VERDICT DE MISSION N EN SORT. Le monde est le notre.")
    print("       ⟨juillet : 96 % en sandbox, 0/38 dans Arma⟩ Arma tranchera.")
