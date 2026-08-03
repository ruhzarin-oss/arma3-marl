#!/usr/bin/env python3
"""monde_mission.py — UN SEUL MONDE, L'OBJECTIF EST UN PARAMETRE.

Contrat : CONTRAT_ORDRE_DE_MISSION.md (69eadd06ca4122e9). Tout ce qui n'y est pas
ne doit pas exister ici.

Verbes de cette version : PRENDRE et INFILTRER. Deux monnaies opposees — des vies
contre de l exposition. Si une seule politique ne tient pas deux objectifs contraires,
elle n en tiendra pas quatre : on le sait en une apres-midi au lieu d une semaine.

L ordre de mission (12 nombres) est ajoute a l observation de CHAQUE agent, a CHAQUE pas.
Budgets affiches en RESTANT, jamais en plafond : un plafond est une constante que l agent
ignore, un budget qui descend EST la decision.
L ordre ne contient AUCUNE information sur l ennemi.
"""
import math
import torch

VERBES = ['prendre', 'infiltrer']
N_VERBES = 4          # taille FIXE du one-hot : tenir/extraire viendront s y loger
DIM_ORDRE = 12

# --- constantes de recompense : LES MEMES POUR TOUS LES VERBES (regle anti-bricolage) ---
W_PROGRES = 1.0
W_PERTE = 0.5
R_SUCCES = 1.0
N_SUCCES = 2          # hommes vivants requis dans le rayon pour valider l objectif

# --- v5 : L ORDRE DEVIENT UN BUDGET (criteres CRITERES_V5_BUDGET.md 9274c81a3842a5e5) ---
# Le verbe etait une CONSTANTE d episode dont la consequence n existait qu au dernier pas :
# mesure du 2026-07-29, divergence d actions 0,00148 sur une echelle qui monte a 0,693.
# Le budget, lui, se CONSUME pendant l episode. C est une grandeur vivante, pas une etiquette.
LAMBDA_DEP = 0.5      # x R_SUCCES : la forme telescopique borne le total a -0,5.R_SUCCES,
                      # donc tout episode reussi domine STRICTEMENT l immobilite.


class MondeMission:
    """Enveloppe autour d AssaultTerrain. Tire une mission par episode et par env,
    expose l ordre dans l observation, calcule progres et succes selon le verbe."""

    def __init__(self, env, seed=0, verbes=None, device=None,
                 mode_budget=False, B_min=0.8, B_max=6.0, budget_force=None):
        self.env = env
        self.dev = device or env.dev
        self.N, self.A = env.N, env.A
        self.verbes = verbes or VERBES
        self.obs_dim = env.obs_dim + DIM_ORDRE
        self.n_actions = env.n_actions
        self.g = torch.Generator(device=self.dev); self.g.manual_seed(seed)
        self.mode_budget = bool(mode_budget)
        self.B_min, self.B_max = float(B_min), float(B_max)
        self.budget_force = budget_force
        # ETAPE 3b : la contrainte cesse d etre une penalite fixe payee des le premier
        # pas. Elle devient un multiplicateur qui PART DE ZERO et ne se resserre que
        # si l agent viole trop souvent. D abord apprendre la route, economiser ensuite.
        self.lam = 0.0
        self.mode_lagrangien = False
        # bornes du contrat
        self.R_MIN, self.R_MAX = 15.0, 30.0
        self.T_MIN, self.T_MAX = 40, 80
        self.K_MIN, self.K_MAX = 2, 3   # amendement 1 : plancher releve de 1 a 2
        self.E_MIN, self.E_MAX = 1.0, 1.8   # CALIBRE 2026-07-29 : expo au succes va de 0,93 (debordement) a 2,90 (frontal). Entre les deux, INFILTRER interdit les doctrines bruyantes.
        self._alloue()

    # ------------------------------------------------------------------ tirage
    def _alloue(self):
        N, d = self.N, self.dev
        z = lambda: torch.zeros(N, device=d)
        self.verbe = torch.zeros(N, dtype=torch.long, device=d)
        self.R = z(); self.T = z(); self.Kmax = z(); self.Emax = z()
        self.t = z(); self.expo_cum = z(); self.pertes_cum = z()
        self.d_prec = z(); self.d0 = z()
        self.succes = torch.zeros(N, dtype=torch.bool, device=d)
        self.pas_took = torch.full((N,), -1.0, device=d)
        self.expo_au_took = torch.zeros(N, device=d)
        self.pertes_au_took = torch.zeros(N, device=d)
        self.acquis = torch.zeros(N, dtype=torch.bool, device=d)   # succes DEJA obtenu dans l episode
        self.u_prec = torch.zeros(N, device=d)                     # depassement au pas precedent
        # ARRIVEE, INDEPENDANTE DE TOUTE CONTRAINTE (2026-07-29). Le champ `took` du
        # journal valait `pas_took >= 0`, or `pas_took` n est renseigne qu au SUCCES,
        # budget compris : les deux colonnes mesuraient la meme chose. On ne pouvait
        # donc pas repondre a la question qui decide du reetiquetage — l escouade
        # arrive-t-elle seulement a l objectif ?
        self.arrive = torch.zeros(N, dtype=torch.bool, device=d)

    def _tire(self, idx):
        n = int(idx.numel())
        if n == 0:
            return
        d = self.dev
        u = lambda: torch.rand(n, generator=self.g, device=d)
        self.verbe[idx] = torch.randint(0, len(self.verbes), (n,), generator=self.g, device=d)
        self.R[idx] = self.R_MIN + u() * (self.R_MAX - self.R_MIN)
        self.T[idx] = torch.round(self.T_MIN + u() * (self.T_MAX - self.T_MIN))
        self.Kmax[idx] = torch.round(self.K_MIN + u() * (self.K_MAX - self.K_MIN))
        if self.mode_budget:
            import math as _m
            # LOG-UNIFORME : un scalaire continu qui determine la penalite ne s ignore pas,
            # la ou un one-hot constant s ignore sans cout.
            lo, hi = _m.log(self.B_min), _m.log(self.B_max)
            self.Emax[idx] = torch.exp(lo + u() * (hi - lo))
            if self.budget_force is not None:
                self.Emax[idx] = float(self.budget_force)
        else:
            self.Emax[idx] = self.E_MIN + u() * (self.E_MAX - self.E_MIN)
        self.t[idx] = 0.0; self.expo_cum[idx] = 0.0; self.pertes_cum[idx] = 0.0
        self.succes[idx] = False; self.acquis[idx] = False
        self.pas_took[idx] = -1.0; self.expo_au_took[idx] = 0.0; self.pertes_au_took[idx] = 0.0
        self.u_prec[idx] = 0.0
        self.arrive[idx] = False

    # ------------------------------------------------------------------ mesures
    def _dist(self):
        """distance du plus proche attaquant VIVANT a l objectif (l objectif est a l origine)"""
        d = torch.sqrt(self.env.apx ** 2 + self.env.apy ** 2)
        vivant = self.env._aalive()
        d = torch.where(vivant, d, torch.full_like(d, 1e4))
        return d.min(dim=1).values

    def _n_dans_rayon(self):
        d = torch.sqrt(self.env.apx ** 2 + self.env.apy ** 2)
        return ((d < self.R[:, None]) & self.env._aalive()).float().sum(1)

    # ------------------------------------------------------------------ ordre
    def _ordre(self):
        """LES 12 NOMBRES. Budgets en RESTANT. Aucune information sur l ennemi."""
        N, d = self.N, self.dev
        o = torch.zeros(N, DIM_ORDRE, device=d)
        o[torch.arange(N, device=d), self.verbe] = 1.0                      # 1-4 verbe
        dmax = self.d0.clamp(min=1.0)
        o[:, 4] = (self.env.apx.mean(1) / dmax).clamp(-2, 2)                # 5-6 objectif
        o[:, 5] = (self.env.apy.mean(1) / dmax).clamp(-2, 2)
        o[:, 6] = self.R / self.R_MAX                                       # 7 rayon
        o[:, 7] = ((self.T - self.t) / self.T).clamp(0, 1)                  # 8 delai RESTANT
        o[:, 8] = ((self.Kmax - self.pertes_cum * self.A) / self.A).clamp(-1, 1)   # 9 vies RESTANTES
        o[:, 9] = ((self.Emax - self.expo_cum) / self.Emax).clamp(-1, 1)    # 10 expo RESTANTE
        o[:, 10] = self.env._aalive().float().sum(1) / self.A               # 11 effectif
        o[:, 11] = 0.0                                                      # 12 phase (EXTRAIRE)
        if self.mode_budget:
            # L ordre n est plus une etiquette : c est un budget qui se consume.
            o[:, 0] = (self.Emax / self.B_max).clamp(0, 1)                   # B
            o[:, 1] = (self.expo_cum / self.Emax).clamp(0, 4) / 4.0          # dose consommee
            o[:, 2] = ((self.T - self.t) / self.T).clamp(0, 1)               # temps restant
            o[:, 3] = ((self.Emax - self.expo_cum) / self.Emax).clamp(-1, 1) # budget restant
        return o

    def _obs(self, obs_base, permute=None):
        """M2 (jalon 1) : `permute` est un DECALAGE ENTIER, plus jamais un tenseur fourni
        par l appelant. La v1 recevait un tenseur calcule AVANT `step`, mais consomme ICI,
        c est-a-dire APRES `_tire` : pour tout environnement qui venait de finir, l ordre
        affichait la permutation d un verbe qui n existait deja plus. Resolu desormais a
        partir de l etat COURANT, la classe entiere de bug disparait."""
        ordre = self._ordre()
        if permute:                  # 0 ou None = ordre vrai
            ordre = ordre.clone()
            ordre[:, :N_VERBES] = 0.0
            affiche = (self.verbe + int(permute)) % len(self.verbes)
            ordre[torch.arange(self.N, device=self.dev), affiche] = 1.0
        return torch.cat([obs_base, ordre[:, None, :].expand(self.N, self.A, DIM_ORDRE)], dim=2)

    # ------------------------------------------------------------------ boucle
    def reset(self, permute=None):
        """M3 : la v1 n appliquait aucune permutation au premier pas d une evaluation
        permutee — le premier pas n etait donc jamais permute."""
        obs = self.env.reset()
        self._tire(torch.arange(self.N, device=self.dev))
        self.d0 = self._dist().clamp(min=1.0)
        self.d_prec = self.d0.clone()
        return self._obs(obs, permute)

    def step(self, acts, permute=None, auto_reset=True):
        """REFONTE 2026-07-29 : l EPISODE APPARTIENT AU MONDE.

        La version 1 tenait sa propre comptabilite d episode et appelait `_reset(idx)` a la
        main : les attaquants renaissaient devant une ligne defensive DEJA engagee et se
        faisaient tuer aussitot. Mesure : episodes de 10 pas, 48 % finissant par
        aneantissement complet, 0 % de reussite — y compris pour les six doctrines ecrites
        a la main, alors que le monde brut en prend 52,7 %.

        Desormais : `auto_reset=True`, le monde gere ses propres remises a zero, et la
        mission ne fait plus que CONDITIONNER LE SUCCES. Un budget depasse ne termine rien :
        il rend le succes impossible, et l episode s acheve quand le monde le decide.
        """
        # M1 : en mode episode (auto_reset=False) tous les environnements partent a t=0
        # et ne redemarrent jamais — le pas scalaire lu par les doctrines est alors exact.
        obs, _, done, info = self.env.step(acts, auto_reset=auto_reset)
        fini = done.bool()
        self.t += 1.0
        expo_pas = info['exposed'] if info['exposed'].dim() == 1 else info['exposed'].sum(1)
        self.expo_cum += expo_pas
        pertes = info['losses'].float()
        pertes_pas = (pertes - self.pertes_cum).clamp(min=0)
        self.pertes_cum = pertes

        dist = self._dist()
        rappro = (self.d_prec - dist) / self.d0
        est_infil = (self.verbe == self.verbes.index('infiltrer')) if 'infiltrer' in self.verbes \
            else torch.zeros_like(self.verbe, dtype=torch.bool)
        # AMENDEMENT 3 (2026-07-29) : la v2 soustrayait l exposition du progres, POUR LE SEUL
        # verbe INFILTRER. Deux fautes en une. D abord un POIDS PAR VERBE, que le contrat
        # interdit explicitement. Ensuite l effet mesure : bouger coutait a chaque pas et le
        # succes etait loin, donc la politique optimale a court terme etait de NE PAS BOUGER.
        # Resultat : 0 % de reussite en INFILTRER correctement ordonne, contre 23 % quand on
        # lui mentait en lui disant PRENDRE. J avais appris a l agent a se figer.
        # Le budget d exposition est DEJA dans le predicat de succes et DEJA visible dans
        # l ordre de mission. C est suffisant. Le progres est le meme pour les deux verbes.
        progres = rappro
        self.d_prec = dist

        # --- LE VERBE NE FAIT QU AJOUTER UNE CONTRAINTE AU SIGNAL DU MONDE ---
        # info['losses'] est une FRACTION de l escouade (0,25 = un homme sur quatre),
        # Kmax est en HOMMES. Mesure du 2026-07-29.
        dans_budget = (self.t <= self.T) & (self.pertes_cum * self.A <= self.Kmax)
        # `info['took']` du monde est l ARRIVEE brute : aucune contrainte, aucun budget.
        arrive_prec = self.arrive.clone()
        self.arrive = self.arrive | info['took']
        atteint = info['took'] & dans_budget
        if self.mode_budget:
            # AUCUNE BRANCHE DE VERBE : le succes est le meme pour tous les ordres, c est le
            # terme de dose qui fait le travail, et il le fait densement.
            succes_pas = atteint & (self.expo_cum < self.Emax)
        else:
            succes_pas = torch.where(est_infil, atteint & (self.expo_cum < self.Emax), atteint)
        # `took` est un ECLAIR : il se declenche AU MOMENT ou l objectif est atteint, pas
        # a la fin de l episode. Le lire seulement au pas terminal ne montre jamais rien
        # (mesure 2026-07-29 : 5246 declenchements, 0 succes compte). On le RETIENT.
        nouveau = succes_pas & ~self.acquis
        # M4 : instantanes FIGES sur le front montant, pour que l analyse puisse recalculer
        # le predicat de succes independamment de ce que le monde en dit.
        self.pas_took = torch.where(nouveau, self.t, self.pas_took)
        self.expo_au_took = torch.where(nouveau, self.expo_cum, self.expo_au_took)
        self.pertes_au_took = torch.where(nouveau, self.pertes_cum, self.pertes_au_took)
        self.acquis = self.acquis | succes_pas
        self.succes = self.acquis
        if self.mode_lagrangien:
            # LE SUCCES PORTE SUR L ARRIVEE, pas sur le succes contraint : la contrainte est
            # desormais le travail de lambda, pas celui du predicat. L evaluation, elle,
            # continue de mesurer le succes contraint — c est la vraie metrique.
            arrive_neuf = info['took'] & ~arrive_prec
            rew = (W_PROGRES * progres - W_PERTE * pertes_pas
                   + R_SUCCES * arrive_neuf.float() - self.lam * expo_pas)
            return_apres = True
        else:
            rew = W_PROGRES * progres - W_PERTE * pertes_pas + R_SUCCES * nouveau.float()
            return_apres = False
        if self.mode_budget and not self.mode_lagrangien:
            # DEPASSEMENT, FORME TELESCOPIQUE. Sous le budget la derivee est NULLE :
            # l exposition est contingentee, pas taxee. Un quota, pas un prix.
            u_t = ((self.expo_cum - self.Emax).clamp(min=0) / self.Emax).clamp(max=1.0)
            rew = rew - LAMBDA_DEP * R_SUCCES * (u_t - self.u_prec)
            self.u_prec = u_t

        # INSTANTANE COMPLET AVANT LE RE-TIRAGE (correctif du 2026-07-29, operation O1).
        # Les trois champs du moment du toucher etaient clones APRES `_tire`, qui venait de
        # les remettre a -1 : en mode continu, tout episode reussi sortait avec `pas_took=-1`.
        # Meme maladie que M1-M4 : une valeur lue apres que l etat a bouge. Invisible en mode
        # episode (pas de re-tirage), c est l analyse qui l a attrapee en refusant de conclure.
        acquis_avant = self.acquis.clone()
        verbe_avant = self.verbe.clone(); expo_avant = self.expo_cum.clone()
        pertes_avant = self.pertes_cum.clone(); t_avant = self.t.clone()
        arrive_avant = self.arrive.clone()
        pas_took_avant = self.pas_took.clone()
        expo_took_avant = self.expo_au_took.clone()
        pertes_took_avant = self.pertes_au_took.clone()
        # LES BORNES DE LA MISSION AUSSI. Troisieme instance de la meme maladie dans ce
        # fichier : clonees apres `_tire`, elles decrivaient la mission SUIVANTE, si bien
        # qu un episode termine etait juge avec le plafond de pertes d un autre.
        R_avant = self.R.clone(); T_avant = self.T.clone()
        Kmax_avant = self.Kmax.clone(); Emax_avant = self.Emax.clone(); d0_avant = self.d0.clone()

        idx = fini.nonzero(as_tuple=False).squeeze(-1)
        if auto_reset and idx.numel() > 0:   # le monde a DEJA repose la scene : on ne retire que la mission
            self._tire(idx)
            nd = self._dist()
            self.d0[idx] = nd[idx].clamp(min=1.0)
            self.d_prec[idx] = nd[idx]
        return self._obs(obs, permute), rew, fini, {
            'succes': acquis_avant, 'verbe': verbe_avant,
            'expo_cum': expo_avant, 'pertes': pertes_avant, 'duree': t_avant,
            'took': info['took'], 'arrive': arrive_avant, 'pas_took': pas_took_avant,
            'expo_au_took': expo_took_avant,
            'pertes_au_took': pertes_took_avant,
            'R': R_avant, 'T': T_avant, 'Kmax': Kmax_avant,
            'Emax': Emax_avant, 'd0': d0_avant}


def fabrique(episodes=4096, D=8, seed=0, device='cuda:0', verbes=None, steps=80,
             mode_budget=False, B_min=0.8, B_max=6.0, budget_force=None):
    """le monde MESURE fige : courbe n1, courbe n2, cible_unique — calibre sur Arma le 28/07"""
    import sys
    sys.path.insert(0, '/home/younes/arma3-marl')
    from assault_terrain import AssaultTerrain
    LEV = '/home/younes/arma3-marl/leviathan'
    env = AssaultTerrain(num_envs=episodes, A=4, D=D, seed=seed, device=device, max_steps=steps,
                         postures=True, hull=True, def_line=True, def_rand=True,
                         secure_task=True, secure_only=True,
                         courbe=LEV + '/courbe_toucher_juge.json',
                         tir_par_pas=1.15, sec_par_pas=3.28, degat_par_impact=0.233,
                         supp_residuel=0.08, supp_persist=0.35, cible_unique=True)
    return MondeMission(env, seed=seed, verbes=verbes, device=device,
                        mode_budget=mode_budget, B_min=B_min, B_max=B_max,
                        budget_force=budget_force)
