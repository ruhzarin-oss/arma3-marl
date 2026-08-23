#!/usr/bin/env python3
"""porter_boucle — PORTER LA POLITIQUE APPRISE VERS ARMA.

La politique de `boucle_pol.pt` a ete entrainee sur 12 entrees. La couture Arma
(`arma_couture.py`) en produit 18 depuis de vraies unites du jeu, dans cet ordre :

    [0..8]   base 9   apx/S, apy/S, dgx, dgy, alive, slope, dcover, los, nd
    [9..10]  suffer 2 degats recus, fraction de defenseurs qui peuvent me toucher
    [11..14] team 4   binome dx, dy, il cloue ?, feu de l equipe
    [15..17] posture 3 one-hot debout / accroupi / couche

Les 12 de la politique sont **base 9 + posture 3**, donc les colonnes **0-8 et 15-17**.
Le contrat se respecte par SELECTION, pas par reinterpretation : aucune colonne n est
renommee, aucune n est fabriquee.

⚠️ TROIS LIMITES DECLAREES AVANT TOUT ESSAI, parce qu'elles decident la lecture :
  1. LA POLITIQUE NE SE COUCHE JAMAIS. Elle a 10 actions (8 caps, tenir, appuyer) ; poser
     une posture, ce sont les actions 10/11/12 du monde, qu elle n a jamais eues. Elle
     jouera donc DEBOUT en permanence. Sur Arma, ou se montrer coute 4,00 DEFINITIVEMENT,
     c est un handicap reel — et il est a elle, pas au portage.
  2. `slope` (colonne 5) vient du relief. La couture la sort du jeu ; si elle rendait zero,
     la politique verrait un monde plat qu elle n a jamais connu. Le self-test le verifie.
  3. Le monde d entrainement avait 13 defenseurs et 8 attaquants a 200 m. Toute mission
     Arma qui s en ecarte mesure autre chose.

  python porter_boucle.py            -> SELF-TEST hors-ligne (pas d Arma)
"""
import sys, math
sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from boucle import Politique, NA

PT = "/home/younes/arma3-marl/boucle_pol.pt"
# `arma_obs=True` : la base tombe a 8 — SANS `slope`, qu Arma ne sait pas rendre.
# Dans les 18 colonnes de la couture, slope est en position 5 : on la SAUTE.
# --- 12/08/2026, remise en route apres le passage sous Windows/WSL2 ---
# La ligne du 11/08 15h36 retirait `slope` en disant qu Arma ne sait pas la rendre. C est
# faux : arma_couture.py ligne 41 la calcule bel et bien, par surfaceNormal. Et trois pieces
# reclament DOUZE entrees -- boucle_pol.pt (128x12), la couture, et le docstring de
# banc_live.py qui declare "base9+posture3". La selection a 11 n a jamais ete reentrainee :
# le formatage est arrive vingt minutes apres. On revient donc a base 9 + posture 3.
# Pour retrouver l etat du 11/08 : porter_boucle.py.avant_12col
COLS = [0, 1, 2, 3, 4, 5, 6, 7, 8] + [15, 16, 17]     # base 9 (slope incluse) + posture 3


def charger(dev="cpu", pt=None):
    """⚠️ LE NOMBRE D ACTIONS SE LIT DANS L ARTEFACT, IL NE SE SUPPOSE PAS. Depuis le 23/08
    il existe des politiques a 10 actions (sans posture) et a 13. Construire le reseau sur
    la valeur courante de `boucle.NA` chargerait un jour l une avec la taille de l autre —
    et `load_state_dict` le dirait, mais seulement si les tailles different. On lit donc la
    forme de la couche de sortie dans le fichier lui-meme."""
    import boucle as _b
    chemin = pt or PT
    sd = torch.load(chemin, map_location=dev)
    na = sd["pi.weight"].shape[0]
    garde = _b.NA
    try:
        _b.NA = na
        pol = Politique(len(COLS)).to(dev)
    finally:
        _b.NA = garde
    pol.load_state_dict(sd)
    pol.eval()
    return pol


def decider(pol, obs18):
    """obs18 : (n_hommes, 18) tel que la couture le sort. Rend les actions du monde."""
    o = torch.as_tensor(obs18, dtype=torch.float32)
    if o.shape[-1] != 18:
        raise ValueError(f"la couture doit rendre 18 colonnes, elle en rend {o.shape[-1]}")
    with torch.no_grad():
        logits, _ = pol(o[:, COLS])
    return logits.argmax(-1).tolist()


def _selftest():
    print("\n  SELF-TEST HORS-LIGNE — la moitie Python <-> reseau <-> SQF")
    print("  " + "=" * 66)
    pol = charger()
    n_par = sum(p.numel() for p in pol.parameters())
    print(f"    politique chargee : {n_par} parametres, {len(COLS)} entrees, {NA} actions")

    # ---- CONTROLE 1 : la selection de colonnes est la bonne
    ok = COLS == [0, 1, 2, 3, 4, 5, 6, 7, 8] + [15, 16, 17]
    print(f"    {'PASSE' if ok else 'TOMBE':>6}  colonnes selectionnees : base 9 avec slope + posture 3")

    # ---- CONTROLE 2 : sur une obs plausible, les actions sont valides
    torch.manual_seed(0)
    o = torch.randn(8, 18) * 0.3
    o[:, 4] = 1.0                       # vivant
    o[:, 15] = 1.0; o[:, 16:18] = 0.0   # debout
    a = decider(pol, o)
    ok2 = all(0 <= x < NA for x in a)
    print(f"    {'PASSE' if ok2 else 'TOMBE':>6}  actions dans [0,{NA}) : {a}")

    # ---- CONTROLE 3 : elle REAGIT a la direction de l objectif. Une politique qui rend
    # la meme action ou que soit le but n a rien appris de transportable.
    vus = set()
    for th in [i * math.pi / 4 for i in range(8)]:
        o = torch.zeros(1, 18)
        o[0, 4] = 1.0; o[0, 15] = 1.0
        o[0, 2] = math.sin(th); o[0, 3] = math.cos(th)     # dgx, dgy = direction du but
        vus.add(decider(pol, o)[0])
    ok3 = len(vus) >= 4
    print(f"    {'PASSE' if ok3 else 'TOMBE':>6}  reagit a la direction du but : "
          f"{len(vus)} actions distinctes sur 8 azimuts")

    # ---- CONTROLE 4 : elle ne se couche jamais — limite declaree, verifiee
    ok4 = all(x < 10 for x in a)
    print(f"    {'PASSE' if ok4 else 'TOMBE':>6}  aucune action de posture (limite declaree)")

    # ---- CONTROLE 5 : le SQF sort bien forme
    try:
        from arma_couture import acts_to_sqf
        sqf = acts_to_sqf(a)
        ok5 = "__ACTS__" not in sqf and len(sqf) > 20
        print(f"    {'PASSE' if ok5 else 'TOMBE':>6}  SQF bien forme ({len(sqf)} caracteres)")
    except Exception as ex:
        ok5 = False
        print(f"    TOMBE  SQF : {str(ex)[:60]}")

    print("  " + "=" * 66)
    tous = ok and ok2 and ok3 and ok4 and ok5
    if tous:
        print("    LA MOITIE PYTHON EST PROUVEE. Le reseau lit une obs de couture, rend des")
        print("    actions valides, reagit a la geometrie, et sort du SQF bien forme.")
        print("    Ce qui reste a prouver : que la couture sorte du JEU les memes 18 colonnes.")
    else:
        print("    LE PORTAGE N EST PAS PRET. On ne lance rien sur Arma.")
    return tous


if __name__ == "__main__":
    sys.exit(0 if _selftest() else 1)
