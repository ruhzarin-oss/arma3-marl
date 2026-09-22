# Confirmation de « toujours attendre » — pré-enregistrement, écrit avant la première paire qui jugera

*22/09/2026, 11 h 55. Étape 1 du plan de Fable (`AVIS_FABLE_22_09.md`), adaptée au résultat de l'étape 0 (e58d72d) :
la perception n'est pas le goulot, la règle candidate de l'Architecte est la constante **C1 = « toujours attendre »**.
Ce fichier est commité AVANT la pose de l'itération 12 de l'Oracle.*

## La question

Dans les situations que l'Oracle choisit, **attendre compromet-il moins que traverser ?**

## Les données qui jugent — et celles qui ne jugent pas

- **Jugent** : uniquement les **paires** des itérations de l'Oracle **numéro 12 et suivantes** (`ORACLE-I012`, …),
  posées après ce commit. Une paire = une même situation (itération, candidat, répétition) sur une même graine, jouée
  sous les deux options ; les deux épisodes doivent être acceptés, avec fin de phase 2 lue et zéro erreur SQF.
- **Ne jugent pas** : les 304 paires existantes (itérations 1 à 11), qui ont servi à *trouver* l'effet (−0,069).
- Les itérations mises en quarantaine par la boucle sont exclues. Un rejeu de réparation remplace un épisode manquant ;
  s'il en existe deux pour la même option, on garde le premier accepté.
- **Intention de traiter** : l'issue est la compromission en fin de phase 2, que le détachement ait atteint la
  décision ou non.
- La population est **celle que choisit l'Oracle** — c'est la distribution du duel, et c'est elle qu'on juge.

## Le nombre et le regard

- **N = 480 paires**, les premières dans l'ordre (itération, candidat, répétition, graine).
- **Un seul regard**, quand les 480 sont là. Avant, le lecteur n'affiche **que le compte**, aucune statistique.
- Puissance attendue : écart-type d'une différence appariée ≈ 0,53 (étape 0) ; à −0,069 le test rejette ~9 fois sur
  10, à −0,05 ~2 fois sur 3.

## Le test

- d = compromission sous attendre − compromission sous traverser, par paire.
- **H0 : moyenne de d = 0 ; H1 : moyenne de d < 0.** Test par **permutation des signes** dans la paire (exact sous
  H0, 100 000 tirages, graine 20260922), unilatéral, **α = 0,05**.

## Les contrôles de l'instrument, faits AVANT de lire H1

1. **Négatif** : 200 jeux où l'option est permutée au hasard dans chaque paire — le test doit rejeter entre 2 % et 9 %.
2. **Positif** : 200 jeux où l'on injecte un effet de −0,07 (des compromissions sous attendre retournées au hasard) —
  le test doit rejeter au moins 70 % des fois.
3. Si l'un échoue, **H1 n'est pas lue**, et on le dit.

## La décision, écrite maintenant

- **H0 rejetée** → l'Architecte **adopte « toujours attendre »** ; l'Oracle change de cible et cherche **où attendre
  perd** (étape 3).
- **H0 non rejetée** → rien n'est adopté ; on rapporte l'estimation et son intervalle ; conclusion : l'avantage
  d'attendre, s'il existe, est trop petit pour compter à 480 paires, et la question passe au **monde** (une horloge).

## Ce qui change dans la boucle pendant la confirmation

- **L'adoption automatique de l'Architecte est suspendue** : son réapprentissage toutes les 2 itérations regardait
  les données trop souvent (étape 0e : porte aveugle ; Fable : regards répétés). Un résultat qu'il produirait est mis
  de côté, jamais installé.
- La boucle écrit à chaque itération **le compte** des paires de confirmation, rien d'autre.
- Rien d'autre ne change : l'Oracle joue déjà chaque situation sous les deux options.

## Description, sans valeur de test

Estimation de la moyenne de d et IC 95 % (bootstrap par paire, puis par monde), signes par monde, sous-groupes
(poste proche, patrouille proche) — affichés seulement **après** la décision, pour comprendre, pas pour décider.

## Amendement ( 22/09, 14 h 10 ) — les paires suivantes viennent du banc multiple

A partir de la paire 11, les episodes de confirmation sont joues comme cellules du banc multiple ( multiplexeur de
l Oracle, REGLES_DE_L_ORACLE.md amendement 5 ) : meme code de mission, memes portes, plus la porte de pouls. L hypothese,
le test, le seuil, N = 480 et le regard unique ne changent pas. A la lecture unique, l ecart par paire sera DECRIT
separement pour les paires du banc seul et celles du banc multiple ( champ `banc_joue` du job ) ; cette description ne
change pas la decision.
