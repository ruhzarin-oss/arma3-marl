#!/usr/bin/env python3
# Ajoute une COQUE DE COUVERT (12 rayons centres sur la menace) a assault_terrain,
# pour entrainer une politique sur l'obs de l'avatar Arma. Opt-in (shell_obs), reste inchange sinon.
SRC = "assault_terrain.py"
s = open(SRC).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, "ancre n=%d : %s" % (s.count(a), a[:70])
    s = s.replace(a, b)


# 1) signature : params shell
rep("                 grid_obs=False, gridK=8, gridspan=80.0, team_obs=False, role_obs=False, device=\"cuda:0\", seed=0):",
    "                 grid_obs=False, gridK=8, gridspan=80.0, team_obs=False, role_obs=False,\n"
    "                 shell_obs=False, shellK=12, shell_R=60.0, device=\"cuda:0\", seed=0):")

# 2) stockage des flags shell
rep("        self.grid_obs = grid_obs; self.gridK = gridK; self.gridspan = gridspan; self.team_obs = team_obs; self.role_obs = role_obs",
    "        self.grid_obs = grid_obs; self.gridK = gridK; self.gridspan = gridspan; self.team_obs = team_obs; self.role_obs = role_obs\n"
    "        self.shell_obs = shell_obs; self.shellK = shellK; self.shell_R = shell_R")

# 3) obs_dim : + (shellK distances + 1 proprio degats)
rep("        self.obs_dim = 9 + (2 * gridK * gridK if grid_obs else 0) + (4 if team_obs else 0) + (2 if role_obs else 0)   # +grille +coequipiers +ROLE (officier)",
    "        self.obs_dim = 9 + (2 * gridK * gridK if grid_obs else 0) + (4 if team_obs else 0) + (2 if role_obs else 0) + ((shellK + 1) if shell_obs else 0)   # +grille +coequipiers +ROLE +COQUE")

# 4) brancher la coque dans _obs (apres la grille/team/role)
rep("        if self.grid_obs: parts.append(self._local_grid())",
    "        if self.shell_obs: parts.append(self._cover_shell())\n"
    "        if self.grid_obs: parts.append(self._local_grid())")

# 5) methode _cover_shell (avant _local_grid)
rep("    def _local_grid(self):",
    "    def _cover_shell(self):\n"
    "        \"\"\"COQUE DE COUVERT : K rayons ray-marches dans le champ de couvert, centres sur la MENACE\n"
    "        (rayon 0 = vers l'ennemi le + proche, sens horaire). Distance au 1er couvert / portee. = l'obs de l'avatar Arma.\"\"\"\n"
    "        N, A, K, d, S = self.N, self.A, self.shellK, self.dev, self.scale\n"
    "        R, steps = self.shell_R, 20\n"
    "        ex = self.dpx.unsqueeze(1) - self.apx.unsqueeze(2); ey = self.dpy.unsqueeze(1) - self.apy.unsqueeze(2)\n"
    "        BIG = torch.tensor(1e18, device=d)\n"
    "        ed2 = torch.where(self._dalive().unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)\n"
    "        bx = torch.gather(self.dpx, 1, km); by = torch.gather(self.dpy, 1, km)\n"
    "        th0 = torch.atan2(by - self.apy, bx - self.apx)                       # cap vers la menace (N,A)\n"
    "        offs = torch.arange(K, device=d).float() * (2 * math.pi / K)\n"
    "        ang = th0.unsqueeze(-1) + offs                                        # (N,A,K)\n"
    "        cs = ang.cos(); sn = ang.sin()\n"
    "        stp = (torch.arange(1, steps + 1, device=d).float() / steps) * R      # (steps,)\n"
    "        sx = (self.apx[..., None, None] + cs[..., None] * stp).reshape(N, A * K * steps)\n"
    "        sy = (self.apy[..., None, None] + sn[..., None] * stp).reshape(N, A * K * steps)\n"
    "        cov = TG.sample(self.cover, sx, sy, S).reshape(N, A, K, steps)\n"
    "        hit = cov > 0.5; anyh = hit.any(-1)\n"
    "        first = hit.float().argmax(-1).float()                               # 1er pas touche (0 si aucun)\n"
    "        dist = torch.where(anyh, (first + 1) / steps * R, torch.full_like(first, R)) / R\n"
    "        return torch.cat([dist, self.admg.unsqueeze(-1)], dim=2)             # (N,A,K+1) : coque + degats\n"
    "\n"
    "    def _local_grid(self):")

open(SRC, "w").write(s)
print("PATCH assault_terrain (coque) OK")
