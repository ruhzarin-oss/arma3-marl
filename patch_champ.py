#!/usr/bin/env python3
"""patch_champ.py — ETAGE 1 : donner a l agent le PRIX DU PAS QU IL N A PAS ENCORE FAIT.

Ce qu il voit deja (lu dans le code, pas dans mes souvenirs) : sa position, chaque defenseur
vivant, son ecart a la face de chacun (`ec_lui`), et un scalaire de risque appris POUR SA
CASE. Ce qu il ne voit pas : le prix d une case voisine. Il a un thermometre, pas une carte.

CE QU ON AJOUTE : huit nombres, le risque APPRIS a 35 m dans huit directions.

Trois choix, repris sans retouche du 27/07 :
  - a 35 m et pas au pas suivant : c est l echelle de la MANOEUVRE, pas du reflexe ;
  - le PRIX, jamais la reponse : pas de booleen « peut-il me tirer dessus » ;
  - geometrie generique, meme principe que la coque a 12 rayons.

ET LE PLACEBO EST DANS LE MEME CODE. `--placebo` remplace le champ par huit nombres de bruit
de meme echelle. Meme reseau, meme capacite, meme barheme. Si le placebo passe aussi, c est
la taille du reseau qui paie et le resultat tombe.
"""
import pathlib, sys

P = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = P.read_text(encoding='utf-8')

# ---------- 1. le champ lui-meme, juste apres risque() ----------
ANC = "def percevoir(p, post, idx):"
NEUF = '''# ============ LE CHAMP DE RISQUE — ETAGE 1 ============
# Criteres deposes avant lancement : CRITERES_ETAGE1_PERCEPTION.md (+ addendum sur la taille
# de la porte : 5 graines, succes a 4 sur 5).
CHAMP_ACTIF = '--champ' in sys.argv
CHAMP_PLACEBO = '--placebo' in sys.argv
PORTEE_CHAMP = 35.0
_a8 = torch.arange(8, device=dev, dtype=torch.float32) * (math.pi / 4)
DIRS8 = torch.stack([torch.sin(_a8), torch.cos(_a8)], -1)     # (8,2), huit caps

def champ_risque(p, post, idx):
    """le prix d un pas de 35 m dans chacune des huit directions. (B,8)

    Le PLACEBO tire huit nombres de bruit de meme echelle : meme capacite offerte au reseau,
    zero information. C est le controle qui sait echouer."""
    B = p.shape[0]
    if CHAMP_PLACEBO:
        return torch.rand(B, 8, device=dev)
    pp = (p.unsqueeze(1) + DIRS8.unsqueeze(0) * PORTEE_CHAMP).reshape(B * 8, 2)
    return risque(pp, post.repeat_interleave(8), idx.repeat_interleave(8)).reshape(B, 8)

def percevoir(p, post, idx):'''
assert t.count(ANC) == 1, "ancre percevoir introuvable"
t = t.replace(ANC, NEUF, 1)

# ---------- 2. le brancher sur l observation ----------
A2 = """                     risque(p, post, idx).unsqueeze(-1)], -1)
    return moi, ent"""
N2 = """                     risque(p, post, idx).unsqueeze(-1)]
                    + ([champ_risque(p, post, idx)] if CHAMP_ACTIF else []), -1)
    return moi, ent"""
assert t.count(A2) == 1, "ancre de moi introuvable"
t = t.replace(A2, N2, 1)

# ---------- 3. la largeur d entree suit ----------
A3 = "CE, CM = 9, 8"
N3 = ("CE, CM = 9, (8 + 8 if CHAMP_ACTIF else 8)   # +8 = le champ de risque (etage 1)\n"
      "print(f\"observation : {CE} par entite, {CM} pour soi\"\n"
      "      f\"{' — CHAMP DE RISQUE ACTIF' if CHAMP_ACTIF else ''}\"\n"
      "      f\"{' (PLACEBO : bruit)' if CHAMP_PLACEBO else ''}\", flush=True)")
assert t.count(A3) == 1, "ancre CE,CM introuvable"
t = t.replace(A3, N3, 1)

P.write_text(t, encoding='utf-8')
print("champ de risque pose (drapeaux --champ et --placebo)")
