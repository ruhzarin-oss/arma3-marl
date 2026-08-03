# CRITÈRES DU RE-VERDICT — FIGÉS AVANT LE PREMIER RUN

Écrit le 27/07/2026 vers 01 h, **avant** d'avoir lancé quoi que ce soit et avant d'avoir
vu le moindre résultat. Toute modification ultérieure de ce fichier doit être datée et
justifiée, et invalide les runs qui la précèdent.

## La question posée
La courbe n°1 (probabilité de toucher, mesurée sur Arma) suffit-elle, à elle seule, à
faire rendre au sandbox les verdicts qu'Arma rend ?

## Le protocole
Même politique, deux mondes. La politique doit être **insensible au monde** : donc
SCRIPTÉE. Une politique apprise dans l'ancien monde a appris à exploiter le sanctuaire
au-delà de 110 m ; la rejouer mesurerait son inadaptation, pas la fidélité du monde.

- **Ancien monde** : `hit=0.06` partout sous 110 m, puis zéro. Profil de posture posé à
  la main `[1.00, 0.50, 0.20]`.
- **Nouveau monde** : courbe mesurée sur Arma + les trois conversions mesurées
  (`sec_par_pas=3.28`, `tir_par_pas=1.15`, `degat_par_impact=0.233`).
- Mêmes graines, mêmes effectifs, même géométrie défensive entre les deux mondes.

## Ce qui est au banc, et ce qui n'y est pas

**VERDICT 1 — le flanc contre une LIGNE défensive à arc de tir paie.**
Référence Arma : le flanc prend l'objectif 2 à 3 fois plus souvent, à un tiers du coût.
→ **Test d'acceptation PRINCIPAL.** Ne dépend d'aucun ingrédient non mesuré : c'est de
la géométrie d'exposition, exactement ce que la courbe n°1 vient de rendre honnête.

**VERDICT 3 — l'assaut saturé rend les postures peu payantes.**
→ Test d'acceptation **secondaire**.

**VERDICT 2 — le feu ne fait presque rien aux retranchés.**
→ **HORS BANC, et c'est écrit d'avance.** Il repose sur la suppression, qui n'est pas
mesurée. S'il échoue, c'est attendu et non disqualifiant. **S'il PASSE, c'est SUSPECT** —
il passerait pour de mauvaises raisons. Il deviendra le test d'acceptation de la
courbe n°2, pas de la n°1.

**Aucun de ces verdicts n'a servi à calibrer.** On a calibré de la micro-physique
(toucher, vitesses, cadence, dégât par impact). Les trois verdicts sont donc formellement
hors-échantillon.

## Seuils, chiffrés d'avance

| | |
|---|---|
| Volume | **200 épisodes par bras et par monde**, graines identiques entre bras |
| **Verdict 1 — succès** | dans le NOUVEAU monde : prise du flanc **≥ 1,5×** celle du frontal **ET** pertes par prise **≤ 0,6×** celles du frontal |
| **Verdict 1 — contre-épreuve** | dans l'ANCIEN monde, cet écart doit être **absent ou inversé**. S'il était déjà là, toute l'analyse est à refaire — il faut le savoir. |
| **Verdict 3 — succès** | deux doctrines de posture opposées diffèrent de **moins de 10 points** de taux de prise dans le nouveau monde |
| Métrique commune | **exposition par mètre gagné** — la variable qui sépare les gagnants (0,65) des perdants (1,21). Elle doit séparer les bras dans le bon sens. |

Le couloir 1,5× / 0,6× est **volontairement plus large** que le 2-3× / un tiers d'Arma :
on valide la direction et l'ordre de grandeur, pas le chiffre.

## Arrêt
Si les intervalles des deux bras se chevauchent encore à 200 épisodes, **on double une
seule fois** (400). Toujours ambigu à 400 = le scénario ne discrimine pas → on **redessine
le scénario**, on ne moud pas plus de graines.

## Interdits, sans exception
1. **Retoucher une courbe mesurée parce qu'un verdict ne passe pas.** Les verdicts sont
   le jeu de test ; les arranger détruit leur valeur et fabrique un menteur certifié.
2. Relancer « pour voir ». Un run enregistré compte. On ne relance qu'avec un changement
   déclaré et daté.
3. Conclure quoi que ce soit sur la qualité du monde à partir du bras DIAGNOSTIC (les
   politiques de l'ancien monde rejouées dans le nouveau). Leur effondrement démontre que
   l'ancien monde enseignait une tactique suicidaire — rien de plus.

## Ce qu'on conclut selon le résultat
- **Flanc bat frontal dans le bon ordre de grandeur** → le monde rend le verdict n°1.
  On avance sans retoucher les courbes.
- **Bonne direction, mauvais rapport** → fidélité directionnelle acquise. On le note, et
  on s'interdit de retuner pour forcer le rapport.
- **Mauvaise direction** → la courbe n°1 seule ne suffit pas. L'ingrédient manquant est
  probablement la suppression (l'élément de fixation ne sert à rien si le feu ne fixe
  pas). **C'est un résultat, pas un échec** : il justifie et priorise la courbe n°2.
