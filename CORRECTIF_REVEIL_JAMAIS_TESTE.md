# CORRECTIF — LES SESSIONS « RÉVEILS ALTERNÉS » N'ENVOYAIENT AUCUN RÉVEIL

17/08/2026, ~03 h. Découvert en préparant la sonde d'unité.

## Ce qui s'est passé

Le script qui devait ajouter le mode `compare` à `prevol.py` s'est arrêté sur une
**assertion précédente** — une ancre du socle qui avait changé. Le patch de `prevol.py`
venait après, dans le même fichier, et n'a jamais été appliqué. **Je n'ai pas vérifié, et
j'ai lu les résultats comme si le mode existait.**

`MODE = "compare"` tombait donc dans le comportement par défaut : ni réveil, ni alternance.

## La table corrigée

| session | annoncé | RÉEL | T5 rouge |
|---|---|---|---|
| porte, 21 h | sans réveil | sans réveil | 0 / 50 |
| nuit NATIF | réveil natif | **réveil natif** (`banc_live.py`) | 24 / 34 |
| « compare » 1.12.0 | réveils alternés | **AUCUN réveil** | 17 / 20 |
| normal 1.12.0 | sans réveil | sans réveil | 2 / 12 |
| « compare » 1.13.0 | réveils alternés | **AUCUN réveil** | 2 / 16 |
| échauffement 45 s | sans réveil | sans réveil | 0 / 4 |
| échauffement 150 s | sans réveil | sans réveil | 3 / 3 |

## Ce que ça retire

**« Le réveil est réfuté » est SANS FONDEMENT. Le réveil n'a jamais été testé.** Il retourne
au registre des hypothèses, intact. C'était ma cinquième cause annoncée ; elle n'a pas été
réfutée, elle n'a pas été mesurée.

## Ce que ça donne, et c'est plus fort que ce que ça retire

Cinq sessions ont désormais un contexte **rigoureusement identique** — sans réveil, socle
sans effet fonctionnel entre les versions :

| session | tirages | T5 rouge | taux |
|---|---|---|---|
| porte 21 h | 50 | 0 | **0 %** |
| « compare » 1.12.0 | 20 | 17 | **85 %** |
| normal 1.12.0 | 12 | 2 | **17 %** |
| « compare » 1.13.0 | 16 | 2 | **13 %** |
| échauffement 45 s | 4 | 0 | **0 %** |
| échauffement 150 s | 3 | 3 | **100 %** |

**De 0 % à 100 % dans des conditions identiques.** L'effet-session n'est plus une intuition
tirée d'une pièce confondue : c'est la seule lecture qui reste debout. Et il rend
rétrospectivement toutes mes sondes de la nuit sans puissance — chacune tenait dans **une**
session, donc chacune tirait à pile ou face. ⟨Fable : *« leurs réfutations sont des lancers
de pièce »*⟩

## Le cliquet

Ce patch avait déjà échoué **en silence**. Désormais tout patch **imprime ce qu'il a posé**,
et la vérification porte sur le fichier **après écriture**, pas sur l'absence d'exception.
