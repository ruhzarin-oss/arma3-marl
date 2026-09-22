# Avis de Fable — le « monde de poche » de la phase 2 (22/09/2026)

*Saisi à la demande de Younes : « demande à Fable de t'aider à construire le gymnase — il faut absolument qu'il donne
des résultats vrais pour Arma ». Déposé avant toute ligne de code, comme Fable l'a demandé. En attente de la
validation de Younes sur la forme (proposeur, pas juge) et l'ordre des étapes 0 → 1 → 2.*

## Verdict : faisable sous une seule forme — pas celle proposée

**Impossible** : un simulateur d'Arma agent par agent, LAMBS compris, qui rendrait les taux d'Arma. L'issue de la
phase 2 est un événement de perception, le mécanisme sur lequel le gymnase de combat a menti (0/20). Et la
personnalité d'un monde tient à sa micro-géométrie : on ne la modélise pas, on l'importe.

**Possible : un modèle de course.** La traversée est une course entre le temps que met le détachement à passer et le
temps que met l'ennemi à l'acquérir. Le OÙ vient du moteur (visibilité et réseau routier cuits depuis Arma, monde par
monde) ; le QUAND vient des noyaux mesurés (délais de détection, portée du moteur, vitesse de patrouille).

**Ce n'est pas un juge, c'est un proposeur.** Il crible des millions de situations et en envoie quatre à Arma. Son
certificat : les pièges qu'il propose se confirment dans Arma plus souvent que ceux de l'imagination actuelle.
Cible pré-enregistrée : un piège confirmé pour 100 paires Arma (aujourd'hui : un pour ~300).

Deux corrections : le goulot n'est pas la vitesse de simulation mais les 16 paires Arma par heure ; et le GPU est
optionnel en v1 — numpy vectorisé fait 10⁴-10⁵ épisodes par seconde à ce grain.

## Forme et grain

Unité de prédiction : la **cellule** (monde × type de menace × distances × phase de la patrouille × fenêtre ×
option). Intégration à la seconde. Pas d'apprentissage au pas de temps (une seule décision binaire : rien à apprendre
par PPO).

1. **Géométrie cuite** par monde depuis Arma (graphe routier, corridor, positions candidates, raster de visibilité).
2. **Détachement** : loi de transit mesurée, fenêtre de 90 s, règle d'attente telle qu'écrite dans le SQF.
3. **Menace** : patrouille sur le graphe (vitesses et haltes lues dans les journaux de l'Oracle) ; poste fixe.
4. **Détection** : hasard par (ennemi, homme) = noyau mesuré × visibilité cuite × posture × mouvement × nuit.
5. **Oracle** : le MÊME code de croyance et d'ordres qu'Arma, porté, jamais réécrit.
6. **Liste blanche** : un mécanisme jamais mesuré dans Arma est interdit.

Ancrage contrefactuel : chaque ligne de décision Arma (avec ses vérités) initialise la poche, qui joue les deux
options — 1 672 tests gratuits.

Sur les idées proposées : numpy d'abord ; calage en **population** (≤ 10 scalaires, postérieur par ABC, **32 mondes
de poche** tirés du postérieur) ; MAP-Elites oui (valeur = écart robuste à l'ensemble) ; PAIRED/POET plus tard ; PPO
non ; EvoGP pour distiller la règle que la poche prétend découvrir.

## Certification

La marge se mesure : écart-type d'un écart apparié √(0,30/n) — 0,086 à 40 paires, 0,025 à 480. **La poche ne sera
jamais certifiée sur des cellules à 5 points, seulement sur des cellules à ≥ 15 points : les pièges.**

Partition écrite d'avance : mondes A (calibrage) / mondes B (≥ 8 graines jamais touchées, cuites après les critères,
≥ 1 sans route, ≥ 40 épisodes chacune) / coupure temporelle. Désaccord admis = 1,5 × le plancher Arma-contre-Arma.

Nuls à battre sur B : N0 constante ; N1 taux par monde (gymnase v0) ; N2 imagination actuelle de l'Oracle.

Contrôles internes à chaque construction (tout ou rien) : contact → interception ≥ 95 % ; détachement à 3 km →
≤ 2 % ; sans menace les deux options à ±1 point ; budget 0 → aucun ordre ; apport de l'Oracle dans [+3 ; +20] ;
noyaux conformes aux mesures ; port de l'Oracle ≥ 95 % d'ordres identiques sur les croyances journalisées.

Verdicts : **V1** écart agrégé dans l'IC Arma ; **V2** niveau par monde neuf, Spearman ≥ 0,6 sur ≥ 8 mondes (jamais
passé par personne) ; **V3** enrichissement prospectif — le seul qui adopte.

## Empêcher l'Oracle d'exploiter la poche

Plages de calibrage (hors plage = demande de mesure, pas piège) ; robustesse d'ensemble (≥ 80 % d'accord de signe,
≥ 50 % sur |écart| ≥ 15) ; rien ne compte sans rejeu Arma, registre de précision, quarantaine si la poche devient
moins précise que l'imagination ; chaque infirmation forte = diagnostic d'un mécanisme fautif ; **jamais deux cycles
de poche sans passage par Arma** ; B jamais recalibré ; bras témoin entrelacé chaque nuit.

## À mesurer dans Arma d'abord

Le manque principal : **on a mesuré comment nous les voyons, jamais comment ils nous voient.** La compromission,
c'est eux qui nous voient.

1. **Noyau miroir** : sentinelle et équipage (phares, à pied / embarqué) contre le détachement, en traversée / à
   l'arrêt, debout / accroupi, nuit, 50 à 450 m ; ~240 épisodes, une demi-nuit. Si l'acquisition est ~0 hors contact,
   la compromission est une collision et le noyau devient un rayon.
2. **Plancher Arma-contre-Arma** : 2 cellules × 2 options × 20 rejeux × 2 charges ; ~160 épisodes ; mesure la marge et
   solde la question de la charge.
3. **Qui compromet** : part des compromissions ouvertes par NOTRE feu, dans les journaux existants.
4. **Cuisson** de 20 mondes, par job HMT.

## Ce que la poche apporte à la question en cours

Elle ne tranchera pas les 5 points d'« attendre » — les 480 paires d'Arma le font. Sa valeur : trouver où le signe
bascule ; **donner une horloge** — si elle dit vrai, l'écart dépend de τ = (temps avant le passage de la patrouille) /
(temps de traversée), et le détachement **perçoit** τ (moteur à 900 m) : ce serait la première règle de l'Architecte
qui ne soit pas une constante, fondée sur une perception ; tester la symétrie des armes avant de les coder ;
dimensionner les campagnes.

## Plan

0. **Lire, zéro épisode (1 jour)** : ce qui pose `compromis`, la règle d'attente exacte, ce qui distingue les
   options, qui tire le premier — une page « mécanique de la phase 2 », chaque mécanisme étiqueté mesuré / mesurable /
   inconnu.
1. **Nuls, partition, critères (1 jour CPU)** : `CRITERES_POCHE.md` commité, lecteur unique.
2. **Mesures miroir et cuisson (1 nuit de ferme, après la confirmation)**.
3. **Monde de poche v1 (3-4 jours CPU)** : noyau de course, liste blanche, ABC, ensemble de 32, contrôles.
4. **Épreuve prospective, celle qui adopte (~20 h de ferme)** : 4 cellules poche contre 4 de l'imagination, 40 paires
   chacune.
5. **Dans la boucle** : proposeur de l'Oracle autonome, registre, quarantaine.
6. **L'horloge (~8 h, seulement si 4 passe)** : τ ≪ 1 contre τ ≫ 1 ; règle « attendre si moteur entendu et
   s'approche », distillée par EvoGP, testée en clair.
7. **Version 2** : élargir l'espace d'action, d'abord dans Arma.

Coût : 4-6 nuits de ferme, ~2 semaines de travail, GPU nul en v1.

## Pièges

Définition de `compromis` (tir ou détection) ; durée de l'attente comme artefact ; attente réparée (v2) à
modéliser telle qu'elle est ; la charge ; le véhicule (équipage embarqué, phares) ; l'Oracle omniscient par accident ;
surapprentissage des 8 mondes historiques ; spirale des traits ; bogue de la poche pris pour une découverte (écart
> 30 points suspect par défaut) ; ne rien modifier dans la mission tant que la confirmation vole.
