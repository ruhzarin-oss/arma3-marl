# CRITÈRES FIGÉS — L'ORDRE D'ASSAUT FINAL (avant les données)

Figés le 2026-07-28, AVANT le run de mesure. Non négociables après coup.

## LA CAUSE, MESURÉE
`doSuppressiveFire` **arrête l'unité**. Dans `HMT_ENVELOP_APPLY`, tout attaquant ayant une
ligne de vue recevait `doTarget` + `doSuppressiveFire` : il se figeait. C'est l'enlisement à
28-110 m constaté sur 28 opérations les 14/06 et 28/07, jamais expliqué jusqu'ici.

## LE MÉCANISME AJOUTÉ
`--assaut_final DIST` (défaut 0 = désactivé, non régressif). Sous DIST mètres du plus proche
attaquant, l'élément d'assaut :
- **cesse de tirer** (`doWatch objNull`, `doTarget objNull`, aucun `doSuppressiveFire`),
- **se lève et court** (`setUnitPos "UP"`, `forceSpeed 100`),
- reçoit un `doMove` répété sur l'objectif.
Les fixeurs, eux, continuent de supprimer. En frontal il n'y a pas de fixeur : tout le monde
franchit. C'est le dernier bond du manuel : l'élément d'assaut ne tire pas, la base de feu couvre.

## PREUVE QUE LE MÉCANISME EST ACTIF (déjà obtenue)
Cellule A=12 vs D=12, frontal, `--assaut_final 40` : FOB PRIS au tick 87 (26 → 19 m en quatre
pas après déclenchement), 6 pertes sur 12. La même cellule sans l'ordre était **0 prise sur 3**,
arrêtée à 58-60 m. n=1 : preuve d'activation, pas encore une mesure.

## CE QUI EST MESURÉ ICI
A=12 vs D=12, 120 pas, `--assaut_final 40`, 3 répétitions par mode (frontal et envelop) = 6 ops.

**Seuil pré-enregistré : ≥5 opérations sur 6 RÉSOLUES** (FOB pris OU escouade anéantie).
- ≥5/6 → l'ordre d'assaut final entre au protocole. Le banc Arma redevient capable de
  trancher, et la certification du seuil de manœuvre (D=8) devient relançable.
- <5/6 → l'ordre ne suffit pas ; on ne relance aucune certification avant d'avoir compris.

## CE QUI N'EST PAS MESURÉ ICI, ET NE DOIT PAS ÊTRE LU
La comparaison frontal / envelop. Trois répétitions par bras ne tranchent rien, et le but de
ce run est la RÉSOLUTION, pas la doctrine. Tout écart entre les deux modes est du bruit tant
qu'un run dimensionné ne l'a pas confirmé.

## INTERDICTIONS
Pas de retouche de DIST, du nombre de répétitions ni du seuil après avoir vu un chiffre.
