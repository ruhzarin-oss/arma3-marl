"""sitrep — projection CARTE -> TEXTE (le maillon carte->Qwen). Fonction DETERMINISTE pure de la
FogCarte : replie la grille brouillard en quelques SECTEURS nommes (3x3 sandbox), chacun resume
(menace qualifiee + fraicheur + nos forces + objectif + TROU). Un LLM ne lit pas le tenseur ; il lit CA.
La reponse de Qwen (verbes fermes + prio) retombera en drv.focus. AUCUN entrainement, AUCUN reseau.
"""
import math
import torch

# 3x3 : (ligne y, colonne x) -> nom secteur (N=nord = y haut)
NAMES = {("hi", "lo"): "NO", ("hi", "mid"): "N ", ("hi", "hi"): "NE",
         ("mid", "lo"): "O ", ("mid", "mid"): "C ", ("mid", "hi"): "E ",
         ("lo", "lo"): "SO", ("lo", "mid"): "S ", ("lo", "hi"): "SE"}
ROWS = [("hi", ["lo", "mid", "hi"]), ("mid", ["lo", "mid", "hi"]), ("lo", ["lo", "mid", "hi"])]


def _bucket(v, R):
    return "lo" if v < -R / 3 else ("hi" if v > R / 3 else "mid")


def _qual_menace(m, thr):
    return "FORTE  " if m > 0.5 else "MOYENNE" if m > 0.2 else "FAIBLE " if m > thr else "—      "


def sitrep(env, e=0):
    """SITREP texte pour l'env e (une carte = une croyance d'equipe)."""
    c = env.carte; R = c.R; G = c.G; thr = c.thr
    T = -1.0 / math.log(c.aT)                                  # constante d'oubli (pas-haut)
    th = c.threat[e].reshape(-1); fr = c.fresh[e].reshape(-1)   # (G*G,)
    cpx = c.cellpx; cpy = c.cellpy
    bx = env.body.apx[e]; by = env.body.apy[e]; al = env.body._aalive()[e]  # nos forces
    secure_r = env.secure_r
    # buckets par cellule et par ami (vectorise simple)
    cbx = torch.where(cpx < -R / 3, 0, torch.where(cpx > R / 3, 2, 1))
    cby = torch.where(cpy < -R / 3, 0, torch.where(cpy > R / 3, 2, 1))
    abx = torch.where(bx < -R / 3, 0, torch.where(bx > R / 3, 2, 1))
    aby = torch.where(by < -R / 3, 0, torch.where(by > R / 3, 2, 1))
    BI = {"lo": 0, "mid": 1, "hi": 2}
    min_obj = torch.sqrt(bx ** 2 + by ** 2)[al].min().item() if al.any() else 9e9
    lines = []
    for yrow, xs in ROWS:
        for xcol in xs:
            iy = BI[yrow]; ix = BI[xcol]
            cell = (cby == iy) & (cbx == ix)
            m = th[cell].max().item() if cell.any() else 0.0
            f = fr[cell].max().item() if cell.any() else 0.0
            nm = int(((aby == iy) & (abx == ix) & al).sum().item())
            name = NAMES[(yrow, xcol)]
            # fraicheur
            if f > 0.6:
                fresh = "fraiche      "
            elif m > thr:
                age = -T * math.log(max(f, 1e-3))
                fresh = "vieille(%2.0fp)↑" % age
            else:
                fresh = "             "
            # objectif : l'objectif est en (0,0) -> secteur C
            obj = ""
            if name.strip() == "C":
                obj = "obj:TENU  " if min_obj < secure_r else "obj:OUVERT"
            trou = "  ⚠TROU" if (m <= thr and f < 0.05) else ""
            lines.append("  %s | menace:%s %s | nous:%d  %s%s"
                         % (name, _qual_menace(m, thr), fresh, nm, obj, trou))
    libres = int(al.sum().item())
    head = ("THEATRE SANDBOX (env %d) — t+%dp — nos forces:%d vivants  (oubli T=%.0fp)"
            % (e, int(env.t_hi[e].item()), libres, T))
    trous = [NAMES[(yr, xc)].strip() for yr, xs in ROWS for xc in xs
             if (lambda cell: (th[cell].max().item() if cell.any() else 0) <= thr
                 and (fr[cell].max().item() if cell.any() else 0) < 0.05)((cby == BI[yr]) & (cbx == BI[xc]))]
    return head + "\n" + "\n".join(lines) + "\n  TROUS (aveugles): " + (", ".join(trous) if trous else "aucun")


if __name__ == "__main__":
    import sys, torch.nn as nn
    sys.path.insert(0, "/home/younes/arma3-marl")
    from commander_env import CommanderEnv
    DEV = "cuda:0"; A, K, D = 8, 4, 8

    class CNet(nn.Module):
        def __init__(s, o, a, h=256):
            super().__init__(); s.body = nn.Sequential(nn.Linear(o, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
            s.mu = nn.Linear(h, a); s.v = nn.Linear(h, 1); s.log_std = nn.Parameter(torch.zeros(a) - 0.5)

        def forward(s, o): h = s.body(o); return s.mu(h), s.v(h).squeeze(-1)

    env = CommanderEnv(64, A=A, K=K, D=D, device=DEV, seed=5, max_steps=120, use_carte=True, carte_T=6.0)
    net = CNet(env.obs_dim, env.act_dim, 256).to(DEV)
    net.load_state_dict(torch.load("/home/younes/compose-embodiment/commander_carte_on.pt", map_location=DEV)); net.eval()
    obs = env.reset()
    print("=== SITREP au DEPART (le commandant ne sait encore rien) ===")
    print(sitrep(env, 0))
    with torch.no_grad():
        for _ in range(16):                                    # on laisse la mission ALLER AU CONTACT
            mu, _ = net(obs); obs, r, dn, info = env.step(mu.view(64, K, 2))
    mass = env.carte.threat.sum(dim=(1, 2))                    # on prend un env qui a VU l'ennemi
    e = int(mass.argmax().item())
    print("\n=== SITREP a mi-mission, env %d (le brouillard s'est rempli du SU) ===" % e)
    print(sitrep(env, e))
