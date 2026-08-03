"""sirocco_test — le banc des quatre briques, EN ISOLATION. Rien n'est branche a un env.

Deux parties :
  1. les smokes de chaque module (proprietes unitaires)
  2. une DEMONSTRATION de chaine complete, sans environnement

Ce que la partie 2 prouve : que les quatre modules s'emboitent et que la chaine tourne de
bout en bout — detection, champ, cascade, recrutement, resolution, memoire, compteurs.

Ce qu'elle NE prouve PAS, et il faut le dire : rien de tactique. Les evenements y sont
FABRIQUES par le script, pas produits par un monde. Aucun chiffre de survie, d'exposition ou
de prise ne doit sortir d'ici. Ces chiffres-la se mesurent sur le banc FIBUA, puis se
certifient sur Arma. C'est exactement le piege qui a fait 83 % en sim et 0 % sur Arma.

    python sirocco_test.py            # tout
    python sirocco_test.py smokes     # que les smokes
    python sirocco_test.py chaine     # que la demonstration
"""
import sys

import torch

import sirocco as S
from sirocco import AlarmeLocale, ChampSirocco, CONTACT, IMPACT, FROLEMENT, PERTE, SOI
from sirocco_cascade import Cascade, NOMS, REFLEXE, LOCAL, RECRUT, ADAPT
from sirocco_memoire import MemoireImmunitaire
from sirocco_patho import Pathologies

SPP = 0.7          # VALEUR DE TEST, PAS UNE MESURE. La vraie se mesure sur Arma.
DEV = S.device_defaut()


def smokes():
    import sirocco_cascade as C
    import sirocco_etat as E
    import sirocco_memoire as M
    import sirocco_patho as P
    import sirocco_thymus as T
    res = []
    for nom, f in [("sirocco", S._smoke), ("cascade", C._smoke),
                   ("memoire", M._smoke), ("patho", P._smoke),
                   ("etat", E._smoke), ("thymus", T._smoke)]:
        res.append((nom, bool(f())))
        print("", flush=True)
    print("=== smokes ===")
    for nom, ok in res: print("  %-12s %s" % (nom, "OK" if ok else "ECHEC"))
    return all(ok for _, ok in res)


def chaine(bavard=True, memoire=None, pas_max=70, i_frole=0.30):
    """Une escouade de 6 avance vers le nord. Un tireur est cache a l'ouest.
    Les evenements sont FABRIQUES : pres du tireur et dans son arc -> frolement ; tres pres
    -> impact. C'est un banc de plomberie, pas un monde.

    Deux agents partent LOIN en arriere : sans eux, toute l'escouade est sous le feu en
    permanence, plus personne n'est eligible, et l'etage 3 ne se declenche jamais — on
    croirait le plafond respecte alors qu'il n'a simplement pas ete sollicite.

    `i_frole` est l'intensite du frolement. Ce parametre n'est pas cosmetique : il decide si
    l'anticipation sert a quelque chose (voir anticipation())."""
    N, A, R = 1, 6, 200.0
    champ = ChampSirocco(N, R, DEV, G=28, sec_par_pas=SPP)
    al = AlarmeLocale(N, A, DEV, sec_par_pas=SPP)
    cas = Cascade(N, A, DEV, sec_par_pas=SPP, s1=0.25, s3=1.0, plafond=2)
    pat = Pathologies(N, A, DEV, sec_par_pas=SPP)

    px = torch.linspace(-40, 40, A, device=DEV).view(1, A).clone()
    py = torch.full((N, A), -120.0, device=DEV)
    py[0, -2:] = -260.0                               # deux en arriere : la reserve recrutable
    vivant = torch.ones(N, A, dtype=torch.bool, device=DEV)
    tir_x = torch.full((N, A), -90.0, device=DEV)      # le tireur, a l'ouest
    tir_y = torch.full((N, A), 0.0, device=DEV)
    obj_y = 80.0
    t_reaction = -1
    max_recrut = 0
    traces = []

    for t in range(pas_max):
        # --- 1. le monde produit des evenements (ici : fabriques) ---
        d = torch.sqrt((px - tir_x) ** 2 + (py - tir_y) ** 2)
        frole = (d < 120.0) & vivant
        touche = (d < 60.0) & vivant
        al.pas(); champ.pas()
        if memoire is not None: memoire.pas()
        if frole.any():
            al.signaler(FROLEMENT, px, py, tir_x, tir_y, i_frole, actif=frole)
            champ.deposer(FROLEMENT, px, py, i_frole, actif=frole)
        if touche.any():
            al.signaler(IMPACT, px, py, tir_x, tir_y, 0.45, actif=touche)
            champ.deposer(IMPACT, px, py, 0.45, actif=touche)
            champ.deposer(CONTACT, tir_x, tir_y, 1.0, actif=touche)   # on a localise le tireur
        champ.deposer(SOI, px, py, 1.0, actif=vivant)                  # canal negatif : IFF + anti-blob

        # --- 2. le systeme lit ---
        seuil = memoire.seuil(px, py, cas.s1) if memoire is not None else None
        m = al.menace()
        cx = px.mean(1, keepdim=True); cy = py.mean(1, keepdim=True)
        charge = champ.somme_zone(cx, cy, 60.0).squeeze(1)
        grad = champ.gradient(px, py)[:, :, CONTACT, :]
        dist_obj = (obj_y - py.mean(1)).clamp(min=0)
        r = cas.pas(al.danger(), px, py, m[..., :2], charge=charge, grad=grad,
                    vivant=vivant, dist_obj=dist_obj, seuil=seuil)
        pat.observer(al.danger(), r["etat"], px, py, vivant=vivant, charge=charge,
                     dist_obj=dist_obj)
        if memoire is not None:
            memoire.marquer(px, py, 1.0, actif=(r["etat"] == REFLEXE))
        if t_reaction < 0 and bool((r["etat"] == REFLEXE).any()): t_reaction = t
        max_recrut = max(max_recrut, int(r["recrute"].sum(1).max()))

        # --- 3. un executeur MINIMAL (il n'est pas le sujet : il rend la scene lisible) ---
        avance = torch.full((N, A), 3.0, device=DEV)
        avance = torch.where(r["etat"] == REFLEXE, torch.zeros_like(avance), avance)   # se plaque
        py = py + avance * vivant.float()
        ecarte = (r["etat"] == REFLEXE).float() * (-2.0) * r["cap"][..., 0]            # rompt la LOS
        px = px + ecarte
        if t == 30:                                                                    # une perte
            vivant[0, 0] = False
            champ.deposer(PERTE, px[:, :1], py[:, :1], 1.0)

        traces.append((t, float(charge[0]), int((r["etat"] == REFLEXE).sum()),
                       int((r["etat"] == LOCAL).sum()), int(r["recrute"].sum()),
                       int(r["etat_grp"][0])))

    etages_vus = {g for (_, _, _, _, _, g) in traces} | \
                 ({REFLEXE} if any(x[2] for x in traces) else set()) | \
                 ({LOCAL} if any(x[3] for x in traces) else set())
    plomberie = (max_recrut > 0 and max_recrut <= cas.plafond
                 and REFLEXE in etages_vus and LOCAL in etages_vus and RECRUT in etages_vus)
    if bavard:
        print("\n=== chaine complete (DEMONSTRATION de plomberie, aucun chiffre tactique) ===")
        print("  pas  charge  reflexe  appui  recrutes  groupe")
        for (t, c, nr, nl, nrec, g) in traces:
            if t % 6 == 0 or nrec:
                print("  %3d  %6.2f  %7d  %5d  %8d  %s" % (t, c, nr, nl, nrec, NOMS[g]))
        print("\n  etages traverses                : %s"
              % " ".join(NOMS[g] for g in sorted(etages_vus)))
        print("  recrutement effectivement teste : %s"
              % ("oui, max %d" % max_recrut if max_recrut else
                 "NON — personne n'etait eligible, le plafond n'a rien prouve ici"))
        print("  plafond respecte                : %s (plafond %d)"
              % ("OUI" if max_recrut <= cas.plafond else "NON", cas.plafond))
        print("  premiere reaction au pas        : %d" % t_reaction)
        passe, txt = pat.verdict()
        print("\n  --- compteurs de pathologie (INFORMATIF) ---")
        print(txt)
        print("  verdict : %s" % ("VERT" if passe else "AU MOINS UN ROUGE"))
        print("  ATTENTION : l'executeur de ce banc est un pis-aller de trois lignes (avancer,")
        print("  se plaquer, s'ecarter). Un compteur rouge ici accuse CET executeur, pas les")
        print("  modules. Les compteurs ne jugent qu'une fois branches sur un vrai env.")
    return {"t_reaction": t_reaction, "max_recrut": max_recrut, "plafond": cas.plafond,
            "patho": pat.rapport(), "verdict": pat.verdict()[0], "plomberie": plomberie}


def anticipation():
    """La propriete de la brique B5 : le MEME scenario, joue deux fois, avec memoire.
    Le second passage doit reagir plus tot — sans que rien d'autre ait change.

    On le joue dans DEUX regimes de signal precoce, et c'est le coeur de l'affaire :

      frolement FORT   le signal precoce suffit deja a lui seul. La memoire n'a rien a
                       apporter : on reagit au meme pas. L'anticipation est INUTILE.
      frolement FAIBLE le signal precoce ne franchit pas le seuil nominal. La memoire, en
                       abaissant le seuil, le rend suffisant. L'anticipation PAIE.

    Autrement dit : la brique B5 ne vaut que si le canal FROLEMENT est faible ou intermittent.
    C'est une condition a verifier sur Arma (voir sonde_firednear.py), pas a supposer."""
    print("\n=== anticipation : le meme scenario, deux fois, dans deux regimes ===")
    lignes = []
    for nom, i_f in [("frolement FORT  (0.30)", 0.30), ("frolement FAIBLE (0.06)", 0.06)]:
        mem = MemoireImmunitaire(1, 200.0, DEV, G=28, sec_par_pas=SPP)
        a = chaine(bavard=False, memoire=mem, i_frole=i_f)
        mem.cloturer_run()           # le vecu passe dans le priming, PUIS la marque s'efface
        b = chaine(bavard=False, memoire=mem, i_frole=i_f)
        t = chaine(bavard=False, memoire=None, i_frole=i_f)
        gain = a["t_reaction"] - b["t_reaction"]
        lignes.append((nom, t["t_reaction"], a["t_reaction"], b["t_reaction"], gain))
    print("  regime                    sans mem.  1er passage  2e passage  gain")
    for nom, ts, ta, tb, g in lignes:
        print("  %-24s %9d  %11d  %10d  %+d pas (%.1f s)" % (nom, ts, ta, tb, g, g * SPP))
    fort, faible = lignes[0][4], lignes[1][4]
    print("\n  -> la memoire ne paie que si le signal precoce est FAIBLE : %s"
          % ("confirme" if faible > fort else "PAS confirme ici"))
    print("  NOTE : les profils d'evenements sont FABRIQUES. Ceci montre a quelle CONDITION")
    print("         le mecanisme sert, pas ce qu'il vaut. La valeur se mesure sur le banc.")
    return faible > 0 and faible >= fort


if __name__ == "__main__":
    quoi = sys.argv[1] if len(sys.argv) > 1 else "tout"
    ok = True
    if quoi in ("tout", "smokes"): ok = smokes() and ok
    if quoi in ("tout", "chaine"):
        r = chaine()
        if not r["plomberie"]:
            print("\n  ECHEC : la chaine n'a pas traverse tous les etages, ou le plafond a saute.")
        ok = r["plomberie"] and anticipation() and ok
    print("\n=== BANC SIROCCO : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"))
    sys.exit(0 if ok else 1)
