# CRITÈRES — L'AXE DU STRESS (figés avant le premier run)

Écrit le 27/07/2026, **avant** tout entraînement avec le stress branché.

## Pourquoi ce test, et pourquoi celui-là d'abord
SIROCCO-V2 section 0 : *« Le système immunitaire n'a aucun objectif à prendre. Poussée à
fond, la métaphore produit un agent qui survit magnifiquement et ne prend rien — exactement
ce que le banc FIBUA a appris à refuser. »*

L'axe du stress est **le seul mécanisme franchement offensif** des quatre codés. Sans
`audace`, tout SIROCCO ne sait que se protéger.

**Et c'est pour ça qu'on le mesure sur la PRISE-À-PERTES, pas sur des compteurs internes.**
« seuil 0,175 → 0,134 » dit que le mécanisme fait ce qu'il a été codé pour faire. Ça ne dit
pas que l'escouade prend davantage. C'est la leçon du 27/07 : mon témoin d'angle mort
bougeait comme prévu et n'expliquait rien.

## Le branchement, et pourquoi celui-là
`audace` multiplie l'exposition qu'on accepte de payer. Il n'y a pas de cascade à moduler
dans ce sandbox — elle n'est pas branchée. Le point d'application honnête est donc le
**champ de risque** : **le prix perçu est divisé par l'audace.**
- audace > 1 → le terrain paraît moins cher → on entre
- audace < 1 → le terrain paraît plus cher → on se protège

Ce n'est pas falsifier la perception : c'est le poids de décision appliqué au perçu.
Personne ne perçoit son adrénaline ; on perçoit le monde autrement. L'agent n'a donc rien
de plus à lire.

**Vérifié au smoke** : l'adrénaline monte de 0,007 à 0,40 quand le temps file, l'audace suit
de ×1,01 à ×1,32. Conforme au chiffre annoncé (×1,00 → ×1,35).

## Le protocole
Deux bras, mêmes graines, tout identique sauf le stress.
- **TÉMOIN** : arc + champ de risque (la meilleure configuration connue)
- **STRESS** : le même + l'audace qui pondère le champ, mission `assaut`

3 graines par bras, 150 rondes, évaluation sur 300 épisodes avec une graine différente.

## La métrique, et elle est nouvelle
**PRISE-À-PERTES = prise ÷ pertes par prise.** Plus c'est haut, mieux c'est.

C'est la métrique du banc FIBUA — celle qui refuse un agent qui survit sans prendre. On
la préfère ici à l'exposition par mètre, parce que la question du stress n'est pas
« manœuvre-t-il mieux ? » mais **« entre-t-il ? »**.

Repères mesurés dans le même monde (bras champ, 3 graines) : prise ≈ 94,5 %,
exposition ≈ 0,0180.

## Seuils, figés
- **SUCCÈS** : prise-à-pertes **≥ +15 %** contre le témoin, mesuré dans le même run.
- **SUCCÈS PARTIEL** : la prise monte d'au moins 2 points **sans** que les pertes par prise
  montent de plus de 5 %.
- **ÉCHEC** : la prise ne monte pas, ou monte au prix de plus de pertes — c'est-à-dire que
  l'audace fait charger, pas entrer. **La distinction est tout l'objet du test.**
- **CONTRE-ÉPREUVE** : le bras témoin doit reproduire ≈94,5 % de prise et ≈0,018
  d'exposition. Sinon autre chose a bougé et la comparaison ne vaut rien.

## Ce qu'on surveille en plus, sans en faire un seuil
- L'exposition par mètre : si elle monte beaucoup pendant que la prise monte un peu,
  l'audace a rendu l'agent téméraire et non habile.
- Le cortisol en fin d'épisode : le mécanisme d'épuisement doit s'activer sur les épisodes
  coûteux, sinon la moitié de l'axe est morte.

## Interdits
1. Retoucher les bornes de l'audace (0,60–2,00) ou la mission après avoir vu les résultats.
2. Déplacer un seuil.
3. Conclure sur la seule prise. Une prise qui monte en payant plus, ce n'est pas de
   l'audace — c'est de l'imprudence, et le banc FIBUA a déjà tranché contre.
