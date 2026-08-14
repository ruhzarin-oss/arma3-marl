"""L agregat du gymnase (8 actions sur 10 240 decisions) melange 64 environnements et
60 pas. Arma, c est UN environnement sur 60 pas. On compare ce qui est comparable."""
import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
act_a = np.asarray(Z["actions"]).reshape(-1); pas = np.asarray(Z["pas"])
pol = charger(B.DEV)
SEQ = []
def rec(o, t):
    with torch.no_grad(): l, v = pol(o)
    a = l.argmax(-1)
    SEQ.append(a.cpu().numpy())          # (n_env, 4)
    return a, None, None
B.jouer(B.monde(64, 101), rec)
S = np.stack(SEQ)                        # (pas, env, 4)
print(f"  gymnase : {S.shape[0]} pas x {S.shape[1]} env x {S.shape[2]} hommes\n")

pe = np.array([len(np.unique(S[:, e, :])) for e in range(S.shape[1])])
ps = np.array([len(np.unique(S[t, e, :])) for e in range(S.shape[1]) for t in range(S.shape[0])])
chg = np.array([len(np.unique(S[:, e, :].reshape(-1, S.shape[2]), axis=0)) for e in range(S.shape[1])])

print("─── LE GYMNASE, PAR EPISODE (ce qui est comparable a Arma) ───")
print(f"  actions distinctes sur tout l episode  mediane {np.median(pe):.0f}   min {pe.min()}   max {pe.max()}")
print(f"  actions distinctes AU MEME PAS (4 hommes) mediane {np.median(ps):.0f}")
print(f"  episodes ou UNE SEULE action sort de bout en bout : {100*(pe==1).mean():.1f} %")

ta = len(np.unique(act_a))
print(f"\n─── ARMA ───")
print(f"  actions distinctes sur tout l episode : {ta}   (action {np.unique(act_a).tolist()})")
print(f"  l action change-t-elle au fil des 60 pas ? " + ("OUI" if len(np.unique([act_a[pas==p][0] for p in np.unique(pas)]))>1 else "NON, jamais"))

print("\n─── LA LECTURE ───")
if (pe == 1).mean() > 0.5:
    print(f"  ⇒ Le gymnase AUSSI sort une seule action dans {100*(pe==1).mean():.0f} % de ses episodes.")
    print("     Arma n a donc rien d anormal : mon « gel » n en etait pas un.")
else:
    print(f"  ⇒ Le gymnase varie ({np.median(pe):.0f} actions par episode en mediane, une seule dans")
    print(f"     {100*(pe==1).mean():.1f} % des cas). Arma en sort {ta} sur 60 pas : l ecart est REEL,")
    print("     et il n est plus explique ni par l observation ni par la scene.")
