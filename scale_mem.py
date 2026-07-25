import torch, torch.nn as nn
N, T, KVIS, H = 4096, 8, 1, 64   # menace visible seulement au pas 0 (KVIS=1)


class MLP(nn.Module):
    def __init__(self):
        super().__init__(); self.b = nn.Sequential(nn.Linear(1, H), nn.ReLU(), nn.Linear(H, H), nn.ReLU()); self.pi = nn.Linear(H, 2)
    def step(self, x, h):
        return self.pi(self.b(x)), h


class GRUN(nn.Module):
    def __init__(self):
        super().__init__(); self.g = nn.GRU(1, H, batch_first=True); self.pi = nn.Linear(H, 2)
    def step(self, x, h):
        o, h2 = self.g(x.unsqueeze(1), h); return self.pi(o.squeeze(1)), h2


def rollout(net, kind, train=True):
    s = (torch.randint(0, 2, (N,)) * 2 - 1).float()          # cote de la menace -1/+1
    h = torch.zeros(1, N, H) if kind == "gru" else None
    pos = torch.zeros(N); logps = []; ents = []
    for t in range(T):
        sig = s if t < KVIS else torch.zeros(N)              # menace montree au pas 0, puis CACHEE
        logits, h = net.step(sig.unsqueeze(-1), h)
        d = torch.distributions.Categorical(logits=logits)
        a = d.sample() if train else d.probs.argmax(-1)
        pos = pos + (a.float() * 2 - 1)                       # action 0->gauche, 1->droite
        logps.append(d.log_prob(a)); ents.append(d.entropy())
    safe = (torch.sign(pos) == -s).float()                   # bon = cote OPPOSE a la menace
    return safe, torch.stack(logps).sum(0), torch.stack(ents).mean()


def run(kind, iters=600):
    torch.manual_seed(0)
    net = GRUN() if kind == "gru" else MLP()
    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    for it in range(iters):
        safe, lp, ent = rollout(net, kind, train=True)
        rew = safe * 2 - 1
        loss = -(lp * (rew - rew.mean())).mean() - 0.01 * ent
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        safe, _, _ = rollout(net, kind, train=False)
    return 100 * safe.mean().item()


print("=== TOY MEMOIRE : menace au pas 0 puis cachee -> aller du cote OPPOSE ===", flush=True)
for kind in ["mlp", "gru"]:
    print(">>> %s : cote sur %.0f%%" % (kind.upper(), run(kind)), flush=True)
print("MEM FINI", flush=True)
