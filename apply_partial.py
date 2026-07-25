P = "/home/younes/compose-embodiment/assault_partial.py"
src = open(P).read()

# 1. signature __init__ : ajoute les flags
a1 = "shell_obs=False, shellK=12, shell_R=60.0, suffer=False, D_min=2,"
assert a1 in src, "anchor 1 introuvable"
src = src.replace(a1, a1 + " partial=False, world_shell=False,", 1)

# 2. stocke les flags
a2 = "self.suffer = suffer; self.D_min = D_min"
assert a2 in src, "anchor 2 introuvable"
src = src.replace(a2, a2 + "; self.partial = partial; self.world_shell = world_shell", 1)

# 3. coque en repere MONDE si world_shell (ne pointe plus l'ennemi -> pas de fuite de direction)
a3 = "th0 = torch.atan2(by - self.apy, bx - self.apx)"
assert a3 in src, "anchor 3 introuvable"
src = src.replace(a3, "th0 = (torch.zeros_like(self.apx) if getattr(self, 'world_shell', False) else torch.atan2(by - self.apy, bx - self.apx))", 1)

# 4. masque la distance ennemie quand HORS-LOS (partial) -> il faut s'en souvenir
a4 = "nd = ed2.min(2).values.clamp(max=1e17).sqrt() / S"
assert a4 in src, "anchor 4 introuvable"
src = src.replace(a4, a4 + "\n        if getattr(self, 'partial', False): nd = torch.where(los > 0.5, nd, torch.ones_like(nd))", 1)

open(P, "w").write(src)
print("partial patch ok")
