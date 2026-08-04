# Étape 5 — critères écrits AVANT toute mesure

*5 août 2026, 00h30. Aucune donnée de ce test n'existe au moment où ce fichier est écrit.*

## La règle que j'applique, et pourquoi

Cette nuit, **quatre fois**, j'ai affirmé de mémoire ce qu'il fallait lire dans le code. La
dernière — « l'agent détourne trop tard » — a coûté une demi-heure de GPU et un agent
dégradé, alors que le défaut **n'existait plus** : l'agent achetait déjà son écart à 74 %
du rayon, le niveau du crochet scripté.

> **Avant d'ajouter quoi que ce soit pour corriger un défaut, mesurer que le défaut existe
> encore sur la version courante.**

Ce fichier est l'application de cette règle à l'étape 5.

## Le défaut supposé

L'agent apprend dans la sandbox sur **`expo`**, une fonction analytique que j'ai construite
à partir de mesures ponctuelles sur Arma : demi-cône de 35°, plateau puis chute, base de
0,45 décroissant avec la distance, facteur de posture en marche à 120 m.

Le corpus, lui, contient la **mortalité réellement observée** — 563 000 observations,
mortalité à 30 secondes, capturée sur un front autonome sans intervention.

**Hypothèse : `expo` et le risque réel divergent, et c'est pourquoi l'agent qui excelle
dans la sandbox échoue sur Arma.**

Si elle est vraie, l'étape 5 a un objet : remplacer la fonction inventée par un risque
**appris sur le corpus**. Si elle est fausse, `expo` est fidèle et l'étape 5 doit chercher
ailleurs — dans le rejeu des trajectoires, pas dans la fonction de coût.

## Le test

Pour chaque observation du corpus, on dispose de la géométrie (positions, caps des ennemis)
et de l'issue à 30 secondes. On compare deux prédicteurs de la mort :

1. **`expo` seule** — la fonction analytique de la sandbox, calculée depuis la géométrie
2. **un prédicteur appris** sur les mêmes entrées géométriques
3. **le plancher** — le taux de base, sans aucune information

Mesure : aire sous la courbe ROC, sur des données tenues à l'écart.

## Les critères

**E0 — VALIDITÉ.** Le prédicteur appris doit battre le plancher d'au moins 0,05 d'AUC.
Sinon la géométrie ne prédit rien sur ce corpus, et le test n'a pas d'objet.

**E1 — LE DÉFAUT EXISTE-T-IL ?**
- si `expo` est à **moins de 0,03 d'AUC** du prédicteur appris → **`expo` est fidèle**, le
  défaut n'existe pas, et remplacer la fonction de coût serait un remède sans mal ;
- si l'écart **dépasse 0,03** → le défaut est établi, et l'étape 5 a son objet.

**E2 — CONTRÔLE DE SENS.** `expo` doit être **positivement** corrélée à la mortalité. Si
elle l'est négativement ou pas du tout, ce n'est pas un écart de calibration mais une
erreur de signe ou de domaine, et il faut la traiter comme telle avant tout apprentissage.

**E3 — CONTRÔLE NUL.** Sur des étiquettes brassées, les trois prédicteurs doivent retomber
à 0,5. Sinon la chaîne d'évaluation fuit.

## Ce que le test ne dira pas

Il ne dira pas si un risque appris ferait passer le banc à 150 m. Il dit seulement si la
fonction actuelle est infidèle — condition nécessaire, pas suffisante.

## Condition d'échec, déposée

Si **E1 conclut que `expo` est fidèle**, l'étape 5 ne passe pas par la fonction de coût.
Elle devra alors porter sur ce que le programme désignait vraiment : **entraîner l'agent
sur des trajectoires rejouées** plutôt que sur des épisodes engendrés à la volée — et ce
sera un autre test, avec ses propres critères écrits avant.
