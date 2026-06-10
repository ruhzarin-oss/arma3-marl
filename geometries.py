"""geometries — KNOB DE GÉOMÉTRIE DE DÉFENSE (test décisif (a) du PDF d'archi, 09/06).
La question qui hante le projet : le vainqueur (M3-fixe) change-t-il selon la STRUCTURE de la défense,
pas seulement sa difficulté ? Si oui -> le sélecteur/officier reprend un sens. Si M3 gagne partout -> officier mort.
PRINCIPE : effectif TOTAL identique (~20) + même profil de skill -> on isole la GÉOMÉTRIE (pas la difficulté).
Format garrison = [(x,y,n,rad), ...] ; garrison[0] = noyau sur l'objectif (déclencheur QRF + métrique garr_pris).
Objectif = COMPLEXE (15000,16000). Manœuvres : M1 frontal, M2 double-enveloppement, M3 enveloppement OUEST.
Géométries conçues ADVERSARIALEMENT (chacune doit punir/récompenser une manœuvre précise)."""

OBJ = (15000, 16000)

GEOMETRIES = {
    # référence : noyau central + 2 patrouilles (la géométrie historique)
    "standard":    [(15000, 16000, 10, 80), (15150, 16120, 5, 110), (14860, 16110, 5, 110)],

    # tout massé sur l'objectif (deux anneaux) : AUCUN flanc à tourner -> doit PUNIR l'enveloppement (M2/M3),
    # favoriser l'appui-feu massif + assaut frontal (M1).
    "concentre":   [(15000, 16000, 10, 55), (15000, 16000, 10, 85)],

    # éclaté en 4 points couvrant TOUS les axes (O/E/N) -> punit l'enveloppement à UN flanc (M3),
    # favorise la double-pince (M2) ou le frontal (M1).
    "disperse":    [(15000, 16000, 8, 80), (14850, 16000, 4, 95), (15150, 16000, 4, 95), (15000, 16150, 4, 95)],

    # FLANC OUEST FAIBLE (2 hommes), fort au centre/est/nord -> doit RÉCOMPENSER M3 (enveloppe par l'ouest),
    # punir le frontal (M1) et toute approche est.
    "faible_ouest":[(15000, 16000, 10, 70), (15150, 16080, 5, 90), (15000, 16150, 3, 90), (14860, 16010, 2, 110)],

    # FLANC EST FAIBLE (miroir) -> M3 (ouest) frappe le flanc FORT et doit ÉCHOUER ; favorise M2 (pince est)
    # ou M1. C'est la paire ouest/est qui teste le plus proprement la rotation du vainqueur.
    "faible_est":  [(15000, 16000, 10, 70), (14850, 16080, 5, 90), (15000, 16150, 3, 90), (15140, 16010, 2, 110)],
}

def total(g):
    return sum(t[2] for t in GEOMETRIES[g])
