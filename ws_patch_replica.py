#!/usr/bin/env python3
# Mode REPLICA pour assault_terrain : terrain = vraie zone Arma (replica.npz), batiments SOLIDES
# qui BLOQUENT le mouvement (collision) ET la LOS (couvert reel). Opt-in, le reste inchange.
SRC = "assault_terrain.py"
s = open(SRC).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, "ancre n=%d : %s" % (s.count(a), a[:70])
    s = s.replace(a, b)


# 0) import numpy
rep("import terrain_gpu as TG\n",
    "import terrain_gpu as TG\nimport numpy as np\n")

# 1) signature
rep("                 shell_obs=False, shellK=12, shell_R=60.0, suffer=False, D_min=2, device=\"cuda:0\", seed=0):",
    "                 shell_obs=False, shellK=12, shell_R=60.0, suffer=False, D_min=2,\n"
    "                 replica=False, replica_path=\"replica.npz\", device=\"cuda:0\", seed=0):")

# 2) chargement replica + override des parametres terrain (AVANT _reset)
rep("        self.max_steps = max_steps; self.dmg_dead = dmg_dead; self.dev = device; self.scale = terr_R",
    "        self.max_steps = max_steps; self.dmg_dead = dmg_dead; self.dev = device; self.scale = terr_R\n"
    "        self.replica = replica\n"
    "        if replica:\n"
    "            _R = np.load(replica_path)\n"
    "            self._solid = torch.tensor(_R[\"solid\"].astype(\"float32\"), device=device)\n"
    "            self._elevR = torch.tensor(_R[\"elev\"].astype(\"float32\"), device=device)\n"
    "            self.terr_G = int(_R[\"GS\"]); self.terr_R = float(_R[\"W\"]); self.scale = self.terr_R\n"
    "            self.R_spawn = min(R_spawn, self.terr_R - 25.0)\n")

# 3) _reset : terrain = replica (sinon genere)
rep("        T = TG.gen_terrain(n, self.terr_G, d, self.g, relief=self.relief)\n"
    "        for nm in (\"hm\", \"slope\", \"cover\", \"dcover\"):\n"
    "            getattr(self, nm)[idx] = T[nm]",
    "        if self.replica:\n"
    "            self.hm[idx] = self._elevR; self.cover[idx] = self._solid\n"
    "            self.slope[idx] = 0.0; self.dcover[idx] = 0.0\n"
    "        else:\n"
    "            T = TG.gen_terrain(n, self.terr_G, d, self.g, relief=self.relief)\n"
    "            for nm in (\"hm\", \"slope\", \"cover\", \"dcover\"):\n"
    "                getattr(self, nm)[idx] = T[nm]")

# 4) ecarter les spawns attaquants des murs (sinon coinces)
rep("        self.apx[idx] = sx[:, None] + (ar % 2) * 6 - 3; self.apy[idx] = sy[:, None] + (ar - 1) * 6; self.admg[idx] = 0.0",
    "        self.apx[idx] = sx[:, None] + (ar % 2) * 6 - 3; self.apy[idx] = sy[:, None] + (ar - 1) * 6; self.admg[idx] = 0.0\n"
    "        if self.replica:\n"
    "            for _ in range(10):\n"
    "                _w = self._sample_solid(self.apx[idx], self.apy[idx]) > 0.5\n"
    "                if not bool(_w.any()): break\n"
    "                self.apx[idx] = torch.where(_w, self.apx[idx] * 0.92, self.apx[idx])\n"
    "                self.apy[idx] = torch.where(_w, self.apy[idx] * 0.92, self.apy[idx])")

# 5) methodes : echantillonnage du solide + LOS solide-aware (avant _obs)
rep("    def _obs(self):",
    "    def _sample_solid(self, px, py):\n"
    "        G = self.terr_G\n"
    "        gx = ((px / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()\n"
    "        gy = ((py / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()\n"
    "        return self._solid[gy, gx]\n"
    "\n"
    "    def _losc(self, hm, ax, ay, bx, by, R):\n"
    "        base = TG.los_clear(hm, ax, ay, bx, by, R)\n"
    "        if not getattr(self, \"replica\", False):\n"
    "            return base\n"
    "        K = 24\n"
    "        t = torch.linspace(0.0, 1.0, K, device=self.dev)\n"
    "        pxr = ax.unsqueeze(-1) * (1 - t) + bx.unsqueeze(-1) * t\n"
    "        pyr = ay.unsqueeze(-1) * (1 - t) + by.unsqueeze(-1) * t\n"
    "        blocked = (self._sample_solid(pxr, pyr) > 0.5).any(-1)\n"
    "        return base * (~blocked).float()\n"
    "\n"
    "    def _obs(self):")

# 6) brancher la LOS solide partout (3 sites : obs, feu defenseurs, suppress attaquants)
s = s.replace("TG.los_clear(self.hm, ", "self._losc(self.hm, ")
assert "self._losc(self.hm, " in s

# 7) collision mouvement dans step
rep("        self.apx = (self.apx + torch.sin(th) * spd * al).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)\n"
    "        self.apy = (self.apy + torch.cos(th) * spd * al).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)",
    "        _oax = self.apx.clone(); _oay = self.apy.clone()\n"
    "        self.apx = (self.apx + torch.sin(th) * spd * al).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)\n"
    "        self.apy = (self.apy + torch.cos(th) * spd * al).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)\n"
    "        if self.replica:\n"
    "            _wall = self._sample_solid(self.apx, self.apy) > 0.5\n"
    "            self.apx = torch.where(_wall, _oax, self.apx); self.apy = torch.where(_wall, _oay, self.apy)")

open(SRC, "w").write(s)
print("PATCH replica OK")
