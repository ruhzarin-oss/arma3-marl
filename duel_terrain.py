"""duel_terrain — AssaultTerrain BILATÉRAL pour la co-évolution soldat-vs-soldat.
Les DEUX camps sont des soldats APPRIS (mêmes obs 17 = arma_obs, mêmes actions 0-12) :
  - ATTAQUANTS (A) : spawn au bord, objectif = prendre le FOB (origine).
  - DÉFENSEURS (B) : spawn au FOB, objectif = tenir (origine aussi -> ils restent + repoussent).
Récompense ZÉRO-SOMME : chaque camp veut tuer l'autre / (prendre|tenir) le FOB. On réutilise
les mécaniques EXACTES d'assault_terrain (LOS 2.5D `_losc`, tir SUPPRESS, postures). 100% GPU, pas de physique.
"""
import math
import torch
import terrain_gpu as TG
import numpy as np
import formations as FORM


class DuelTerrain:
    def __init__(self, num_envs=1024, A=9, B=9, R_spawn=120.0, R_def=22.0,
                 move=14.0, fire_range=110.0, hit=0.10, secure_r=25.0, max_steps=60, dmg_dead=0.7,
                 death_pen=0.15, win_bonus=2.5, kill_w=2.5,
                 a_form="coin", b_form="demi_cercle", form_forward=18.0, form_w=0.0, mutual_support=False, flank=0.0,
                 replica=True, replica_path="replica.npz", device="cuda:0", seed=0):
        self.N = num_envs; self.A = A; self.B = B; self.dev = device
        self.R_spawn = R_spawn; self.R_def = R_def
        self.move = move; self.fire_range = fire_range; self.hit = hit; self.secure_r = secure_r
        self.max_steps = max_steps; self.dmg_dead = dmg_dead
        self.death_pen = death_pen; self.win_bonus = win_bonus; self.kill_w = kill_w
        self.form_forward = form_forward; self.form_w = form_w   # form_w>0 -> récompense de MANIEMENT des formes (tenir le rang hors engagement)
        self.mutual_support = mutual_support   # option B : le bon espacement (formation) réduit les dégâts reçus -> la forme PAIE
        self.flank = flank   # AFFORDANCE FLANC : touché de flanc/dos = plus de dégâts -> contourner (tenaille/échelon) PAIE
        self.a_form_idx = torch.full((num_envs,), FORM.NAMES.index(a_form), dtype=torch.long, device=device)   # forme PAR ENV (l'étage HAUT la choisit)
        self.b_form_idx = torch.full((num_envs,), FORM.NAMES.index(b_form), dtype=torch.long, device=device)
        self._tmplA = FORM.templates(A, device=device); self._tmplB = FORM.templates(B, device=device)          # slots canoniques des 15 formes
        self.a_maneuver = torch.zeros(num_envs, dtype=torch.long, device=device)   # 0=assaut 1=defend 2=hunt 3=bounding (l'étage HAUT la choisit)
        self.b_maneuver = torch.zeros(num_envs, dtype=torch.long, device=device)
        # ENVELOPPEMENT en CONTINUUM (Phase 2 : ouvrir l'espace) : profondeur du débordement (m) + ratio DÉBORDEURS, par env.
        self.a_depth = torch.full((num_envs,), 55.0, device=device); self.b_depth = torch.full((num_envs,), 55.0, device=device)
        self.a_split = torch.full((num_envs,), 0.5, device=device); self.b_split = torch.full((num_envs,), 0.5, device=device)
        # DÉCOMPOSITION (man==5) : parts FIXEURS (bas de rang) et RUSHEURS (haut de rang) ; le reste = FLANC.
        self.a_fix = torch.full((num_envs,), 0.40, device=device); self.b_fix = torch.full((num_envs,), 0.40, device=device)
        self.a_rush = torch.full((num_envs,), 0.30, device=device); self.b_rush = torch.full((num_envs,), 0.30, device=device)
        self.n_forms = len(FORM.NAMES); self.n_maneuvers = 6; self.n_actions = 13; self.obs_dim = 17; self.squad_dim = 6   # +envelopper +décomposé
        self._sd = 3.0
        self._eye_lut = torch.tensor([1.7, 1.0, 0.3], device=device)
        d = device
        R = np.load(replica_path)
        self._elevR = torch.tensor(R["elev"].astype("float32"), device=d)
        self._solid = torch.tensor(R["solid"].astype("float32"), device=d)
        self._solidhR = torch.tensor(R["solidh"].astype("float32"), device=d) if "solidh" in R.files else torch.zeros_like(self._solid)
        self._lowhR = torch.tensor(R["lowh"].astype("float32"), device=d) if "lowh" in R.files else torch.zeros_like(self._solid)
        self.terr_G = int(R["GS"]); self.terr_R = float(R["W"]); self.scale = self.terr_R
        self.R_spawn = min(R_spawn, self.terr_R - 25.0)
        self.g = torch.Generator(device=d).manual_seed(seed)
        N = num_envs
        for nm, n in (("ax", A), ("ay", A), ("admg", A), ("bx", B), ("by", B), ("bdmg", B)):
            setattr(self, nm, torch.zeros(N, n, device=d))
        self.apost = torch.zeros(N, A, dtype=torch.long, device=d); self.bpost = torch.zeros(N, B, dtype=torch.long, device=d)
        self.a_lastdmg = torch.zeros(N, A, device=d); self.b_lastdmg = torch.zeros(N, B, device=d)
        self.a_supp = torch.zeros(N, A, device=d); self.b_supp = torch.zeros(N, B, device=d)
        self.t = torch.zeros(N, dtype=torch.long, device=d)
        self.hm = self._elevR; self.cover = self._solid          # carte unique partagée (comme replica)
        self._reset(torch.arange(N, device=d))

    # ---- terrain helpers (identiques à assault_terrain) ----
    def _sample_solid(self, px, py):
        G = self.terr_G
        gx = ((px / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        gy = ((py / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        return self._solid[gy, gx]

    def _sample_field(self, field, px, py):
        G = self.terr_G
        gx = ((px / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        gy = ((py / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        return field[gy, gx]

    def _losc(self, ax, ay, bx, by, eye_a, eye_b):                # LOS 2.5D : le relief (elevR) ET le bâti (solidh) occultent
        K = 24; t = torch.linspace(0.0, 1.0, K, device=self.dev)
        pxr = ax.unsqueeze(-1) * (1 - t) + bx.unsqueeze(-1) * t
        pyr = ay.unsqueeze(-1) * (1 - t) + by.unsqueeze(-1) * t
        za = self._sample_field(self._elevR, ax, ay) + eye_a
        zb = self._sample_field(self._elevR, bx, by) + eye_b
        z_ray = za.unsqueeze(-1) * (1 - t) + zb.unsqueeze(-1) * t
        top = self._sample_field(self._elevR, pxr, pyr) + self._sample_field(self._solidhR, pxr, pyr) + self._sample_field(self._lowhR, pxr, pyr)
        blocked = (top > z_ray).any(-1)
        return (~blocked).float()

    def _eye(self, post): return self._eye_lut[post]

    def _reset(self, idx):
        n = idx.numel(); d = self.dev
        # attaquants au bord (anneau), cap aléatoire
        th = torch.rand(n, generator=self.g, device=d) * 2 * math.pi
        sx = self.R_spawn * torch.sin(th); sy = self.R_spawn * torch.cos(th)
        ar = torch.arange(self.A, device=d).float()
        self.ax[idx] = sx[:, None] + (ar % 3) * 6 - 6; self.ay[idx] = sy[:, None] + (ar - 1) * 5
        # défenseurs autour du FOB (origine)
        dth = torch.arange(self.B, device=d).float() / self.B * 2 * math.pi
        self.bx[idx] = self.R_def * torch.cos(dth)[None] + torch.randn(n, self.B, device=d) * 3.0
        self.by[idx] = self.R_def * torch.sin(dth)[None] + torch.randn(n, self.B, device=d) * 3.0
        for nm in ("admg", "bdmg", "a_lastdmg", "b_lastdmg", "a_supp", "b_supp"):
            getattr(self, nm)[idx] = 0.0
        self.apost[idx] = 0; self.bpost[idx] = 0; self.t[idx] = 0
        # anti-mur (replica) : pousse hors du bâti
        for _ in range(8):
            wa = self._sample_solid(self.ax[idx], self.ay[idx]) > 0.5
            self.ax[idx] = torch.where(wa, self.ax[idx] * 0.94, self.ax[idx]); self.ay[idx] = torch.where(wa, self.ay[idx] * 0.94, self.ay[idx])

    def reset(self): return self._obs_A(), self._obs_B()
    def _a_alive(self): return self.admg < self.dmg_dead
    def _b_alive(self): return self.bdmg < self.dmg_dead

    def set_forms(self, a_idx=None, b_idx=None):
        """L'étage HAUT (commandant) pose la forme par env."""
        if a_idx is not None: self.a_form_idx = a_idx.long()
        if b_idx is not None: self.b_form_idx = b_idx.long()

    def set_maneuvers(self, a_m=None, b_m=None):
        """L'étage HAUT pose la manœuvre par env (0=assaut 1=defend 2=hunt 3=bounding)."""
        if a_m is not None: self.a_maneuver = a_m.long()
        if b_m is not None: self.b_maneuver = b_m.long()

    def set_envelop(self, a_depth=None, b_depth=None, a_split=None, b_split=None):
        """Paramètres de l'enveloppement (continuum) : profondeur du débordement (m) + ratio DÉBORDEURS [0,1], par env."""
        def _v(x): return x if torch.is_tensor(x) else torch.full((self.N,), float(x), device=self.dev)
        if a_depth is not None: self.a_depth = _v(a_depth)
        if b_depth is not None: self.b_depth = _v(b_depth)
        if a_split is not None: self.a_split = _v(a_split)
        if b_split is not None: self.b_split = _v(b_split)

    def set_decompose(self, a_fix=None, b_fix=None, a_rush=None, b_rush=None):
        """Parts des sous-groupes de la manœuvre DÉCOMPOSÉE : fixeurs (bas de rang) + rusheurs (haut de rang), reste = flanc."""
        def _v(x): return x if torch.is_tensor(x) else torch.full((self.N,), float(x), device=self.dev)
        if a_fix is not None: self.a_fix = _v(a_fix)
        if b_fix is not None: self.b_fix = _v(b_fix)
        if a_rush is not None: self.a_rush = _v(a_rush)
        if b_rush is not None: self.b_rush = _v(b_rush)

    def squad_obs(self, side):
        """Obs d'escouade (N,6) pour le COMMANDANT : centroïde self rel objectif, vecteur vers l'ennemi, effectifs."""
        S = self.scale
        if side == 0: sx, sy, sal, ex, ey, eal = self.ax, self.ay, self._a_alive(), self.bx, self.by, self._b_alive()
        else:         sx, sy, sal, ex, ey, eal = self.bx, self.by, self._b_alive(), self.ax, self.ay, self._a_alive()
        ws = sal.float().sum(1).clamp(min=1); we = eal.float().sum(1).clamp(min=1)
        scx = (sx * sal.float()).sum(1) / ws; scy = (sy * sal.float()).sum(1) / ws
        ecx = (ex * eal.float()).sum(1) / we; ecy = (ey * eal.float()).sum(1) / we
        return torch.stack([scx / S, scy / S, (ecx - scx) / S, (ecy - scy) / S,
                            sal.float().sum(1) / sx.shape[1], eal.float().sum(1) / ex.shape[1]], dim=1)

    def _side_slots(self, sx, sy, salive, form_idx, tmpl, tx, ty, forward):
        """Numéro d'agent i -> SON slot dans la forme CHOISIE PAR L'ENV. Ancre = centroïde poussé de 'forward' vers (tx,ty)."""
        w = salive.float(); ws = w.sum(1).clamp(min=1)
        cx = (sx * w).sum(1) / ws; cy = (sy * w).sum(1) / ws
        dxo = tx - cx; dyo = ty - cy; dist = torch.sqrt(dxo * dxo + dyo * dyo).clamp(min=1e-3)
        heading = torch.atan2(dxo / dist, dyo / dist)
        fwd_t = forward if torch.is_tensor(forward) else torch.full_like(dist, forward)   # forward scalaire OU par env
        fp = torch.minimum(fwd_t, dist)
        ax = cx + dxo / dist * fp; ay = cy + dyo / dist * fp
        pos, _ = FORM.place_idx(form_idx, tmpl, torch.stack([ax, ay], -1), heading)   # forme par env
        return pos[..., 0], pos[..., 1]

    def _fidelity(self, sx, sy, salive, form_idx, tmpl, ex, ey, ealive, tx, ty, forward):
        """Récompense de MANIEMENT : proche de son slot ET pas engagé. S'efface quand un ennemi est à
        portée -> libre de rompre pour combattre. Apprend le JUGEMENT (quand tenir, quand rompre)."""
        d = self.dev
        slot_x, slot_y = self._side_slots(sx, sy, salive, form_idx, tmpl, tx, ty, forward)
        dist = torch.sqrt((sx - slot_x) ** 2 + (sy - slot_y) ** 2)                     # écart au slot (N,n)
        dx = ex.unsqueeze(1) - sx.unsqueeze(2); dy = ey.unsqueeze(1) - sy.unsqueeze(2)
        BIG = torch.tensor(1e18, device=d)
        nd = torch.where(ealive.unsqueeze(1), dx * dx + dy * dy, BIG).min(2).values.sqrt()
        engaged = (nd < self.fire_range).float()                                       # ennemi à portée = engagé
        fid = torch.exp(-dist / 15.0) * (1.0 - engaged)                                # tenir le rang SEULEMENT hors engagement
        return (fid * salive.float()).sum(1) / salive.float().sum(1).clamp(min=1)      # (N,) moyenne escouade

    def _support_mult(self, sx, sy, salive):
        """APPUI MUTUEL (option B) : multiplicateur de dégâts REÇUS par soldat. Voisins vivants au bon
        espacement [4,20]m -> couverture d'arcs -> moins de dégâts. Isolé -> normal. Aggloméré (<4m) ->
        plus de dégâts (blob = cible). Rend la BONNE formation payante -> elle est adoptée par intérêt."""
        d = self.dev; n = sx.shape[1]
        dx = sx.unsqueeze(1) - sx.unsqueeze(2); dy = sy.unsqueeze(1) - sy.unsqueeze(2)   # (N,n,n) : allié j vu de i
        dist = torch.sqrt(dx * dx + dy * dy + 1e-6)
        aj = salive.unsqueeze(1) & ~torch.eye(n, dtype=torch.bool, device=d)[None]
        support = ((dist >= 9.0) & (dist <= 32.0) & aj).float().sum(2)                   # voisins au bon espacement (formation ~12m)
        cluster = ((dist < 9.0) & aj).float().sum(2)                                     # voisins trop proches = BLOB (pénalisé)
        mult = 1.0 - 0.55 * (support / 3.0).clamp(max=1.0) + 0.30 * (cluster / 2.0).clamp(max=1.0)
        return mult.clamp(0.35, 1.3)                                                     # (N,n)

    # ---- obs générique 17 features pour un camp (self) face à l'autre (enemy) ; feat 2,3 = VECTEUR VERS MON SLOT ----
    def _side_obs(self, sx, sy, spost, salive, ex, ey, ealive, s_lastdmg, s_supp, slot_x, slot_y):
        N, n = sx.shape; m = ex.shape[1]; S = self.scale; d = self.dev
        relx = sx / S; rely = sy / S                              # position relative à l'objectif (origine)
        vsx = (slot_x - sx) / S; vsy = (slot_y - sy) / S          # VECTEUR VERS MON SLOT (remplace la dir-objectif brute)
        eye_s = self._eye(spost)
        # ennemi le plus proche + LOS + distance
        dx = ex.unsqueeze(1) - sx.unsqueeze(2); dy = ey.unsqueeze(1) - sy.unsqueeze(2)   # (N,n,m)
        BIG = torch.tensor(1e18, device=d)
        ed2 = torch.where(ealive.unsqueeze(1), dx * dx + dy * dy, BIG)
        km = ed2.argmin(2); bx = torch.gather(ex, 1, km); by = torch.gather(ey, 1, km)
        nd = ed2.min(2).values.clamp(max=1e17).sqrt()
        los = self._losc(sx, sy, bx, by, eye_a=eye_s, eye_b=1.7)
        # menace : nb d'ennemis vivants qui me voient à portée
        thr = torch.zeros(N, n, device=d)
        for j in range(m):
            l = self._losc(sx, sy, ex[:, j:j+1].expand(N, n), ey[:, j:j+1].expand(N, n), eye_a=eye_s, eye_b=1.7)
            dist = torch.sqrt((sx - ex[:, j:j+1]) ** 2 + (sy - ey[:, j:j+1]) ** 2)
            thr += ealive[:, j:j+1].float() * l * (dist < self.fire_range).float()
        # coéquipier le plus proche (dx,dy), suppresse-t-il, feu d'équipe
        adx = sx.unsqueeze(1) - sx.unsqueeze(2); ady = sy.unsqueeze(1) - sy.unsqueeze(2)  # (N,n,n) ally-self? -> self-self
        eye_m = torch.eye(n, dtype=torch.bool, device=d)[None]
        a2 = torch.where(eye_m | ~salive.unsqueeze(1), BIG, adx * adx + ady * ady); jm = a2.argmin(2)
        madx = torch.gather(sx, 1, jm) - sx; mady = torch.gather(sy, 1, jm) - sy      # ally - self
        nm_ally = a2.min(2).values >= 1e18
        madx = (madx / S).masked_fill(nm_ally, 0.0); mady = (mady / S).masked_fill(nm_ally, 0.0)
        asup = torch.gather(s_supp, 1, jm)
        tf = ((s_supp * salive.float()).sum(1, keepdim=True) / salive.float().sum(1, keepdim=True).clamp(min=1)).expand(N, n)
        dc = torch.zeros(N, n, device=d)                          # dcover=0 en replica (comme l'entraînement)
        base = torch.stack([relx, rely, vsx, vsy, salive.float(), dc, los, (nd / S).clamp(max=1.0)], dim=2)
        suf = torch.stack([(s_lastdmg * 5.0).clamp(max=1.0), (thr / self.B).clamp(max=1.0)], dim=2)
        team = torch.stack([madx, mady, asup, tf], dim=2)
        post = torch.stack([(spost == 0).float(), (spost == 1).float(), (spost == 2).float()], dim=2)
        return torch.cat([base, suf, team, post], dim=2)          # (N,n,17)

    def _obs_A(self):
        z = torch.zeros(self.N, device=self.dev)                            # attaquants : formation vers le FOB (origine)
        sx, sy = self._side_slots(self.ax, self.ay, self._a_alive(), self.a_form_idx, self._tmplA, z, z, self.form_forward)
        return self._side_obs(self.ax, self.ay, self.apost, self._a_alive(), self.bx, self.by, self._b_alive(), self.a_lastdmg, self.a_supp, sx, sy)

    def _obs_B(self):
        aw = self._a_alive().float(); aws = aw.sum(1).clamp(min=1)
        acx = (self.ax * aw).sum(1) / aws; acy = (self.ay * aw).sum(1) / aws  # centroïde attaquant = la menace
        sx, sy = self._side_slots(self.bx, self.by, self._b_alive(), self.b_form_idx, self._tmplB, acx, acy, 0.0)   # défenseurs tiennent, face à la menace
        return self._side_obs(self.bx, self.by, self.bpost, self._b_alive(), self.ax, self.ay, self._a_alive(), self.b_lastdmg, self.b_supp, sx, sy)

    def _move_fire(self, acts, sx, sy, spost, salive, ex, ey, ealive, eye_e):
        """déplace un camp (actions 0-7), pose posture (10-12) ; renvoie (nouv sx,sy,spost, supp_mask, dmg infligé à l'ennemi)."""
        d = self.dev; N, n = sx.shape; m = ex.shape[1]
        th = acts.float() * (math.pi / 4.0); spd = self.move * (acts < 8).float() * salive.float()
        osx, osy = sx.clone(), sy.clone()
        sx = (sx + torch.sin(th) * spd).clamp(-self.scale * 0.99, self.scale * 0.99)
        sy = (sy + torch.cos(th) * spd).clamp(-self.scale * 0.99, self.scale * 0.99)
        wall = self._sample_solid(sx, sy) > 0.5
        sx = torch.where(wall, osx, sx); sy = torch.where(wall, osy, sy)
        for pa, pv in ((10, 0), (11, 1), (12, 2)):
            spost = torch.where(acts == pa, torch.full_like(spost, pv), spost)
        supp = (acts == 9) & salive                              # SUPPRESS = tir
        dmg_e = torch.zeros(N, m, device=d)
        eye_s = self._eye(spost)
        if self.flank > 0:                                       # la cible fait face au GROS de l'assaut (centroïde des tireurs)
            sw = salive.float(); sws = sw.sum(1, keepdim=True).clamp(min=1)
            scx = (sx * sw).sum(1, keepdim=True) / sws; scy = (sy * sw).sum(1, keepdim=True) / sws   # (N,1)
            face_ang = torch.atan2(scx - ex, scy - ey)           # (N,m) orientation présumée de la cible
        for i in range(n):
            bx = sx[:, i:i+1].expand(N, m); by = sy[:, i:i+1].expand(N, m)
            los = self._losc(ex, ey, bx, by, eye_a=eye_e, eye_b=eye_s[:, i:i+1])
            dist = torch.sqrt((ex - sx[:, i:i+1]) ** 2 + (ey - sy[:, i:i+1]) ** 2)
            eff = los * (dist < self.fire_range).float() * supp[:, i:i+1].float() * ealive.float()
            if self.flank > 0:                                   # tir de FACE ×1, de FLANC ×(1+f/2), de DOS ×(1+f)
                shot_ang = torch.atan2(sx[:, i:i+1] - ex, sy[:, i:i+1] - ey)
                eff = eff * (1.0 + self.flank * (1.0 - torch.cos(shot_ang - face_ang)) / 2.0)
            dmg_e += 0.10 * eff
        return sx, sy, spost, supp.float(), dmg_e

    def step(self, aA, aB, auto_reset=True):
        d = self.dev; N = self.N
        aal0 = self._a_alive().float().sum(1); bal0 = self._b_alive().float().sum(1)
        eyeA = self._eye(self.apost); eyeB = self._eye(self.bpost)
        # les deux camps agissent (tir simultané, dégâts appliqués après)
        self.ax, self.ay, self.apost, self.a_supp, dmg_to_b = self._move_fire(aA, self.ax, self.ay, self.apost, self._a_alive(), self.bx, self.by, self._b_alive(), eyeB)
        self.bx, self.by, self.bpost, self.b_supp, dmg_to_a = self._move_fire(aB, self.bx, self.by, self.bpost, self._b_alive(), self.ax, self.ay, self._a_alive(), eyeA)
        if self.mutual_support:                                                       # option B : la formation réduit les dégâts reçus
            dmg_to_a = dmg_to_a * self._support_mult(self.ax, self.ay, self._a_alive())
            dmg_to_b = dmg_to_b * self._support_mult(self.bx, self.by, self._b_alive())
        self.a_lastdmg = (dmg_to_a * self._a_alive().float()).detach(); self.b_lastdmg = (dmg_to_b * self._b_alive().float()).detach()
        self.admg = (self.admg + dmg_to_a).clamp(max=0.95); self.bdmg = (self.bdmg + dmg_to_b).clamp(max=0.95)
        self.t = self.t + 1
        aal = self._a_alive().float().sum(1); bal = self._b_alive().float().sum(1)
        a_killed = (bal0 - bal) / self.B; b_killed = (aal0 - aal) / self.A         # fractions tuées ce pas
        a_lost = (aal0 - aal) / self.A; b_lost = (bal0 - bal) / self.B
        # objectif pris ? (un attaquant vivant atteint l'origine)
        adist = torch.sqrt(self.ax ** 2 + self.ay ** 2)
        took = ((adist < self.secure_r) & self._a_alive()).any(1)
        a_wiped = aal < 0.5; b_wiped = bal < 0.5
        timeout = self.t >= self.max_steps
        att_wins = took | b_wiped
        def_wins = (a_wiped & ~att_wins) | (timeout & ~att_wins)
        done = att_wins | def_wins
        # récompense ZÉRO-SOMME (mêmes knobs que SHAMAL)
        rA = self.kill_w * a_killed - self.death_pen * a_lost + self.win_bonus * att_wins.float() - self.win_bonus * def_wins.float()
        rB = self.kill_w * b_killed - self.death_pen * b_lost + self.win_bonus * def_wins.float() - self.win_bonus * att_wins.float()
        if self.form_w > 0:                                                            # récompense de MANIEMENT des formes
            z = torch.zeros(N, device=d)
            rA = rA + self.form_w * self._fidelity(self.ax, self.ay, self._a_alive(), self.a_form_idx, self._tmplA, self.bx, self.by, self._b_alive(), z, z, self.form_forward)
            aw = self._a_alive().float(); aws = aw.sum(1).clamp(min=1)
            acx = (self.ax * aw).sum(1) / aws; acy = (self.ay * aw).sum(1) / aws
            rB = rB + self.form_w * self._fidelity(self.bx, self.by, self._b_alive(), self.b_form_idx, self._tmplB, self.ax, self.ay, self._a_alive(), acx, acy, 0.0)
        info = {"att_wins": att_wins, "def_wins": def_wins, "a_alive": aal / self.A, "b_alive": bal / self.B, "took": took}
        if auto_reset:
            self._reset(done.nonzero(as_tuple=True)[0])
        return (self._obs_A(), self._obs_B()), (rA, rB), done.float(), info
