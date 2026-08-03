"""sirocco_patho — LES QUATRE PATHOLOGIES. Brique ISOLEE, rien n'est branche.

Un systeme immunitaire mal regle ne fait pas "moins bien". Il tue son hote. Ces quatre
compteurs entrent dans le banc AVANT les donnees, pas apres — un gain avec un compteur dans
le rouge est un ECHEC, pas un compromis.

  ANERGIE               seuils trop hauts : l'agent encaisse sans reagir.
                        Compteur : delai entre le 1er signal et la 1re reaction.
                        C'est l'ETAT ACTUEL, avant tout SIROCCO. C'est la ligne de base.

  AUTO-IMMUNITE         reaction sur signal ami : fratricide.
                        Compteur : part des tirs ou un ami est dans l'arc.

  CHOC CYTOKINIQUE      tout le monde repond au meme signal -> blob.
                        Compteur : dispersion de l'escouade quand le champ monte, rapportee
                        a sa dispersion au calme. Sous 1, l'escouade s'agglutine.
                        RISQUE N.1 : le blob a 150 agents est deja mesure chez toi.

  INFLAMMATION CHRONIQUE  jamais de resolution, plus personne n'avance.
                        Compteur : part du temps en etage >= 2 sans gain vers l'objectif.

smoke : python sirocco_patho.py smoke
"""
import math
import sys
import torch

from sirocco_cascade import REFLEXE, LOCAL

# Seuils PRE-ENREGISTRES. A figer AVANT le run, jamais ajustes apres coup.
# Ce sont des valeurs de depart discutables — ce qui ne l'est pas, c'est qu'elles soient
# ecrites avant de voir les donnees.
SEUILS = {
    "anergie_s": 2.0,          # reagir en moins de 2 s apres le 1er signal
    "auto_immun": 0.02,        # moins de 2 % des tirs avec un ami dans l'arc
    "dispersion_min": 0.85,    # l'escouade ne se resserre pas de plus de 15 % sous le feu
    "chronique_max": 0.30,     # moins de 30 % du temps inflamme sans progresser
}


class Pathologies:
    def __init__(self, N, A, device, sec_par_pas=None):
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError("sec_par_pas manquant (les delais se rendent en SECONDES).")
        self.N, self.A, self.dev, self.spp = int(N), int(A), device, float(sec_par_pas)
        z = lambda: torch.zeros(self.N, device=device)                          # noqa: E731
        self.t = 0
        self.t_signal = torch.full((self.N,), -1.0, device=device)   # pas du 1er danger
        self.t_reaction = torch.full((self.N,), -1.0, device=device)  # pas de la 1re reaction
        self.tirs = 0; self.tirs_amis = 0
        self.disp_chaud = z(); self.n_chaud = z()
        self.disp_froid = z(); self.n_froid = z()
        self.pas_inflam = z(); self.pas_inflam_sterile = z()
        self.meilleure_dist = torch.full((self.N,), float("inf"), device=device)

    @torch.no_grad()
    def observer(self, danger, etat, px, py, vivant=None, charge=None, dist_obj=None,
                 seuil_danger=0.05, seuil_charge=1.0):
        """Un pas d'observation. Aucun effet sur le systeme : on regarde, on ne corrige pas."""
        N, A, dev = self.N, self.A, self.dev
        vivant = torch.ones(N, A, dtype=torch.bool, device=dev) if vivant is None else vivant.bool()
        self.t += 1

        # --- ANERGIE : premier signal, puis premiere reaction ---
        a_signal = ((danger >= seuil_danger) & vivant).any(1)
        self.t_signal = torch.where((self.t_signal < 0) & a_signal,
                                    torch.full_like(self.t_signal, float(self.t)), self.t_signal)
        a_reagi = ((etat >= REFLEXE) & (etat <= LOCAL) & vivant).any(1)
        self.t_reaction = torch.where((self.t_reaction < 0) & a_reagi & (self.t_signal >= 0),
                                      torch.full_like(self.t_reaction, float(self.t)), self.t_reaction)

        # --- CHOC CYTOKINIQUE : la dispersion, chaud contre froid ---
        v = vivant.float(); nv = v.sum(1).clamp(min=1.0)
        cx = (px * v).sum(1) / nv; cy = (py * v).sum(1) / nv
        d2 = ((px - cx.unsqueeze(1)) ** 2 + (py - cy.unsqueeze(1)) ** 2) * v
        disp = torch.sqrt(d2.sum(1) / nv)                                     # rayon quadratique
        assez = vivant.sum(1) >= 2
        chaud = (charge >= seuil_charge) if charge is not None else (danger.max(1).values >= seuil_danger)
        m_chaud = chaud & assez; m_froid = (~chaud) & assez
        self.disp_chaud += disp * m_chaud.float(); self.n_chaud += m_chaud.float()
        self.disp_froid += disp * m_froid.float(); self.n_froid += m_froid.float()

        # --- INFLAMMATION CHRONIQUE : inflamme et n'avance pas ---
        inflam = ((etat >= LOCAL) & vivant).any(1)
        self.pas_inflam += inflam.float()
        if dist_obj is not None:
            gagne = dist_obj < self.meilleure_dist - 1.0
            self.meilleure_dist = torch.minimum(self.meilleure_dist, dist_obj)
            self.pas_inflam_sterile += (inflam & ~gagne).float()

    @torch.no_grad()
    def observer_tir(self, px, py, cap, tire, vivant=None, arc=0.12, portee=200.0):
        """AUTO-IMMUNITE. `cap` (N,A,2) direction de tir unitaire, `tire` (N,A) bool.
        Un tir est fratricide en puissance si un AMI vivant est dans le cone `arc` (rad) et
        a moins de `portee`. On ne demande pas au moteur qui a ete touche : on compte le
        GESTE, parce que c'est lui qu'on veut apprendre a ne pas faire."""
        N, A, dev = self.N, self.A, self.dev
        vivant = torch.ones(N, A, dtype=torch.bool, device=dev) if vivant is None else vivant.bool()
        tire = tire.bool() & vivant
        dx = px.unsqueeze(1) - px.unsqueeze(2); dy = py.unsqueeze(1) - py.unsqueeze(2)   # j vu de i
        d = torch.sqrt(dx * dx + dy * dy).clamp(min=1e-6)
        ux = dx / d; uy = dy / d
        cos = ux * cap[..., 0].unsqueeze(2) + uy * cap[..., 1].unsqueeze(2)
        eye = torch.eye(A, dtype=torch.bool, device=dev).unsqueeze(0)
        dans_arc = (cos >= math.cos(arc)) & (d <= portee) & vivant.unsqueeze(1) & ~eye
        self.tirs += int(tire.sum())
        self.tirs_amis += int((tire & dans_arc.any(2)).sum())

    def rapport(self):
        d = self.t_reaction - self.t_signal
        vus = (self.t_signal >= 0) & (self.t_reaction >= 0)
        jamais = int(((self.t_signal >= 0) & (self.t_reaction < 0)).sum())
        anergie = float(d[vus].mean()) * self.spp if int(vus.sum()) else float("nan")
        dc = float((self.disp_chaud.sum() / self.n_chaud.sum().clamp(min=1)))
        df = float((self.disp_froid.sum() / self.n_froid.sum().clamp(min=1)))
        return {
            "anergie_s": anergie,
            "jamais_reagi": jamais,
            "auto_immun": (self.tirs_amis / self.tirs) if self.tirs else 0.0,
            "tirs": self.tirs,
            "dispersion_ratio": (dc / df) if df > 1e-6 else float("nan"),
            "dispersion_chaud_m": dc, "dispersion_froid_m": df,
            "chronique": float(self.pas_inflam_sterile.sum() / self.pas_inflam.sum().clamp(min=1))
            if float(self.pas_inflam.sum()) > 0 else 0.0,
        }

    def verdict(self, seuils=None):
        """Rend (passe, lignes). Un seul compteur dans le rouge suffit a faire echouer."""
        s = dict(SEUILS); s.update(seuils or {})
        r = self.rapport(); lignes = []; passe = True

        def test(nom, val, cond, attendu):
            nonlocal passe
            bon = bool(cond)
            passe = passe and bon
            lignes.append("  %-22s %-10s %s (attendu %s)"
                          % (nom, ("%.3f" % val) if val == val else "n/a",
                             "OK " if bon else "ROUGE", attendu))

        test("anergie (s)", r["anergie_s"],
             (r["anergie_s"] != r["anergie_s"]) or r["anergie_s"] <= s["anergie_s"],
             "<= %.1f" % s["anergie_s"])
        test("auto-immunite", r["auto_immun"], r["auto_immun"] <= s["auto_immun"],
             "<= %.3f" % s["auto_immun"])
        test("dispersion (chaud/froid)", r["dispersion_ratio"],
             (r["dispersion_ratio"] != r["dispersion_ratio"]) or r["dispersion_ratio"] >= s["dispersion_min"],
             ">= %.2f" % s["dispersion_min"])
        test("inflam. chronique", r["chronique"], r["chronique"] <= s["chronique_max"],
             "<= %.2f" % s["chronique_max"])
        if r["jamais_reagi"]:
            lignes.append("  %-22s %-10d %s" % ("jamais reagi (envs)", r["jamais_reagi"], "ROUGE"))
            passe = False
        return passe, "\n".join(lignes)


# ---- smoke ------------------------------------------------------------------------------
def _smoke():
    from sirocco import device_defaut
    dev = device_defaut()
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== sirocco_patho : smoke isole (device %s) ===" % dev, flush=True)
    SPP = 0.7; N, A = 2, 4

    # 1. ANERGIE : un agent qui reagit vite vs un agent qui n'a jamais reagi
    p = Pathologies(N, A, dev, sec_par_pas=SPP)
    px = torch.linspace(0, 30, A, device=dev).view(1, A).expand(N, A).contiguous()
    py = torch.zeros(N, A, device=dev)
    d = torch.zeros(N, A, device=dev); d[:, 0] = 0.9
    e = torch.zeros(N, A, dtype=torch.long, device=dev)
    p.observer(d, e, px, py)                       # signal, pas de reaction
    p.observer(d, e, px, py)
    e[:, 0] = REFLEXE
    p.observer(d, e, px, py)                       # reaction au 3e pas
    r = p.rapport()
    dire("anergie mesuree en secondes", abs(r["anergie_s"] - 2 * SPP) < 1e-6,
         "%.2f s" % r["anergie_s"])

    p2 = Pathologies(N, A, dev, sec_par_pas=SPP)
    for _ in range(5): p2.observer(d, torch.zeros(N, A, dtype=torch.long, device=dev), px, py)
    passe, txt = p2.verdict()
    dire("n'a jamais reagi -> verdict ROUGE", not passe)

    # 2. AUTO-IMMUNITE : tirer vers un ami est compte, tirer a l'oppose ne l'est pas
    p3 = Pathologies(N, A, dev, sec_par_pas=SPP)
    cap = torch.zeros(N, A, 2, device=dev); cap[..., 0] = 1.0     # tous tirent vers l'est
    tire = torch.zeros(N, A, dtype=torch.bool, device=dev); tire[:, 0] = True   # l'agent 0 est a l'ouest
    p3.observer_tir(px, py, cap, tire)
    dire("tir vers un ami : compte", p3.rapport()["auto_immun"] == 1.0)
    cap[..., 0] = -1.0                                            # maintenant il tire a l'oppose
    p4 = Pathologies(N, A, dev, sec_par_pas=SPP)
    p4.observer_tir(px, py, cap, tire)
    dire("tir a l'oppose : pas compte", p4.rapport()["auto_immun"] == 0.0)

    # 3. CHOC CYTOKINIQUE : une escouade qui converge sous le feu est detectee
    def scenario(converge):
        pp = Pathologies(N, A, dev, sec_par_pas=SPP)
        for t in range(20):
            chaud = t >= 10
            ecart = 30.0 * (0.2 if (chaud and converge) else 1.0)
            x = torch.linspace(-ecart, ecart, A, device=dev).view(1, A).expand(N, A).contiguous()
            y = torch.zeros(N, A, device=dev)
            ch = torch.full((N,), 5.0 if chaud else 0.0, device=dev)
            pp.observer(torch.zeros(N, A, device=dev), torch.zeros(N, A, dtype=torch.long, device=dev),
                        x, y, charge=ch)
        return pp.rapport()["dispersion_ratio"]

    rc = scenario(True); rn = scenario(False)
    dire("blob detecte (dispersion s'effondre)", rc < 0.5, "ratio %.2f" % rc)
    dire("pas de faux positif si l'escouade tient", abs(rn - 1.0) < 0.05, "ratio %.2f" % rn)

    # 4. INFLAMMATION CHRONIQUE : inflamme et bloque
    p5 = Pathologies(N, A, dev, sec_par_pas=SPP)
    e = torch.full((N, A), LOCAL, dtype=torch.long, device=dev)
    dobj = torch.full((N,), 100.0, device=dev)
    for _ in range(20): p5.observer(d, e, px, py, dist_obj=dobj)     # jamais de gain
    dire("inflammation sterile detectee", p5.rapport()["chronique"] > 0.9,
         "%.2f" % p5.rapport()["chronique"])
    p6 = Pathologies(N, A, dev, sec_par_pas=SPP)
    dobj = torch.full((N,), 100.0, device=dev)
    for _ in range(20):
        dobj = dobj - 2.0
        p6.observer(d, e, px, py, dist_obj=dobj)
    dire("inflammation qui PRODUIT du terrain : verte", p6.rapport()["chronique"] < 0.1,
         "%.2f" % p6.rapport()["chronique"])

    # 5. le verdict est bien un ET : un seul rouge fait echouer
    p7 = Pathologies(N, A, dev, sec_par_pas=SPP)
    p7.observer(d, torch.zeros(N, A, dtype=torch.long, device=dev), px, py)
    e2 = torch.zeros(N, A, dtype=torch.long, device=dev); e2[:, 0] = REFLEXE
    p7.observer(d, e2, px, py)
    p7.observer_tir(px, py, torch.zeros(N, A, 2, device=dev) - 1.0,
                    torch.zeros(N, A, dtype=torch.bool, device=dev))
    passe, txt = p7.verdict()
    dire("verdict vert quand tout va bien", passe)
    print(txt)

    print("=== sirocco_patho : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
