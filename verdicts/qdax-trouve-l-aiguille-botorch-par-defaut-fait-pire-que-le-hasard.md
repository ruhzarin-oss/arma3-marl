# QDax trouve l'aiguille mieux que le hasard ; BoTorch par défaut fait pire que le hasard ; aucun Oracle n'ajoute de diversité

*17/09/2026 — statut ETABLI — domaine : méthode (banc des Oracles, sans Arma)*
*Critères pré-enregistrés : `oracle/CRITERES_BANC_ORACLE.md` (dépôt c5042fc, calibrage et fumées sur graines disjointes
consignés avant). Lecture unique : `oracle/lire_banc_oracle.py`, sortie `oracle/resultats/lecture.txt`.*

## Énoncé

**Le banc.** 4 mondes cachés × 20 répétitions × 7 oracles. Chaque oracle dispose de 1920 épisodes bruités, puis d'une
confirmation commune de 150 épisodes par candidat.
- **QDax (MAP-Elites) est le seul classé UTILE.** Il trouve la faille étroite 13 fois sur 20 (me4) et 12 fois sur 20
  (me8), contre 7 sur 20 pour le tirage uniforme, sans fausse faille dans le monde nul.
- **BoTorch avec ses réglages par défaut fait pire que le hasard.** Il trouve l'aiguille 1 fois sur 20, et 0,50 région
  sur 4 contre 1,65 pour l'uniforme.
- **BoTorch aux longueurs de corrélation bornées et l'Oracle à cases du plan** égalent le hasard, sans être utiles :
  9/20 et 11/20 sur l'aiguille, 1,45 et 1,60 région sur 4.
- **Aucun oracle n'ajoute de diversité** : sur les quatre failles, aucun ne dépasse l'uniforme d'une région.

## Résultats (20 répétitions)

| oracle | nul : fausses | aiguille trouvée | quatre failles : régions | large faible | budget joué en faille | durée |
|---|---|---|---|---|---|---|
| parfait (borne haute) | 0/20 | 20/20 | 3,60 [3,35 ; 3,85] | 8/20 | 100 % | — |
| uniforme (borne basse) | 0/20 | 7/20 | 1,65 [1,15 ; 2,10] | 11/20 | 12,0 % | — |
| cases du plan | 0/20 | 11/20 | 1,60 [1,20 ; 2,00] | 12/20 | 14,9 % | < 1 s |
| **qdax_me4** | 0/20 | **13/20** | 1,95 [1,55 ; 2,35] | 11/20 (1 fausse) | 12,8 % | 2 s |
| **qdax_me8** | 0/20 | **12/20** | 1,60 [1,25 ; 2,00] | 8/20 | 12,2 % | 2 s |
| botorch_ts_court | 0/20 | 9/20 | 1,45 [1,15 ; 1,75] | 12/20 | 12,9 % | 8 s |
| botorch_ts (défaut) | 0/20 | 1/20 | 0,50 [0,30 ; 0,70] | 3/20 | 5,4 % | 6 s |

Écart avec les cases du plan, en régions trouvées : QDax me4 +0,35 [−0,20 ; +0,90] sur les quatre failles, +0,10
[−0,20 ; +0,40] sur l'aiguille. BoTorch défaut −1,10 [−1,55 ; −0,65] sur les quatre failles.

## Ce que cela apprend

1. **Le vrai goulot est le bruit, pas l'algorithme de recherche.** Un épisode donne +2, −2 ou 0 : avec 4 épisodes par
   situation, aucun oracle ne sait où il est. Tous jouent 12 à 15 % de leur budget en faille, à peine plus que le hasard
   (12 %). L'oracle parfait trouve 3,6 régions sur 4 : l'écart vient de **savoir où regarder**, pas de la confirmation.
2. **L'hypothèse écrite avant est réfutée** : BoTorch borné n'est pas le meilleur sur l'aiguille (9/20 contre 13/20
   pour QDax). QDax gagne sans modèle, parce qu'il garde les meilleures situations de chaque zone et mute autour.
3. **Un modèle mal réglé est pire que pas de modèle.** BoTorch par défaut apprend une longueur de corrélation trop
   longue (1,44 sur la distance, vu à la fumée) : il lisse les failles et dépense son budget en bord d'espace.
4. **La diversité ne se gagne pas encore** : aucun oracle ne trouve plus de failles distinctes que le hasard. Pour y
   arriver, il faudrait plus d'épisodes par situation, ou des perceptions qui disent où chercher.
5. **Pour le plan Architecte / Oracle** : QDax est le candidat Oracle, rapide (2 s) et le seul utile. L'Oracle à cases
   du plan n'est pas meilleur que le hasard à ce niveau de bruit.

## Faute évitée avant le banc

**Candidats de l'Oracle à cases pris au centre des cases.** Ces centres tombent hors des failles étroites : 0,10 région
en W2 au calibrage. Corrigé avant les répétitions 0 à 19 : les candidats sont les situations explorées au meilleur z̄.

## Falsificateur pré-enregistré

Un oracle n'est UTILE que si le contrôle nul tient et s'il bat l'uniforme de 5 répétitions sur l'aiguille ou d'une
région sur les quatre failles. Tenu pour QDax (aiguille) ; **franchi** pour BoTorch (les deux variantes) et pour les
cases du plan.
