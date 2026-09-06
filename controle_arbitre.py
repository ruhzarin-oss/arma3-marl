#!/usr/bin/env python3
"""controle_arbitre — LE CONTROLE POSITIF DE L ARBITRE, avec ses DEUX facons d echouer.
Regle 16 : on juge l ACTE de mesure — l instrument doit savoir dire NON avant de dire oui.

CE QUI EST ISOLE : le SCORE, et rien d autre. Les cinq bras partagent les memes candidats,
la meme annotation moteur, la meme cadence, la meme emission, les memes scenarios GELES
(blocs de marge.py : tous les bras jouent les MEMES placements — sans blocs, le max sur
plusieurs bras d un bruit a ecart-type ~1,8 fabrique une marge tout seul).

LES BRAS
  arbitre      . le score complet (tarifs mesures : vu x2,45 ; supprime x29,81 ; etre-vu
                 = 2x voir ; cote suppression x27,9).
  uniforme     . LE TEMOIN : memes candidats, meme execution, selection UNIFORME. Ce que
                 l arbitre doit battre — une pre-inscription doit battre un temoin sans
                 modele (<cinq-arrets-derivation-placeur>).
  anti         . PREMIERE FACON D ECHOUER : signes des termes TARIFES inverses (maximiser
                 etre-vu, penaliser la suppression). Progres et immobilite NON inverses :
                 si l anti perd, il perd par l EXPOSITION, pas par le tempo. Il doit perdre
                 d au moins l effet revendique — sinon les tarifs ne portent rien ICI.
  melange      . DEUXIEME FACON D ECHOUER : annotations PERMUTEES entre candidats avant
                 scorage. L information detruite, l arbitre doit retomber sur l uniforme.
                 S il s en ecarte, il lit AUTRE CHOSE que les annotations -> banc invalide.
  arbitre_bis  . LE PLANCHER DE BRUIT : meme score contre meme score, graines
                 d echantillonnage differentes. Mesure AVANT tout seuil.

METRIQUE PRINCIPALE : PERTES (hommes perdus sur 8), par bloc apparie. Les tarifs sont des
rapports de taux de MORT — c est sur les morts que la revendication porte.
EFFET MINIMAL PRE-INSCRIT : 1,0 perte sur 8 (12,5 pts), du meme ordre que le seul tarif de
survie deja chiffre (tenue : 31,4 % -> 19,9 %, ~11,5 pts).
SEUIL FINAL = max(1,0 ; 2 x plancher de bruit). Le plancher se lit EN PREMIER.

ORDRE DE LECTURE — ecrit AVANT les donnees (le detail est dans DEPOT_ARBITRE.md) :
  0. plancher (arbitre vs arbitre_bis). S il depasse l effet minimal : AUCUN VERDICT.
  1. uniforme - arbitre >= seuil sur les pertes. Sinon RIEN D AUTRE N EST LU.
  2. anti - arbitre >= seuil : l anti-score doit PERDRE d au moins l effet revendique.
  3. |melange - uniforme| <= 2 x plancher : detruire l information rend la selection uniforme.
  4. garde du tempo : avance(arbitre) >= avance(uniforme) - 30 m.

LES LECTURES PERDANTES, ECRITES D AVANCE (aucune ne sera requalifiee apres coup) :
  1. CONTRE L INCONNU — si > 50 % du feu recu vient d eid HORS journal au moment de
     l evenement, les annotations ne pricent pas ce qui tue : arbitre ~ uniforme jugera le
     CAPTEUR, pas l arbitre.
  2. CONTRE LE TEMPO — l arbitre peut acheter ses pertes en refusant d avancer. Si la garde
     n.4 tombe, le verdict est « il survit en n entrant pas » (<tout-ce-qui-fige-un-homme-
     coute> : doctrine scriptee 91,0 % en RETIRANT des gestes).
  3. HORS DU MONDE TARIFE — les tarifs viennent d un autre banc (432 transitions). Si l anti
     ne perd pas ALORS QUE les annotations discriminent (etendue non nulle), les tarifs ne
     transferent pas a CE monde-ci : re-mesurer ICI avant de toucher au score.
"""
import sys, time, json, random, argparse
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from marge import scene, NB_AMI
from arbitre import Arbitre

BRAS = ("arbitre", "uniforme", "anti", "melange", "arbitre_bis")
MODE = {"arbitre": "arbitre", "arbitre_bis": "arbitre",
        "uniforme": "uniforme", "anti": "anti", "melange": "melange"}
DUREE = 300                 # s par episode
EFFET_MIN = 1.0             # pertes sur 8 — devenu NON DECISIF (amendement 2 : plancher
                            # mesure 4,41/8, il faudrait 78 blocs ~36 h pour detecter 1,0)
SEUIL_DECOUVERTE = 1.44     # seuil DEPOSE (banc de marge, plancher 7,42 sigma 1,78) —
                            # METRIQUE PRINCIPALE depuis l amendement 2 du 30/08.
                            # ⚠️ LE SENS S INVERSE : moins de pertes est BIEN, plus de
                            # decouverte est BIEN. Tous les signes ci-dessous sont retournes.
GARDE_TEMPO = 30.0          # m — la garde n.4
SORTIE = "/mnt/data/controle_arbitre.json"


def episode(b, bras, graine):
    scene(b, graine)                            # BLOC GELE : tous les bras, memes placements
    time.sleep(3)
    arb = Arbitre(b, mode=MODE[bras], graine_ech=(hash((bras, graine)) & 0xffff))
    arb.armer()
    v0, dec0, _ = arb.mesurer()
    if v0 is None or v0 < NB_AMI - 1:
        return None                             # scene incomplete : episode invalide
    arb.boucle(DUREE)
    v1, dec1, _ = arb.mesurer()
    if v1 is None:
        return None
    avance = (arb.hist[0][2] - arb.hist[-1][2]) if len(arb.hist) >= 2 else 0.0
    return dict(bras=bras, graine=graine,
                pertes=v0 - v1, vivants=v1,
                decouverte=(dec1 or 0) - (dec0 or 0),
                avance=round(avance, 1),
                feu_total=arb.feu_total, feu_inconnu=arb.feu_inconnu)


def lecture(res):
    """L ORDRE DE LECTURE, applique mecaniquement. res : bras -> {graine: episode}."""
    communs = [set(v) for v in res.values() if v]
    scs = sorted(set.intersection(*communs)) if len(communs) == len(BRAS) else []
    if len(scs) < 4:
        print("\n  ⛔ moins de 4 blocs communs aux 5 bras — AUCUN VERDICT")
        return
    P = {br: {s: res[br][s] for s in scs} for br in BRAS}

    def m(br, k):
        return float(np.mean([P[br][s][k] for s in scs]))

    print("\n" + "─" * 92)
    print("  LA TABLE (DECOUVERTE par bloc — tous les bras sur les MEMES placements)")
    print("  %-12s %s   moyenne" % ("bras", " ".join("sc%d" % s for s in scs)))
    for br in BRAS:
        v = [P[br][s]["decouverte"] for s in scs]
        print("  %-12s %s   %.2f" % (br, " ".join("%3d" % x for x in v), np.mean(v)))

    print("\n" + "─" * 92)
    print("  ORDRE DE LECTURE — ecrit avant les donnees (DEPOT_ARBITRE.md)")

    # 0. LE PLANCHER DE BRUIT — avant tout seuil
    dp = [abs(P["arbitre"][s]["decouverte"] - P["arbitre_bis"][s]["decouverte"]) for s in scs]
    plancher = float(np.mean(dp))
    seuil = max(SEUIL_DECOUVERTE, 2.0 * plancher)
    print("\n  0. PLANCHER : |arbitre - arbitre_bis| moyen = %.2f decouverte(s)  ->  seuil final %.2f"
          % (plancher, seuil))
    if plancher > SEUIL_DECOUVERTE:
        print("     ⛔ le plancher DEPASSE l effet minimal pre-inscrit (%.1f) : le banc ne peut"
              " rien dire. AUCUN VERDICT." % SEUIL_DECOUVERTE)
        return

    # diagnostic de la lecture perdante n.1, imprime AVANT le verdict n.1
    ft = sum(P["arbitre"][s]["feu_total"] for s in scs)
    fi = sum(P["arbitre"][s]["feu_inconnu"] for s in scs)
    part_inconnu = (fi / ft) if ft else 0.0
    print("     feu recu venant de l INCONNU (hors journal) : %.0f %%  (%d/%d)"
          % (100 * part_inconnu, fi, ft))

    # 1. arbitre contre le temoin uniforme
    gain = m("arbitre", "decouverte") - m("uniforme", "decouverte")
    ok1 = gain >= seuil
    print("\n  1. arbitre - uniforme = %+.2f decouverte(s)   (seuil %.2f)   %s"
          % (gain, seuil, "✅" if ok1 else "⛔ RIEN D AUTRE N EST LU"))
    if not ok1:
        if part_inconnu > 0.5:
            print("     -> LECTURE PERDANTE n.1 — CONTRE L INCONNU : %.0f %% du feu vient de"
                  " tireurs hors journal. Le verdict juge le CAPTEUR, pas l arbitre."
                  % (100 * part_inconnu))
        else:
            print("     -> le feu venait de contacts CONNUS (%.0f %% d inconnu) : la lecture"
                  " perdante n.1 ne s applique pas. Voir n.3 (hors du monde tarife)"
                  " via le bras anti ci-dessous, rapporte a titre de diagnostic." % (100 * part_inconnu))

    # 2. l anti-score doit PERDRE d au moins l effet revendique
    d_anti = m("arbitre", "decouverte") - m("anti", "decouverte")
    ok2 = d_anti >= seuil
    print("\n  2. arbitre - anti = %+.2f decouverte(s)   (doit etre >= %.2f)   %s"
          % (d_anti, seuil, "✅ l anti PERD : le score porte un effet, dans le bon sens"
             if ok2 else "⛔ l anti ne perd pas assez"))
    if not ok2:
        print("     -> LECTURE PERDANTE n.3 — HORS DU MONDE TARIFE : les tarifs (2,45 ; 29,81),"
              " mesures sur 432 transitions d un AUTRE banc, ne transferent pas a ce monde-ci."
              " Re-mesurer ICI avant de toucher au score.")

    # 3. annotations melangees -> retomber sur l uniforme
    d_mel = abs(m("melange", "decouverte") - m("uniforme", "decouverte"))
    ok3 = d_mel <= 2.0 * plancher if plancher > 0 else d_mel <= SEUIL_DECOUVERTE / 2.0
    print("\n  3. |melange - uniforme| = %.2f decouverte(s)   (doit etre <= %.2f)   %s"
          % (d_mel, max(2.0 * plancher, SEUIL_DECOUVERTE / 2.0),
             "✅ l information detruite rend la selection uniforme"
             if ok3 else "⛔ l arbitre lit AUTRE CHOSE que les annotations — BANC AUTO-INVALIDE"))

    # 4. la garde du tempo
    d_av = m("arbitre", "avance") - m("uniforme", "avance")
    ok4 = d_av >= -GARDE_TEMPO
    print("\n  4. avance(arbitre) - avance(uniforme) = %+.1f m   (garde -%.0f m)   %s"
          % (d_av, GARDE_TEMPO, "✅" if ok4 else
             "⛔ LECTURE PERDANTE n.2 — CONTRE LE TEMPO : il survit en n entrant pas"))

    # secondaire, rapportee, non decisive
    d_per = m("uniforme", "pertes") - m("arbitre", "pertes")
    print("\n  secondaire : pertes uniforme - arbitre = %+.2f / 8 — NON DECISIF, plancher 4,41 (%.0f)"
          % (d_per, 0))

    print("\n" + "─" * 92)
    if ok1 and ok2 and ok3 and ok4:
        print("  ✅ LES QUATRE LIGNES SONT VERTES : l arbitre bat le temoin, l anti perd,")
        print("     le melange retombe sur l uniforme, le tempo est tenu. L instrument sait")
        print("     echouer et n a pas echoue.")
    else:
        print("  ⛔ AU MOINS UNE LIGNE ROUGE : la lecture s arrete a la premiere, et la lecture")
        print("     perdante correspondante — ecrite avant les donnees — est LE verdict.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", type=int, default=6)
    ap.add_argument("--bras", nargs="+", default=list(BRAS))
    a = ap.parse_args()
    print("=" * 92)
    print(" CONTROLE POSITIF DE L ARBITRE — %d blocs geles x %d bras, %d s l episode"
          % (a.scenarios, len(a.bras), DUREE))
    print("=" * 92)
    print("  metrique principale : DECOUVERTE   seuil pre-inscrit : %.2f   (amendement 2)"
          % SEUIL_DECOUVERTE, flush=True)
    print("  les PERTES sur %d sont rapportees mais NON DECISIVES : plancher mesure 4,41/8,\n"
          "  il faudrait 78 blocs (~36 h) pour y detecter l effet minimal de %.1f."
          % (NB_AMI, EFFET_MIN), flush=True)
    res = {br: {} for br in a.bras}
    b = None
    try:
        b = NativeBridge(port=5801, timeout=90)
        for sc in range(a.scenarios):
            ordre = list(a.bras)
            random.Random(sc).shuffle(ordre)          # ordre des bras BROUILLE par bloc
            for br in ordre:
                e = episode(b, br, sc)
                if e:
                    res[br][sc] = e
                    print("  sc%d %-12s : pertes %d/%d  avance %6.1f m  decouverte %+d"
                          "  feu inconnu %d/%d"
                          % (sc, br, e["pertes"], NB_AMI, e["avance"], e["decouverte"],
                             e["feu_inconnu"], e["feu_total"]), flush=True)
                else:
                    print("  sc%d %-12s : episode INVALIDE" % (sc, br), flush=True)
                json.dump(res, open(SORTIE, "w"), indent=1)
    finally:
        if b:
            try:
                b.close()
            except Exception:
                pass
    if all(br in res for br in BRAS):
        lecture(res)
    else:
        print("\n  (bras partiels : la lecture complete exige les 5 bras)")
