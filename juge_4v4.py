import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
NOMS = ["apx/S","apy/S","dgx","dgy","alive","slope","dcover","los","nd","p_deb","p_acc","p_cou"]
Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
A = Z["obs18"][:, COLS].astype(np.float64); pas = np.asarray(Z["pas"])
act = np.asarray(Z["actions"]).reshape(-1)
G, pol = [], charger(B.DEV)
def rec(o, t):
    G.append(o.reshape(-1, o.shape[-1]).cpu().numpy())
    with torch.no_grad(): l, v = pol(o); return l.argmax(-1), None, None
st, *_ = B.jouer(B.monde(64, 101), rec)
G = np.concatenate(G).astype(np.float64)
with torch.no_grad():
    ag = pol(torch.tensor(G, dtype=torch.float32, device=B.DEV))[0].argmax(-1).cpu().numpy()

print(f"  Arma {len(A)} decisions sur {len(np.unique(pas))} pas  ·  gymnase {len(G)} decisions, prise {st['prise']:.1f} %\n")
print("─── LA PORTE : les 12 colonnes RESTENT-elles dans la plage ? ───")
gl, gh = np.percentile(G,1,axis=0), np.percentile(G,99,axis=0)
hors = []
for i,n in enumerate(NOMS):
    a50 = np.percentile(A[:,i],50)
    if a50 < gl[i] or a50 > gh[i]: hors.append(f"{n} ({a50:.3f} hors [{gl[i]:.3f};{gh[i]:.3f}])")
conj = 100*((A<gl)|(A>gh)).any(1).mean()
print(f"  colonnes hors plage : {len(hors)}/12" + ("" if not hors else "  → " + ", ".join(hors)))
print(f"  decisions avec au moins une colonne hors plage : {conj:.1f} %")
print("  " + ("✓ PASSE — les colonnes tiennent" if len(hors)==0 else "⛔ TOMBE — passer a 4v4 en a fait sortir"))

print("\n─── RAPPORTE, NON JUGE ───")
u,c = np.unique(act, return_counts=True); ug,cg = np.unique(ag, return_counts=True)
print(f"  GYMNASE  {dict(zip(ug.tolist(),cg.tolist()))}")
print(f"           dominante {100*cg.max()/len(ag):.1f} %  ·  {len(ug)}/10 actions")
print(f"  ARMA     {dict(zip(u.tolist(),c.tolist()))}")
print(f"           dominante {100*c.max()/len(act):.1f} %  ·  {len(u)}/10 actions")
print(f"  survie   {len(np.unique(pas))} pas   (etait 14-17 a 8 contre 13)")
print("\n  ⚠️ UN SEUL EPISODE. Aucun verdict de concordance sans repetitions.")
