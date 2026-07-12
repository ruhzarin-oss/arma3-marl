#!/usr/bin/env python3
"""tail_envs.py — la QUEUE du répertoire : reworks (B6 repli, marksman) + fin de curriculum (CQB, sapeur,
mortier, défense statique, conduite). Même patron : env vectorisé torch, A/B voyant/aveugle, un signal
POSITIF vers l'état réussi, prime à l'usage pour l'équipement, départ aléatoire contre les pièges d'explo.
Chaque classe : __init__(n,device,blind,seed) · obs_dim · _obs · step→(obs,r,done,info[metric])."""
import math, torch


class Repli2Env:
    """B6 REPLI (rework) : tenir tant qu'on GAGNE, décrocher quand la MARÉE tourne. Tenir en gagnant = prime
    (on fait le job) ; tenir en perdant = attrition→mort ; décrocher = banque les survivants. Voit la marée ;
    aveugle non → mistime. action 0=tenir 1=décrocher. métrique=`score` (survivants banqués)."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 30; self.obs_dim = 4
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("mystr", "estr", "erate", "banked", "alive", "t", "ret"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.mystr[idx] = 1.0
        self.estr[idx] = 0.2 + torch.rand(n, device=dev) * 0.3
        self.erate[idx] = 0.03 + torch.rand(n, device=dev) * 0.07              # renfort ennemi (rythme aléatoire)
        self.banked[idx] = 0.0; self.alive[idx] = 1.0; self.t[idx] = 0.0; self.ret[idx] = 0.0

    def _obs(self):
        tide = (self.estr - self.mystr).clamp(-1, 1)                            # >0 = je perds (le secret)
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([z if self.blind else tide, self.mystr, self.banked, self.t / self.max_steps], dim=1)

    def step(self, action):
        dev = self.dev; live = self.alive * (1 - self.ret)
        losing = (self.estr > self.mystr).float()
        hold = (action == 0).float() * live; retreat = (action == 1).float() * live
        loss = hold * losing * (0.12 + 0.12 * torch.rand(self.N, device=dev))   # attrition en tenant qu'on perd
        self.mystr = (self.mystr - loss).clamp(min=0)
        dead = (self.mystr <= 0).float() * self.alive; self.alive = self.alive * (1 - dead)
        self.banked = torch.where(retreat > 0, self.mystr, self.banked)         # décrocher = banque
        self.ret = (self.ret + retreat).clamp(0, 1)
        self.estr = self.estr + self.erate
        early = retreat * (self.estr < 0.45).float()                            # décrocher trop tôt = abandon
        r = hold * (1 - losing) * 0.15 - hold * losing * 0.4 - dead * 5.0 + retreat * self.mystr * 3.0 - early * 1.5
        self.t += 1
        done = (self.ret > 0) | (self.alive == 0) | (self.t >= self.max_steps)
        banked = torch.where((self.ret == 0) & (self.alive > 0) & (self.t >= self.max_steps), self.mystr, self.banked)
        info = {"score": banked.clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info


class Marksman2Env:
    """MARKSMAN (rework) : tirs LIMITÉS (3), plusieurs cibles dont 1-2 HVT (le secret) — prioriser les HVT.
    Voit qui est HVT ; aveugle gaspille sur les grouillots. action=tirer cible k (0..4). métrique=`hvt`."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.M = 5; self.SHOTS = 3; self.max_steps = 4
        self.obs_dim = self.M + 1
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        if not hasattr(self, "hvt"):
            self.hvt = torch.zeros(self.N, self.M, device=dev); self.dead = torch.zeros(self.N, self.M, device=dev)
            self.shots = torch.zeros(self.N, device=dev); self.killed = torch.zeros(self.N, device=dev)
            self.tot = torch.zeros(self.N, device=dev); self.t = torch.zeros(self.N, device=dev)
        h = (torch.rand(n, self.M, device=dev) < 0.3).float()
        h[:, 0] = (torch.rand(n, device=dev) < 0.8).float()                     # au moins souvent 1 HVT
        self.hvt[idx] = h; self.dead[idx] = 0.0; self.shots[idx] = float(self.SHOTS)
        self.killed[idx] = 0.0; self.tot[idx] = h.sum(1).clamp(min=1); self.t[idx] = 0.0

    def _obs(self):
        hv = self.hvt if not self.blind else torch.zeros(self.N, self.M, device=self.dev)
        return torch.cat([hv * (1 - self.dead), (self.shots / self.SHOTS).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev; a = action.clamp(0, self.M - 1).unsqueeze(1)
        can = (self.shots > 0).float()
        already = self.dead.gather(1, a).squeeze(1)
        ishvt = self.hvt.gather(1, a).squeeze(1)
        kill = can * (1 - already)
        self.dead.scatter_(1, a, (self.dead.gather(1, a) + kill.unsqueeze(1)).clamp(0, 1))
        self.shots = (self.shots - can).clamp(min=0)
        self.killed = self.killed + kill * ishvt                                # seul un HVT compte
        r = kill * ishvt * 3.0 - kill * (1 - ishvt) * 0.5 - 0.05                # prime HVT, coût grouillot
        self.t += 1
        done = (self.shots <= 0) | (self.t >= self.max_steps)
        info = {"hvt": (self.killed / self.tot).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info


class CQBEnv:
    """CQB : combat rapproché, engager EN PREMIER la menace qui te VISE (imminente), sinon elle te tue.
    4 secteurs, menaces présentes, 1 = l'assaillant qui vise (le secret). Voit qui vise ; aveugle random.
    action=engager secteur k. métrique=`score` (survécu ET nettoyé)."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 4; self.max_steps = 4
        self.obs_dim = 2 * self.D
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        if not hasattr(self, "threat"):
            self.threat = torch.zeros(self.N, self.D, device=dev); self.aim = torch.zeros(self.N, self.D, device=dev)
            self.dead = torch.zeros(self.N, self.D, device=dev); self.alive = torch.zeros(self.N, device=dev)
            self.t = torch.zeros(self.N, device=dev); self.tot = torch.zeros(self.N, device=dev)
        th = (torch.rand(n, self.D, device=dev) < 0.6).float(); th[:, 0] = 1.0
        aimsec = torch.randint(0, self.D, (n,), device=dev)
        am = torch.zeros(n, self.D, device=dev); am.scatter_(1, aimsec.unsqueeze(1), 1.0)
        am = am * th                                                            # l'assaillant est une menace réelle
        self.threat[idx] = th; self.aim[idx] = am; self.dead[idx] = 0.0
        self.alive[idx] = 1.0; self.t[idx] = 0.0; self.tot[idx] = th.sum(1).clamp(min=1)

    def _obs(self):
        z = torch.zeros(self.N, self.D, device=self.dev)
        return torch.cat([self.threat * (1 - self.dead), z if self.blind else self.aim * (1 - self.dead)], dim=1)

    def step(self, action):
        dev = self.dev; a = action.clamp(0, self.D - 1).unsqueeze(1)
        kill = (1 - self.dead.gather(1, a).squeeze(1)) * self.threat.gather(1, a).squeeze(1) * self.alive
        killed_aim = kill * self.aim.gather(1, a).squeeze(1)
        self.dead.scatter_(1, a, (self.dead.gather(1, a) + kill.unsqueeze(1)).clamp(0, 1))
        # l'assaillant encore vivant après le 1er temps te tue
        aim_alive = ((self.aim * (1 - self.dead)).sum(1) > 0).float()
        hit = aim_alive * (self.t >= 1).float()
        self.alive = self.alive * (1 - hit)
        r = kill * 1.0 + killed_aim * 2.0 - hit * 5.0 - 0.05
        self.t += 1
        cleared = ((self.threat * (1 - self.dead)).sum(1) <= 0).float()
        done = (self.alive == 0) | (cleared > 0) | (self.t >= self.max_steps)
        info = {"score": (self.alive * cleared)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info


class SapeurEnv:
    """SAPEUR : poser la charge sur le POINT FAIBLE de la structure pour brécher (limité 2). Bon point=brèche ;
    mauvais=perdu. Voit le point faible ; aveugle random. action=poser secteur k (0..5) / attendre(6). métrique=`breached`."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 6; self.CH = 2; self.max_steps = 5
        self.obs_dim = self.D + 1
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("weak", "charges", "breached", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.weak[idx] = torch.randint(0, self.D, (n,), device=dev).float()
        self.charges[idx] = float(self.CH); self.breached[idx] = 0.0; self.t[idx] = 0.0

    def _obs(self):
        oh = torch.zeros(self.N, self.D, device=self.dev)
        if not self.blind: oh.scatter_(1, self.weak.long().unsqueeze(1), 1.0)
        return torch.cat([oh, (self.charges / self.CH).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev
        place = (action < self.D).float() * (self.charges > 0).float()
        good = (action == self.weak.long()).float() * place
        self.breached = (self.breached + good).clamp(0, 1)
        self.charges = (self.charges - place).clamp(min=0)
        r = good * 5.0 - place * (1 - good) * 0.3 - 0.05                        # prime au bon point, coût gaspi RÉDUIT
        self.t += 1
        timeout = (self.t >= self.max_steps) & (self.breached <= 0)             # finir sans brèche = échec puni
        r = r - timeout.float() * 3.0
        done = (self.breached > 0) | (self.charges <= 0) | (self.t >= self.max_steps)
        info = {"breached": self.breached}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info


class MortierEnv:
    """MORTIER (appui indirect) : frapper le secteur le plus DENSE en ennemis, ÉVITER le secteur ami.
    Voit densités + où sont les amis ; aveugle random → tir fratricide. action=tir secteur k (0..5). métrique=`score`."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 6; self.SH = 3; self.max_steps = 3
        self.obs_dim = 2 * self.D
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        if not hasattr(self, "dens"):
            self.dens = torch.zeros(self.N, self.D, device=dev); self.friend = torch.zeros(self.N, self.D, device=dev)
            self.sh = torch.zeros(self.N, device=dev); self.killed = torch.zeros(self.N, device=dev)
            self.ff = torch.zeros(self.N, device=dev); self.t = torch.zeros(self.N, device=dev)
        d = torch.rand(n, self.D, device=dev)
        fsec = torch.randint(0, self.D, (n,), device=dev)
        fr = torch.zeros(n, self.D, device=dev); fr.scatter_(1, fsec.unsqueeze(1), 1.0)
        self.dens[idx] = d; self.friend[idx] = fr; self.sh[idx] = float(self.SH)
        self.killed[idx] = 0.0; self.ff[idx] = 0.0; self.t[idx] = 0.0

    def _obs(self):
        z = torch.zeros(self.N, self.D, device=self.dev)
        return torch.cat([self.dens, z if self.blind else self.friend], dim=1)

    def step(self, action):
        dev = self.dev; a = action.clamp(0, self.D - 1).unsqueeze(1)
        can = (self.sh > 0).float()
        hit_dens = self.dens.gather(1, a).squeeze(1) * can
        is_ff = self.friend.gather(1, a).squeeze(1) * can
        self.killed = self.killed + hit_dens * (1 - is_ff)
        self.ff = self.ff + is_ff
        self.sh = (self.sh - can).clamp(min=0)
        r = hit_dens * (1 - is_ff) * 3.0 - is_ff * 5.0 - 0.05                   # frapper dense OK, ami = catastrophe
        self.t += 1
        done = (self.sh <= 0) | (self.t >= self.max_steps)
        info = {"score": (self.killed / self.SH - self.ff).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info


class DefenseEnv:
    """DÉFENSE STATIQUE : masser le feu sur l'AXE de la poussée principale (qui se déplace vague après vague).
    Voit où pousse l'ennemi ; aveugle s'éparpille → percée. action=couvrir avenue k (0..3). métrique=`held`."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.D = 4; self.WAVES = 6; self.max_steps = 6
        self.obs_dim = self.D + 1
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("push", "blocked", "wave", "t"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.push[idx] = torch.randint(0, self.D, (n,), device=dev).float()
        self.blocked[idx] = 0.0; self.wave[idx] = 0.0; self.t[idx] = 0.0

    def _obs(self):
        oh = torch.zeros(self.N, self.D, device=self.dev)
        if not self.blind: oh.scatter_(1, self.push.long().unsqueeze(1), 1.0)
        return torch.cat([oh, (self.wave / self.WAVES).unsqueeze(1)], dim=1)

    def step(self, action):
        dev = self.dev
        block = (action == self.push.long()).float()                           # couvrir l'axe de poussée = bloque
        self.blocked = self.blocked + block
        r = block * 2.0 - (1 - block) * 0.5 - 0.03
        self.wave = self.wave + 1
        self.push = torch.randint(0, self.D, (self.N,), device=dev).float()     # la poussée se déplace
        self.t += 1
        done = (self.wave >= self.WAVES) | (self.t >= self.max_steps)
        info = {"held": (self.blocked / self.WAVES).clamp(0, 1)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info


class ConduiteEnv:
    """CONDUITE : rejoindre l'objectif en ÉVITANT les zones AT (kill-zones anti-véhicule). Voit les zones AT ;
    aveugle fonce dedans → détruit. action=déplacement 8 dir. métrique=`arrived`. Départ aléatoire (curriculum)."""
    def __init__(self, n, device, blind=False, seed=0):
        self.N = n; self.dev = device; self.blind = blind; self.max_steps = 45; self.speed = 7.0; self.field = 200.0
        self.D = 8; self.obs_dim = 7
        ang = [k * 2 * math.pi / self.D for k in range(self.D)]
        self.DX = torch.tensor([math.cos(a) for a in ang], device=device)
        self.DY = torch.tensor([math.sin(a) for a in ang], device=device)
        torch.manual_seed(seed); self._reset(torch.arange(n, device=device))

    def _reset(self, idx):
        n = idx.numel(); dev = self.dev
        for a in ("mx", "my", "ox", "oy", "ax", "ay", "alive", "t", "arr"):
            if not hasattr(self, a): setattr(self, a, torch.zeros(self.N, device=dev))
        self.mx[idx] = (torch.rand(n, device=dev) - 0.5) * 180
        self.my[idx] = (torch.rand(n, device=dev) - 0.5) * 180
        ac = torch.rand(n, device=dev) * 2 * math.pi
        self.ox[idx] = 110 * torch.cos(ac); self.oy[idx] = 110 * torch.sin(ac)  # objectif
        self.ax[idx] = 55 * torch.cos(ac) + (torch.rand(n, device=dev) - 0.5) * 50   # zone AT ~ sur le chemin
        self.ay[idx] = 55 * torch.sin(ac) + (torch.rand(n, device=dev) - 0.5) * 50
        self.alive[idx] = 1.0; self.t[idx] = 0.0; self.arr[idx] = 0.0

    def _obs(self):
        dox = self.ox - self.mx; doy = self.oy - self.my; do = torch.sqrt(dox ** 2 + doy ** 2 + 1e-6)
        dax = self.ax - self.mx; day = self.ay - self.my; da = torch.sqrt(dax ** 2 + day ** 2 + 1e-6)
        z = torch.zeros(self.N, device=self.dev)
        return torch.stack([dox / do, doy / do, (do / self.field).clamp(0, 1),
                            (dax / da) if not self.blind else z, (day / da) if not self.blind else z,
                            (da / self.field).clamp(0, 1) if not self.blind else z, self.alive], dim=1)

    def step(self, action):
        dev = self.dev
        do0 = torch.sqrt((self.ox - self.mx) ** 2 + (self.oy - self.my) ** 2 + 1e-6)
        mvi = action.clamp(0, self.D - 1)
        self.mx = self.mx + self.DX[mvi] * self.speed; self.my = self.my + self.DY[mvi] * self.speed
        do = torch.sqrt((self.ox - self.mx) ** 2 + (self.oy - self.my) ** 2 + 1e-6)
        da = torch.sqrt((self.ax - self.mx) ** 2 + (self.ay - self.my) ** 2 + 1e-6)
        in_at = (da < 32).float()
        hit = (torch.rand(self.N, device=dev) < in_at * 0.16)
        self.alive = self.alive * (~hit).float()
        self.arr = ((do < 18) & (self.alive > 0)).float()
        r = (do0 - do) * 0.06 + self.arr * 10.0 - hit.float() * 8.0 - 0.03
        self.t += 1
        done = (self.arr > 0) | (self.alive == 0) | (self.t >= self.max_steps)
        info = {"arrived": (self.arr > 0)}
        idx = torch.where(done)[0]
        if idx.numel() > 0: self._reset(idx)
        return self._obs(), r, done.float(), info
