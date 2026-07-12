#!/usr/bin/env python3
# FIX : ecarter les DEFENSEURS des murs en mode replique (sinon ils spawnent dans un batiment = intouchables = 0% force).
s = open("assault_terrain.py").read()
A = '        self.dpx[idx] = 12.0 * torch.cos(dang)[None]; self.dpy[idx] = 12.0 * torch.sin(dang)[None]'
assert s.count(A) == 1, "ancre defenseurs introuvable"
B = (A + "\n"
     "        if self.replica:\n"
     "            for _ in range(20):\n"
     "                _dw = self._sample_solid(self.dpx[idx], self.dpy[idx]) > 0.5\n"
     "                if not bool(_dw.any()): break\n"
     "                _jx = (torch.rand_like(self.dpx[idx]) * 2 - 1) * 10.0\n"
     "                _jy = (torch.rand_like(self.dpy[idx]) * 2 - 1) * 10.0\n"
     "                self.dpx[idx] = torch.where(_dw, (self.dpx[idx] + _jx).clamp(-self.terr_R * 0.95, self.terr_R * 0.95), self.dpx[idx])\n"
     "                self.dpy[idx] = torch.where(_dw, (self.dpy[idx] + _jy).clamp(-self.terr_R * 0.95, self.terr_R * 0.95), self.dpy[idx])")
open("assault_terrain.py", "w").write(s.replace(A, B))
print("PATCH defnudge OK")
