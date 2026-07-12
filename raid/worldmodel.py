#!/usr/bin/env python3
"""worldmodel.py — MODELE DU MONDE appris (HARMATTAN, #2, la BONNE version du surrogate).
Apprend la dynamique du raid A PARTIR DES ROLLOUTS ARMA reels (pas codee a la main) : etant donne
l'observation et les 20 actions a l'instant t, predit le pas t+1 (deplacement des SF, survie) + la recompense.
Tourne sur la 3090. But v1 : MESURER si la dynamique d'Arma est apprenable (erreur de prediction).
Si oui -> on pourra en faire un sim rapide pour pre-entrainer (sans le piege du surrogate code main)."""
import os, sys, time, glob, math
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F

ROLL = "/home/younes/maac_nuit/rollouts"
CKPT = "/home/younes/maac_nuit/worldmodel.pt"
N_SF = 20; N_SUBOBJ = 10; N_MATE = 19; F_SELF = 7; F_SUB = 5; F_MATE = 4
DEV = "cuda" if torch.cuda.is_available() else "cpu"

def load_transitions():
    """(ss,sb,sm,ac) a t -> (dpos, alive_next, reward) ; depuis tous les episodes dumpes."""
    SS, SB, SM, AC, DP, AN, RW = [], [], [], [], [], [], []
    for f in sorted(glob.glob(os.path.join(ROLL, "ep_*.npz"))):
        try: d = np.load(f)
        except Exception: continue
        ss, sb, sm, ac, rw = d["ss"], d["sb"], d["sm"], d["ac"], d["rw"]
        T = ss.shape[0]
        if T < 2: continue
        for t in range(T - 1):
            at = ac[t]; at = at[:, 0] if at.ndim > 1 else at      # nouveau format [N,2] -> on garde la destination
            SS.append(ss[t][:, :F_SELF]); SB.append(sb[t]); SM.append(sm[t]); AC.append(at)   # tronque obs a F_SELF (rollouts 7 et 8 mixtes)
            dp = ss[t + 1][:, :2] - ss[t][:, :2]                 # deplacement normalise (x,y)
            DP.append(dp); AN.append(ss[t + 1][:, 2]); RW.append(rw[t])
    if not SS: return None
    return (np.array(SS, np.float32), np.array(SB, np.float32), np.array(SM, np.float32),
            np.array(AC, np.int64), np.array(DP, np.float32), np.array(AN, np.float32), np.array(RW, np.float32))

class WorldModel(nn.Module):
    def __init__(self, d=96, heads=4):
        super().__init__()
        self.self_enc = nn.Sequential(nn.Linear(F_SELF, d), nn.ReLU(), nn.Linear(d, d))
        self.mate_enc = nn.Sequential(nn.Linear(F_MATE, d), nn.ReLU())
        self.attn = nn.MultiheadAttention(d, heads, batch_first=True)
        self.sub_enc = nn.Sequential(nn.Linear(F_SUB, d), nn.ReLU())
        self.act_emb = nn.Embedding(N_SUBOBJ + 1, d)     # 10 sous-obj + "tenir" (indice 10)
        self.head = nn.Sequential(nn.Linear(3 * d, d), nn.ReLU(), nn.Linear(d, 3))   # dx, dy, alive_logit
        self.rhead = nn.Sequential(nn.Linear(d, d), nn.ReLU(), nn.Linear(d, 1))      # recompense d'equipe
    def forward(self, ss, sb, sm, ac):
        B, N = ss.shape[:2]
        s = self.self_enc(ss)
        m = self.mate_enc(sm.reshape(B * N, N_MATE, F_MATE))
        att, _ = self.attn(s.reshape(B * N, 1, -1), m, m); att = att.reshape(B, N, -1)
        subc = self.sub_enc(sb).mean(2)                          # contexte objectifs [B,N,d]
        ae = self.act_emb(ac)                                    # [B,N,d]
        h = torch.cat([s + att, subc, ae], -1)                  # [B,N,3d]
        per = self.head(h)                                       # [B,N,3]
        r = self.rhead((s + att).mean(1)).squeeze(-1)            # [B]
        return per[..., :2], per[..., 2], r

def main():
    print("=== MODELE DU MONDE | device=%s ===" % DEV, flush=True)
    if DEV == "cuda": print("GPU:", torch.cuda.get_device_name(0), flush=True)
    net = WorldModel().to(DEV); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    cyc = 0
    while True:
        cyc += 1
        data = load_transitions()
        if data is None or len(data[0]) < 64:
            print("[cyc %d] donnees insuffisantes (%d transitions) - attente des rollouts Arma..." % (cyc, 0 if data is None else len(data[0])), flush=True)
            time.sleep(60); continue
        ss, sb, sm, ac, dp, an, rw = [torch.tensor(x).to(DEV) for x in data]
        S = ss.shape[0]; ntr = int(S * 0.9); idx = np.random.permutation(S)
        tr, va = idx[:ntr], idx[ntr:]
        for ep in range(60):                                    # passes sur les donnees courantes
            np.random.shuffle(tr)
            for i in range(0, len(tr), 256):
                b = tr[i:i + 256]
                pdp, pal, pr = net(ss[b], sb[b], sm[b], ac[b])
                loss = F.mse_loss(pdp, dp[b]) + 0.5 * F.binary_cross_entropy_with_logits(pal, an[b]) + 0.1 * F.mse_loss(pr, rw[b])
                opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad():
            pdp, pal, pr = net(ss[va], sb[va], sm[va], ac[va])
            pos_err = (pdp - dp[va]).pow(2).mean().sqrt().item() * 1000          # m (denormalise)
            alive_acc = ((pal > 0).float() == an[va]).float().mean().item()
            r_mae = (pr - rw[va]).abs().mean().item()
        torch.save(net.state_dict(), CKPT)
        print("[cyc %d] transitions=%d | err_pos=%.1f m | survie_acc=%.2f | reward_MAE=%.2f" % (
            cyc, S, pos_err, alive_acc, r_mae), flush=True)
        time.sleep(120)                                         # laisse les rollouts s'accumuler

if __name__ == "__main__":
    main()
