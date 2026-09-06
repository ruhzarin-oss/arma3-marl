#!/usr/bin/env python3
"""para — LE REGISTRE DES INSTANCES ARMA. Une instance = un proprietaire = un travail.

⚠️ CETTE REGLE N'EST PAS UNE PREFERENCE, c'est une cicatrice. Le 30/08 j'ai tue mon
propre R2-bis a 42/75 en lancant le harnais sur des instances deja occupees. Deux
harnais sur un meme dossier de commandes se volent les cmd_N ET s'effacent au
demarrage. Rien dans les journaux ne le dit : ca ressemble a un pont mort.

Ce que chaque instance possede EN PROPRE :
  · son profil      -> son RPT (voie de retour)
  · son port        -> son serveur
  · son dossier de pont (HMT_BRIDGE_WIN, lu par la DLL) -> sa voie aller

⚠️ L'INSTANCE 0 GARDE L'ANCIEN CHEMIN C:\\hmt_bridge. Non par elegance : un run y
tourne depuis 11 h 25 et le deplacer voudrait dire le tuer. A normaliser une fois
la graine 1 finie.
"""
INSTANCES = {
    0: dict(profil="/mnt/c/Users/Younes/hmtech0", pont="/mnt/c/hmt_bridge",    port=2402),
    1: dict(profil="/mnt/c/Users/Younes/hmtech1", pont="/mnt/c/hmt_bridge/i1", port=2412),
    2: dict(profil="/mnt/c/Users/Younes/hmtech2", pont="/mnt/c/hmt_bridge/i2", port=2422),
    3: dict(profil="/mnt/c/Users/Younes/hmtech3", pont="/mnt/c/hmt_bridge/i3", port=2432),
}

def instance(i):
    if i not in INSTANCES:
        raise SystemExit(f"instance {i} inconnue ; connues : {sorted(INSTANCES)}")
    return INSTANCES[i]
