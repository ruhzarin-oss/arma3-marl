"""sirocco_etat — L'AXE DU STRESS + le reglage de mission. Brique ISOLEE, rien n'est branche.

Dans la v1, `s1` est une constante. C'est la naivete qui reste : le meme agent joue la meme
partition a la minute 1 et a la minute 20, avec 300 cartouches ou 30.

Le corps ne fait pas ca. Il a un modulateur GLOBAL — deux, en fait, et ils tirent en sens
inverse :

  ADRENALINE  aigue. Monte avec la menace immediate et l'urgence temporelle.
              Baisse les seuils (reagir vite) ET augmente l'audace (accepter l'exposition).
  CORTISOL    chronique. Monte avec la duree de l'engagement et l'attrition.
              DEPRIME la reponse : on economise, on encaisse, on ne repart plus.

Ce dualisme n'est pas decoratif : il produit un systeme qui s'emballe puis s'epuise, ce qui
est le comportement observe d'une escouade sous le feu depuis dix minutes.

Deux sorties, et la seconde est celle qui fait PRENDRE :

  mod_seuil   multiplie les seuils de la cascade. < 1 = plus reactif.
  audace      multiplie l'exposition qu'on accepte de payer. > 1 = on entre.

Sans `audace`, tout ce systeme ne sait que se proteger — et un systeme immunitaire tactique
qui ne sait que se proteger est un systeme rate (cf. SIROCCO-V2.md section 0).

smoke : python sirocco_etat.py smoke
"""
import sys
import torch

# Reglage de base par MISSION (section 1.10 : le seuil n'est pas un hyperparametre).
# L'immunite ne regle pas son compromis une fois pour toutes : elle le regle par TISSU.
# L'oeil et le cerveau sont des sites immuno-privilegies — on y prefere laisser passer une
# infection plutot que detruire le tissu par l'inflammation.
MISSIONS = {
    "recon":      1.60,   # ne pas reagir, rester invisible, encaisser du risque
    "patrouille": 1.00,
    "defense":    0.90,
    "assaut":     0.70,   # reagir tot, quitte a sur-reagir
}


class EtatGlobal:
    def __init__(self, N, device, mission="assaut", sec_par_pas=None,
                 demivie_adre=8.0,      # s : l'adrenaline retombe vite
                 demivie_corti=90.0,    # s : le cortisol traine
                 seuil_min=0.40, seuil_max=1.80,     # bornes dures sur la modulation
                 audace_min=0.60, audace_max=2.00):
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError("sec_par_pas manquant : les demi-vies hormonales sont en SECONDES.")
        if mission not in MISSIONS:
            raise ValueError("mission inconnue : %s (connues : %s)" % (mission, list(MISSIONS)))
        self.N, self.dev, self.mission = int(N), device, mission
        self.k_mission = MISSIONS[mission]
        self.a_adre = 0.5 ** (sec_par_pas / demivie_adre)
        self.a_corti = 0.5 ** (sec_par_pas / demivie_corti)
        self.smin, self.smax = seuil_min, seuil_max
        self.amin, self.amax = audace_min, audace_max
        self.adre = torch.zeros(N, device=device)
        self.corti = torch.zeros(N, device=device)

    @torch.no_grad()
    def reset(self, idx=None):
        if idx is None: self.adre.zero_(); self.corti.zero_()
        else: self.adre[idx] = 0.0; self.corti[idx] = 0.0

    @torch.no_grad()
    def pas(self, danger=None, pertes=0.0, temps_restant=1.0, munitions=1.0, dist_obj=None,
            dist_obj0=None):
        """Un pas d'horloge hormonale. Tout est en fractions (N,) dans [0,1] sauf dist_obj.

        danger        (N,A) ou (N,) l'alarme courante -> pousse l'adrenaline
        pertes        (N,) fraction de l'escouade perdue -> pousse le cortisol
        temps_restant (N,) fraction du temps de mission restant -> 0 = urgence maximale
        munitions     (N,) fraction restante -> peu de munitions = on ne peut plus arroser
        dist_obj      (N,) distance a l'objectif ; avec dist_obj0 -> retard de progression
        """
        d = self.dev
        f = lambda x: (torch.as_tensor(x, device=d, dtype=torch.float32).expand(self.N).clone()
                       if not torch.is_tensor(x) or x.dim() == 0 else x.float())   # noqa: E731
        dg = torch.zeros(self.N, device=d) if danger is None else \
            (danger.max(1).values if danger.dim() > 1 else danger.float())
        tr = f(temps_restant).clamp(0, 1); pe = f(pertes).clamp(0, 1); mu = f(munitions).clamp(0, 1)

        # retard : loin de l'objectif ALORS que le temps file. C'est ca, la pression de mission.
        retard = torch.zeros(self.N, device=d)
        if dist_obj is not None and dist_obj0 is not None:
            reste = (f(dist_obj) / f(dist_obj0).clamp(min=1e-6)).clamp(0, 1)
            retard = (reste - tr).clamp(min=0.0)        # > 0 = on est en retard sur l'horaire

        # --- montee ---
        # aigu : le danger present + l'urgence temporelle + le retard
        pousse_a = (0.60 * dg + 0.25 * (1 - tr) + 0.60 * retard).clamp(0, 1)
        # chronique : l'attrition + le manque de munitions. Ca ne redescend pas vite.
        pousse_c = (0.70 * pe + 0.30 * (1 - mu)).clamp(0, 1)
        self.adre = (self.adre * self.a_adre + pousse_a * (1 - self.a_adre)).clamp(0, 1)
        self.corti = (self.corti * self.a_corti + pousse_c * (1 - self.a_corti)).clamp(0, 1)
        return self.adre, self.corti

    @torch.no_grad()
    def mod_seuil(self):
        """Facteur multiplicatif sur les seuils de la cascade. (N,).
        L'adrenaline les baisse (on reagit a moins). Le cortisol les remonte : un organisme
        epuise cesse de repondre — c'est l'anergie, et c'est une pathologie que le banc
        surveille deja. La borne basse existe pour qu'elle reste une pathologie possible,
        pas une fatalite."""
        m = self.k_mission * (1.0 - 0.55 * self.adre) * (1.0 + 0.45 * self.corti)
        return m.clamp(self.smin, self.smax)

    @torch.no_grad()
    def audace(self):
        """Facteur sur l'exposition qu'on accepte de payer. (N,). > 1 = on entre.

        C'est la sortie qui fait PRENDRE. Quand le temps manque, l'agent accepte une
        exposition qu'il refusait — pas parce qu'il a appris quelque chose de neuf, mais
        parce que le prix relatif a change. Le cortisol la rabaisse : epuise, on n'attaque
        plus."""
        a = (1.0 + 0.85 * self.adre) * (1.0 - 0.35 * self.corti)
        return a.clamp(self.amin, self.amax)

    @torch.no_grad()
    def seuil(self, s1_base, forme=None):
        """Seuil final a passer a la cascade. `forme` (N,A) -> diffuse sur les agents."""
        m = self.mod_seuil() * float(s1_base)
        return m if forme is None else m.unsqueeze(1).expand(forme)

    def resume(self):
        return "mission=%s adre=%.2f corti=%.2f seuil x%.2f audace x%.2f" % (
            self.mission, float(self.adre.mean()), float(self.corti.mean()),
            float(self.mod_seuil().mean()), float(self.audace().mean()))


# ---- smoke ------------------------------------------------------------------------------
def _smoke():
    from sirocco import device_defaut
    dev = device_defaut()
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== sirocco_etat : smoke isole (device %s) ===" % dev, flush=True)
    SPP = 0.7; S1 = 0.25

    try:
        EtatGlobal(2, dev, sec_par_pas=SPP, mission="banzai"); dire("mission inconnue refusee", False)
    except ValueError:
        dire("mission inconnue refusee", True)
    try:
        EtatGlobal(2, dev); dire("sec_par_pas obligatoire", False)
    except ValueError:
        dire("sec_par_pas obligatoire (refus explicite)", True)

    # 1. la mission decale le seuil de base, sans aucune hormone
    sr = float(EtatGlobal(1, dev, "recon", SPP).seuil(S1))
    sa = float(EtatGlobal(1, dev, "assaut", SPP).seuil(S1))
    dire("recon reagit MOINS qu'assaut", sr > sa * 1.5, "recon %.3f vs assaut %.3f" % (sr, sa))

    # 2. l'adrenaline monte avec le danger et fait baisser le seuil
    e = EtatGlobal(1, dev, "assaut", SPP)
    s0 = float(e.seuil(S1))
    for _ in range(20): e.pas(danger=torch.ones(1, 1, device=dev))
    s1 = float(e.seuil(S1))
    dire("sous le feu : le seuil baisse", s1 < s0 * 0.8, "%.3f -> %.3f" % (s0, s1))
    dire("sous le feu : l'audace monte", float(e.audace()) > 1.3, "x%.2f" % float(e.audace()))

    # 3. l'adrenaline retombe quand le danger cesse
    for _ in range(int(30 / SPP)): e.pas(danger=torch.zeros(1, 1, device=dev))
    dire("le calme fait retomber l'adrenaline", float(e.adre) < 0.15, "%.3f" % float(e.adre))

    # 4. LE comportement voulu : le temps qui manque fait ENTRER
    e2 = EtatGlobal(1, dev, "assaut", SPP)
    a_debut = float(e2.audace())
    for t in range(40):
        e2.pas(temps_restant=torch.tensor([1 - t / 40.0], device=dev),
               dist_obj=torch.tensor([120.0], device=dev), dist_obj0=torch.tensor([150.0], device=dev))
    a_fin = float(e2.audace())
    dire("le temps qui manque augmente l'audace", a_fin > a_debut * 1.25,
         "x%.2f -> x%.2f" % (a_debut, a_fin))

    # 5. le cortisol : l'attrition finit par DEPRIMER la reponse (l'epuisement existe)
    e3 = EtatGlobal(1, dev, "assaut", SPP)
    for _ in range(int(240 / SPP)):
        e3.pas(pertes=torch.tensor([0.5], device=dev), munitions=torch.tensor([0.15], device=dev))
    dire("attrition longue : le cortisol monte", float(e3.corti) > 0.4, "%.2f" % float(e3.corti))
    dire("attrition longue : l'audace retombe", float(e3.audace()) < 1.0,
         "x%.2f" % float(e3.audace()))

    # 6. bornes tenues, meme en saturation absurde
    e4 = EtatGlobal(1, dev, "recon", SPP)
    for _ in range(400):
        e4.pas(danger=torch.ones(1, 1, device=dev), pertes=1.0, munitions=0.0, temps_restant=0.0)
    m = float(e4.mod_seuil()); a = float(e4.audace())
    dire("bornes du seuil tenues", e4.smin - 1e-6 <= m <= e4.smax + 1e-6, "x%.2f" % m)
    dire("bornes de l'audace tenues", e4.amin - 1e-6 <= a <= e4.amax + 1e-6, "x%.2f" % a)

    # 7. branchement reel sur la cascade : le seuil module change la date de reaction
    from sirocco import AlarmeLocale, FROLEMENT
    from sirocco_cascade import Cascade, REFLEXE

    def date_reaction(mission):
        e = EtatGlobal(1, dev, mission, SPP)
        al = AlarmeLocale(1, 1, dev, sec_par_pas=SPP)
        cas = Cascade(1, 1, dev, sec_par_pas=SPP, s1=S1)
        p = torch.zeros(1, 1, device=dev); src = torch.full((1, 1), -50.0, device=dev)
        for t in range(30):
            al.pas(); al.signaler(FROLEMENT, p, p, src, p, 0.15)
            e.pas(danger=al.danger())
            r = cas.pas(al.danger(), p, p, al.menace()[..., :2],
                        seuil=e.seuil(S1, forme=(1, 1)))
            if int(r["etat"][0, 0]) == REFLEXE: return t
        return -1

    t_rec = date_reaction("recon"); t_ass = date_reaction("assaut")
    dire("en assaut on reagit AVANT la recon", 0 <= t_ass < t_rec or (t_rec == -1 and t_ass >= 0),
         "assaut pas %d / recon pas %d" % (t_ass, t_rec))

    print("=== sirocco_etat : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
