#!/usr/bin/env python3
"""monde.py — LE MODÈLE DU MONDE, sur le corpus de la nuit.

Étape 3 de la liste cognitive : la PRÉDICTION. Le modèle regarde une tranche de combat et
apprend à deviner la suivante. C'est ce qui servira un jour de gymnase rapide à l'agent —
mille fois plus vite qu'Arma, et fidèle parce qu'appris SUR Arma.

CE QUI EST DÉJÀ MESURÉ ET QUI ORIENTE LA CONCEPTION
  · donner les entités à un modèle vaut +44,6 % de pouvoir prédictif  ⟨sonde 1⟩
  · les lire par ATTENTION bat l'addition de +6,1 %, et le contrôle passe (sur un seul
    ennemi, l'écart tombe à 0,0025)  ⟨sonde 1⟩
  · l'encodeur du RSSM actuel agrège par SOMME : c'est le verrou qu'on lève ici.
On entraîne donc les DEUX, sur les mêmes données et à budget de paramètres égal. Ce qui a
été vérifié sur « qui va mourir » ne l'a pas été sur « que devient le monde ».

CE QU'IL DOIT PRÉDIRE, à partir d'une tranche de 24 pas :
  · où sera chaque homme au pas suivant
  · s'il sera encore vivant
  · s'il tirera

CRITÈRES ÉCRITS AVANT DE REGARDER
  1. battre la PERSISTANCE — le modèle bête qui répond « rien ne change ». C'est le plancher
     honnête sur des positions : à 5 Hz, un homme bouge de moins de 3 m entre deux pas, et
     ne rien prédire du tout est déjà une bonne prédiction. Si on ne bat pas ça, on n'a rien.
  2. l'attention doit battre la somme d'au moins 3 % sur l'erreur de position.
  3. la tête de mort doit battre le taux de base (aire sous la courbe > 0,6).
  4. CONTRÔLE — sur des tranches TENUES À L'ÉCART par blocs de temps, jamais vues.
"""
import numpy as np, torch, torch.nn as nn, math, time, json, sys
from collections import defaultdict

D = '/mnt/data/corpus/tenseurs'
dev = 'cuda'; torch.cuda.set_device(0)
torch.backends.cuda.matmul.allow_tf32 = True
print(torch.cuda.get_device_name(0), flush=True)

X   = np.load(f'{D}/noeuds.npy', mmap_mode='r')     # (T, 577, 11)
P   = np.load(f'{D}/presence.npy', mmap_mode='r')
SPL = np.load(f'{D}/split.npy')
T, NP, NC = X.shape
print(f"corpus : {T} ticks", flush=True)

LEN = 24          # longueur d'une tranche
NE  = 32          # entités suivies par tranche
NFEN = 24000      # tranches échantillonnées

# ---------- construction des tranches ----------
# On suit des entités PRÉSENTES SUR TOUTE la tranche : le modèle doit prédire un mouvement,
# pas gérer des apparitions. Les apparitions sont un autre problème, et le mélanger ici
# masquerait l'essentiel.
print("construction des tranches", flush=True)
t0 = time.time()
rng = np.random.default_rng(11)
OBS = np.zeros((NFEN, LEN, NE, 8), np.float32)   # x,y,z,vivant,camp,tir,azimut,suppression
MSQ = np.zeros((NFEN, LEN, NE), np.float32)
SPT = np.zeros(NFEN, np.int8)
n = 0
essais = 0
while n < NFEN and essais < NFEN*8:
    essais += 1
    t = int(rng.integers(0, T-LEN-1))
    p0 = np.asarray(P[t]); x0 = np.asarray(X[t])
    ids0 = {int(x0[j,0]): j for j in range(NP) if p0[j] and x0[j,0] > 0}
    if len(ids0) < 8: continue
    pf = np.asarray(P[t+LEN]); xf = np.asarray(X[t+LEN])
    idsf = {int(xf[j,0]) for j in range(NP) if pf[j] and xf[j,0] > 0}
    communs = [i for i in ids0 if i in idsf]
    if len(communs) < 8: continue
    sel = rng.permutation(communs)[:NE]
    pos_ref = None
    for k in range(LEN):
        xt = np.asarray(X[t+k]); pt = np.asarray(P[t+k])
        idm = {int(xt[j,0]): j for j in range(NP) if pt[j] and xt[j,0] > 0}
        for a, uid in enumerate(sel):
            j = idm.get(int(uid))
            if j is None: continue
            OBS[n,k,a] = [xt[j,1], xt[j,2], xt[j,3], xt[j,4], xt[j,5], xt[j,6], xt[j,7], xt[j,9]]
            MSQ[n,k,a] = 1
        if k == 0:
            v = OBS[n,0,:,:2][MSQ[n,0]>0]
            pos_ref = v.mean(0) if len(v) else np.zeros(2, np.float32)
    # recentrage : le modèle apprend une dynamique locale, pas des coordonnées de Stratis
    OBS[n,:,:,0] -= pos_ref[0]; OBS[n,:,:,1] -= pos_ref[1]
    OBS[n,:,:,:2] *= MSQ[n][...,None]
    SPT[n] = SPL[t]
    n += 1
    if n % 4000 == 0: print(f"  {n} tranches   {time.time()-t0:.0f} s", flush=True)
OBS = OBS[:n]; MSQ = MSQ[:n]; SPT = SPT[:n]
print(f"  {n} tranches en {time.time()-t0:.0f} s   tenues à l'écart : {(SPT==1).mean():.0%}", flush=True)

# normalisation
OBS[...,0] /= 200.0; OBS[...,1] /= 200.0; OBS[...,2] /= 100.0; OBS[...,6] /= 360.0
tr = np.where(SPT==0)[0]; te = np.where(SPT==1)[0]
OBS_t = torch.tensor(OBS, device=dev); MSQ_t = torch.tensor(MSQ, device=dev)
print(f"  apprentissage {len(tr)}   écart {len(te)}   mémoire {OBS_t.numel()*4/1e9:.1f} Go", flush=True)

H, Z, G = 96, 32, 256

class Encodeur(nn.Module):
    """somme ou attention — c'est la SEULE différence entre les deux modèles"""
    def __init__(s, mode):
        super().__init__()
        s.mode = mode
        s.f = nn.Sequential(nn.Linear(8,H), nn.ReLU(), nn.Linear(H,H))
        if mode == 'attention':
            s.q = nn.Linear(G, H)
    def forward(s, obs, msk, h_prec):
        e = s.f(obs)                                  # (B, NE, H)
        if s.mode == 'somme':
            return (e*msk.unsqueeze(-1)).sum(1)/msk.sum(1,keepdim=True).clamp(min=1)
        a = (e * s.q(h_prec).unsqueeze(1)).sum(-1)/math.sqrt(H)
        a = torch.softmax(a.masked_fill(msk<0.5, -1e9), -1).unsqueeze(-1)
        return (e*a).sum(1)

class Monde(nn.Module):
    def __init__(s, mode):
        super().__init__()
        s.enc = Encodeur(mode)
        s.gru = nn.GRUCell(H+Z, G)
        s.prior = nn.Sequential(nn.Linear(G,H), nn.ReLU(), nn.Linear(H,2*Z))
        s.post  = nn.Sequential(nn.Linear(G+H,H), nn.ReLU(), nn.Linear(H,2*Z))
        # les têtes prédisent PAR ENTITÉ : on rend l'état à chacune
        s.tete = nn.Sequential(nn.Linear(G+Z+8,H), nn.ReLU(), nn.Linear(H,H), nn.ReLU())
        s.dpos = nn.Linear(H,2); s.dmort = nn.Linear(H,1); s.dtir = nn.Linear(H,1)
    def forward(s, obs, msk):
        B, L, NEnt, _ = obs.shape
        h = torch.zeros(B, G, device=obs.device)
        z = torch.zeros(B, Z, device=obs.device)
        pertes = dict(pos=0., mort=0., tir=0., kl=0.)
        for k in range(L-1):
            e = s.enc(obs[:,k], msk[:,k], h)
            h = s.gru(torch.cat([e, z], -1), h)
            mu_p, ls_p = s.prior(h).chunk(2,-1)
            mu_q, ls_q = s.post(torch.cat([h, e],-1)).chunk(2,-1)
            ls_p = ls_p.clamp(-4,2); ls_q = ls_q.clamp(-4,2)
            z = mu_q + torch.randn_like(mu_q)*ls_q.exp()
            kl = (ls_p - ls_q + (ls_q.exp()**2 + (mu_q-mu_p)**2)/(2*ls_p.exp()**2) - 0.5).sum(-1)
            pertes['kl'] = pertes['kl'] + kl.mean()
            ctx = torch.cat([h, z], -1).unsqueeze(1).expand(-1, NEnt, -1)
            y = s.tete(torch.cat([ctx, obs[:,k]], -1))
            m = msk[:,k+1] * msk[:,k]
            cible_d = (obs[:,k+1,:,:2] - obs[:,k,:,:2])
            pertes['pos'] = pertes['pos'] + (((s.dpos(y)-cible_d)**2).sum(-1)*m).sum()/m.sum().clamp(min=1)
            pertes['mort'] = pertes['mort'] + (nn.functional.binary_cross_entropy_with_logits(
                s.dmort(y).squeeze(-1), 1.0-obs[:,k+1,:,3], reduction='none')*m).sum()/m.sum().clamp(min=1)
            pertes['tir'] = pertes['tir'] + (nn.functional.binary_cross_entropy_with_logits(
                s.dtir(y).squeeze(-1), obs[:,k+1,:,5], reduction='none')*m).sum()/m.sum().clamp(min=1)
        return {k: v/(L-1) for k,v in pertes.items()}

    @torch.no_grad()
    def evaluer(s, obs, msk):
        B, L, NEnt, _ = obs.shape
        h = torch.zeros(B, G, device=obs.device); z = torch.zeros(B, Z, device=obs.device)
        err = 0.; err_pers = 0.; nm = 0.
        pm, ym = [], []
        for k in range(L-1):
            e = s.enc(obs[:,k], msk[:,k], h)
            h = s.gru(torch.cat([e, z], -1), h)
            mu_q, ls_q = s.post(torch.cat([h, e],-1)).chunk(2,-1)
            z = mu_q
            ctx = torch.cat([h, z], -1).unsqueeze(1).expand(-1, NEnt, -1)
            y = s.tete(torch.cat([ctx, obs[:,k]], -1))
            m = msk[:,k+1]*msk[:,k]
            d = (obs[:,k+1,:,:2]-obs[:,k,:,:2])
            err = err + (((s.dpos(y)-d)**2).sum(-1)*m).sum()
            err_pers = err_pers + ((d**2).sum(-1)*m).sum()      # « rien ne change »
            nm = nm + m.sum()
            pm.append((s.dmort(y).squeeze(-1)*m).flatten()); ym.append(((1.0-obs[:,k+1,:,3])*m).flatten())
        p = torch.cat(pm).cpu().numpy(); yv = torch.cat(ym).cpu().numpy()
        o = np.argsort(p); yv = yv[o]
        pos = yv.sum(); neg = len(yv)-pos
        auc = float((np.arange(1,len(yv)+1)[yv==1].sum() - pos*(pos+1)/2)/(pos*neg)) if pos>0 and neg>0 else float('nan')
        return float(err/nm), float(err_pers/nm), auc

def entrainer(mode, epoques=12, B=256):
    torch.manual_seed(7)
    m = Monde(mode).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=8e-4)
    npar = sum(x.numel() for x in m.parameters())
    for ep in range(epoques):
        perm = np.random.permutation(tr)
        tot = 0.; nb = 0
        for i in range(0, len(perm), B):
            k = torch.tensor(perm[i:i+B], device=dev)
            p = m(OBS_t[k], MSQ_t[k])
            # reconstruction SOMMÉE, poids KL bas ⟨régime différent de DreamerV3, mesuré en juillet⟩
            perte = p['pos']*30 + p['mort']*3 + p['tir'] + 0.05*p['kl']
            opt.zero_grad(); perte.backward()
            torch.nn.utils.clip_grad_norm_(m.parameters(), 100.)
            opt.step(); tot += float(perte); nb += 1
        if ep % 3 == 0 or ep == epoques-1:
            kt = torch.tensor(te[:3000], device=dev)
            e, ep_, auc = m.evaluer(OBS_t[kt], MSQ_t[kt])
            print(f"    {mode:9s} époque {ep:2d}  perte {tot/nb:7.3f}   erreur {e:.5f}"
                  f"  (persistance {ep_:.5f})   mort AUC {auc:.4f}", flush=True)
    kt = torch.tensor(te, device=dev)
    e, ep_, auc = m.evaluer(OBS_t[kt], MSQ_t[kt])
    return dict(mode=mode, err=e, err_pers=ep_, auc=auc, npar=npar), m

print("\n" + "="*74, flush=True)
res = {}
for mode in ('somme', 'attention'):
    print(f"\n### encodeur : {mode}", flush=True)
    t0 = time.time()
    r, m = entrainer(mode)
    r['secondes'] = time.time()-t0
    res[mode] = r
    torch.save(m.state_dict(), f'/mnt/data/corpus/monde_{mode}.pt')

print("\n" + "="*74)
print("RÉSULTATS — contre les critères écrits avant\n")
s, a = res['somme'], res['attention']
print(f"  {'':12s} {'erreur pos':>12s} {'persistance':>12s} {'gain':>8s} {'mort AUC':>10s} {'params':>9s}")
for k, r in res.items():
    g = (r['err_pers']-r['err'])/r['err_pers']
    print(f"  {k:12s} {r['err']:12.5f} {r['err_pers']:12.5f} {g:7.1%} {r['auc']:10.4f} {r['npar']:9d}")
print()
c1 = s['err'] < s['err_pers'] and a['err'] < a['err_pers']
print(f"  1. battre la persistance : {'PASSE' if c1 else 'ÉCHOUE'}")
gain_att = (s['err']-a['err'])/s['err']
c2 = gain_att >= 0.03
print(f"  2. l'attention bat la somme de {gain_att:+.1%} (seuil 3 %) : {'PASSE' if c2 else 'ÉCHOUE'}")
c3 = a['auc'] > 0.6
print(f"  3. la tête de mort dépasse 0,60 : {a['auc']:.4f} -> {'PASSE' if c3 else 'ÉCHOUE'}")
print()
if c1 and c2 and c3:
    print("  LE MODÈLE DU MONDE TIENT, ET L'ATTENTION Y GAGNE AUSSI.")
elif c1 and c3:
    print("  LE MODÈLE TIENT. Mais sur cette tâche, l'attention n'apporte pas —")
    print("  ce qui est un résultat : le gain mesuré sur « qui va mourir » ne se transporte pas ici.")
else:
    print("  PAS ENCORE — voir quel critère a lâché.")
json.dump(res, open('/mnt/data/corpus/monde.json','w'), indent=2)
