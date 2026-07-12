#!/usr/bin/env python3
# Mode SUFFER pour assault_terrain : gagnabilite VARIABLE (n defenseurs actifs par env),
# signal de DEBORDEMENT dans l'obs (degats recus + nb menacant), mort qui COUTE (discernement tenir/decrocher).
SRC = "assault_terrain.py"
s = open(SRC).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, "ancre n=%d : %s" % (s.count(a), a[:70])
    s = s.replace(a, b)


# 1) signature
rep("                 shell_obs=False, shellK=12, shell_R=60.0, device=\"cuda:0\", seed=0):",
    "                 shell_obs=False, shellK=12, shell_R=60.0, suffer=False, D_min=2, device=\"cuda:0\", seed=0):")

# 2) stockage
rep("        self.shell_obs = shell_obs; self.shellK = shellK; self.shell_R = shell_R",
    "        self.shell_obs = shell_obs; self.shellK = shellK; self.shell_R = shell_R\n"
    "        self.suffer = suffer; self.D_min = D_min")

# 3) obs_dim : +2 features de debordement
rep("+ ((shellK + 1) if shell_obs else 0)   # +grille +coequipiers +ROLE +COQUE",
    "+ ((shellK + 1) if shell_obs else 0) + (2 if suffer else 0)   # +grille +coequipiers +ROLE +COQUE +SUFFER")

# 4) init last_dmg_in
rep("            self.dsupp = torch.zeros(N, D, device=d); self.t = torch.zeros(N, dtype=torch.long, device=d)",
    "            self.dsupp = torch.zeros(N, D, device=d); self.t = torch.zeros(N, dtype=torch.long, device=d)\n"
    "            self.last_dmg_in = torch.zeros(N, self.A, device=d)")

# 5) gagnabilite variable : desactiver (pre-tuer) des defenseurs par env
rep("        self.ddmg[idx] = 0.0; self.dsupp[idx] = 0.0",
    "        self.ddmg[idx] = 0.0; self.dsupp[idx] = 0.0\n"
    "        if self.suffer:\n"
    "            nact = torch.randint(self.D_min, self.D + 1, (n,), device=d)         # nb defenseurs ACTIFS par env\n"
    "            deact = (torch.arange(self.D, device=d)[None] >= nact[:, None])       # True = desactive\n"
    "            self.ddmg[idx] = deact.float()                                        # desactives = deja neutralises")

# 6) prev_dk = fraction deja morte (sinon bonus parasite au 1er pas en suffer)
rep("        self._prev_dk[idx] = 0.0; self.last_supp[idx] = 0.0",
    "        self._prev_dk[idx] = (self.ddmg[idx] >= self.dmg_dead).float().sum(1) / self.D; self.last_supp[idx] = 0.0")

# 7) brancher les features de debordement dans _obs
rep("        if self.shell_obs: parts.append(self._cover_shell())",
    "        if self.shell_obs: parts.append(self._cover_shell())\n"
    "        if self.suffer: parts.append(self._suffer_feats())")

# 8) methode _suffer_feats (avant _cover_shell)
rep("    def _cover_shell(self):",
    "    def _suffer_feats(self):\n"
    "        \"\"\"Signal de DEBORDEMENT : degats recus au dernier pas + fraction de defenseurs qui PEUVENT me toucher\n"
    "        (vivant + portee + LOS). C'est ce qui permet de JUGER tenir(gagnable) vs decrocher(submerge).\"\"\"\n"
    "        N, A, D, d, S = self.N, self.A, self.D, self.dev, self.scale\n"
    "        nt = torch.zeros(N, A, device=d)\n"
    "        for di in range(D):\n"
    "            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)\n"
    "            los = TG.los_clear(self.hm, self.apx, self.apy, bx, by, S)\n"
    "            dist = torch.sqrt((self.apx - self.dpx[:, di:di + 1]) ** 2 + (self.apy - self.dpy[:, di:di + 1]) ** 2)\n"
    "            nt += self._dalive()[:, di:di + 1].float() * los * (dist < self.fire_range).float()\n"
    "        return torch.stack([(self.last_dmg_in * 5.0).clamp(max=1.0), nt / self.D], dim=2)   # (N,A,2)\n"
    "\n"
    "    def _cover_shell(self):")

# 9) memoriser les degats recus + MORT QUI COUTE (suffer)
rep("        self.admg = (self.admg + dmg_a * al).clamp(max=0.95)",
    "        self.last_dmg_in = (dmg_a * al).detach()\n"
    "        self.admg = (self.admg + dmg_a * al).clamp(max=0.95)")

rep("        self.prev_d = cur; self._prev_dk = dk",
    "        if self.suffer:\n"
    "            rew = rew - 1.1 * (wiped & ~neutralized).float()        # la mort COUTE (total -1.5) -> decrocher le perdu devient rationnel\n"
    "        self.prev_d = cur; self._prev_dk = dk")

open(SRC, "w").write(s)
print("PATCH suffer OK")
