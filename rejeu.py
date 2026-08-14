"""rejeu — LES DEUX MACHOIRES ⟨Fable, 14/08⟩.

Un releve seul donne un INDICE. Le rejeu hors-ligne donne un VERDICT : il departage
d un coup les trois hypotheses — colonnes hors-plage, politique degeneree, decodage
d action.

CONTROLE POSITIF ⟨regle 16 clause 1⟩ : les observations du GYMNASE, passees dans le
MEME .pt, doivent produire des actions VARIEES. Si elles se figent aussi, la politique
est degeneree et les colonnes sont innocentes — et c est CA que le run dit, pas ce que
j esperais lire.
"""
import sys, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B

# ⚠️ LUS dans le docstring de arma_couture.py, PAS devines. Ma premiere passe affichait des
# noms inventes — le resultat etait positionnel donc juste, les etiquettes etaient fausses.
# Ordre declare (18) : [apx/S, apy/S, dgx, dgy, alive, slope, dcover, los, nd] + suffer2
# + team4 + [post_stand, post_crouch, post_prone]. COLS garde 0-8 et 15-17.
NOMS = ["apx/S", "apy/S", "dgx", "dgy", "alive", "slope", "dcover", "los", "nd",
        "post_debout", "post_accroupi", "post_couche"]

Z = np.load("/tmp/releve_live.npz", allow_pickle=True)
assert str(Z["statut"]) == "montage", "regle 17 : statut absent"
A18 = Z["obs18"]                     # (decisions, 18) — deja aplati
A = A18[:, COLS]
act_live = np.asarray(Z["actions"]).reshape(-1)
print(f"  releve d Arma : {len(A)} decisions sur {len(np.unique(Z['pas']))} pas")

pol_c = charger("cpu")
with torch.no_grad():
    lo, _ = pol_c(torch.tensor(A, dtype=torch.float32))
act_rej = lo.argmax(-1).numpy()

# ─── le gymnase : les obs que la politique a REELLEMENT vues
G, pol_g = [], charger(B.DEV)
def gele_rec(o, t):
    G.append(o.reshape(-1, o.shape[-1]).cpu().numpy())
    with torch.no_grad():
        l, v = pol_g(o)
    return l.argmax(-1), None, None
st, *_ = B.jouer(B.monde(64, 101), gele_rec)
G = np.concatenate(G)
with torch.no_grad():
    lg, _ = pol_g(torch.tensor(G, dtype=torch.float32, device=B.DEV))
act_gym = lg.argmax(-1).cpu().numpy()
print(f"  gymnase (graine 101, held-out) : {len(G)} decisions · prise {st['prise']:.1f} %\n")

def histo(a, nom):
    u, c = np.unique(a, return_counts=True)
    dom = 100.0 * c.max() / len(a)
    print(f"  {nom:<22} {dict(zip(u.tolist(), c.tolist()))}")
    print(f"  {'':<22} action dominante : {dom:.1f} %   actions distinctes : {len(u)}/10")
    return dom

print("─── LES ACTIONS ───")
d_gym  = histo(act_gym,  "GYMNASE")
d_rej  = histo(act_rej,  "ARMA rejoue hors-ligne")
d_live = histo(act_live, "ARMA en vif")

print("\n─── CONTROLE POSITIF : le gymnase fait-il varier la politique ? ───")
if d_gym > 80:
    print(f"  ⛔ TOMBE : le gymnase lui-meme se fige a {d_gym:.1f} %.")
    print("     La politique est degeneree ; les colonnes sont innocentes. RUN LU A L ENVERS.")
else:
    print(f"  ✓ PASSE : {d_gym:.1f} % de domination au gymnase. La politique SAIT varier.")

print("\n─── LA PLOMBERIE VIVE : vif == rejeu ? ───")
n = min(len(act_live), len(act_rej))
acc = 100.0 * (act_live[:n] == act_rej[:n]).mean()
print(f"  accord vif/rejeu : {acc:.1f} % sur {n} decisions")
print("  " + ("les memes obs donnent les memes actions : la plomberie est FIDELE."
      if acc > 99 else "⚠️ DESACCORD : obs livrees != obs relevees, ou decalage d index."))

print("\n─── LES COLONNES : Arma tombe-t-il dans la plage du gymnase ? ───")
print(f"  {'colonne':<10}{'gym 1%':>9}{'gym 50%':>9}{'gym 99%':>9}   {'arma 1%':>9}{'arma 50%':>9}{'arma 99%':>9}  verdict")
gl, gh = np.percentile(G, 1, axis=0), np.percentile(G, 99, axis=0)
hors = 0
for i, nm in enumerate(NOMS):
    g1, g50, g99 = np.percentile(G[:, i], [1, 50, 99])
    a1, a50, a99 = np.percentile(A[:, i], [1, 50, 99])
    v = "HORS PLAGE" if (a50 < g1 or a50 > g99) else ("bord" if (a1 < g1 or a99 > g99) else "ok")
    hors += (v == "HORS PLAGE")
    print(f"  {nm:<10}{g1:>9.3f}{g50:>9.3f}{g99:>9.3f}   {a1:>9.3f}{a50:>9.3f}{a99:>9.3f}  {v}")

conj = 100.0 * ((A < gl) | (A > gh)).any(1).mean()
print(f"\n  colonnes dont la MEDIANE Arma sort de la plage gymnase : {hors} sur 12")
print(f"  decisions Arma avec AU MOINS une colonne hors plage : {conj:.1f} %")
print("  ⚠️ 12 colonnes chacune « dans la plage » peuvent rester CONJOINTEMENT hors-distribution.")
