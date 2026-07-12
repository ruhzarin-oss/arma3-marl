"""Probe A — le sandbox GPU peut-il porter du terrain + pente/LOS/couvert en VECTORISE vite ?
Prototype torch : heightmap par env, pente (gradient), couvert (masque+distance), LOS (ray-march agent->ennemi
contre le relief). Batch B envs x A agents x E ennemis, chronometre sur la 3090."""
import torch, time
dev = "cuda:0"
B, H, W, A, E, K = 4096, 128, 128, 8, 8, 32
g = torch.Generator(device=dev).manual_seed(0)
# heightmap lisse par env (collines)
hm = torch.randn(B, H, W, generator=g, device=dev)
for _ in range(3):  # lissage -> relief continu
    hm = (hm + torch.roll(hm,1,1) + torch.roll(hm,-1,1) + torch.roll(hm,1,2) + torch.roll(hm,-1,2)) / 5
hm = (hm - hm.amin((1,2),keepdim=True)) * 30  # 0..~30 m
torch.cuda.synchronize()
# --- PENTE (gradient) ---
t0=time.time()
gy, gx = torch.gradient(hm, dim=(1,2)); slope = (gx*gx+gy*gy).sqrt()
torch.cuda.synchronize(); t_slope=time.time()-t0
# --- COUVERT (masque seuil pente + distance approx) ---
t0=time.time()
cover = (slope > slope.mean()).float()   # ex : pentes/crêtes = couvert
torch.cuda.synchronize(); t_cover=time.time()-t0
# --- LOS vectorise (agent -> ennemi, ray-march contre le relief) ---
ax=torch.randint(0,W,(B,A),generator=g,device=dev); ay=torch.randint(0,H,(B,A),generator=g,device=dev)
ex=torch.randint(0,W,(B,E),generator=g,device=dev); ey=torch.randint(0,H,(B,E),generator=g,device=dev)
ts=torch.linspace(0,1,K,device=dev)
t0=time.time()
lx=(ax[:,:,None,None]*(1-ts)+ex[:,None,:,None]*ts).long().clamp(0,W-1)
ly=(ay[:,:,None,None]*(1-ts)+ey[:,None,:,None]*ts).long().clamp(0,H-1)
idx=(ly*W+lx).view(B,-1)
terr=hm.view(B,-1).gather(1,idx).view(B,A,E,K)
ha=hm.view(B,-1).gather(1,(ay*W+ax)).view(B,A,1,1)
he=hm.view(B,-1).gather(1,(ey*W+ex)).view(B,1,E,1)
sight=ha*(1-ts)+he*ts+1.7
los_blocked=(terr>sight).any(-1)   # (B,A,E)
torch.cuda.synchronize(); t_los=time.time()-t0
tot=t_slope+t_cover+t_los
print("B=%d envs, A=%d agents, E=%d ennemis, heightmap %dx%d"%(B,A,W,H,W))
print("pente %.1fms | couvert %.1fms | LOS(B*A*E*K=%.1fM rays) %.1fms"%(t_slope*1e3,t_cover*1e3,B*A*E*K/1e6,t_los*1e3))
print("TOTAL %.1fms -> %.0f envs/s (perception terrain complete)"%(tot*1e3, B/tot))
print("LOS bloquees: %.0f%% | VRAM: %.1f Go"%(100*los_blocked.float().mean(),torch.cuda.max_memory_allocated()/1e9))
