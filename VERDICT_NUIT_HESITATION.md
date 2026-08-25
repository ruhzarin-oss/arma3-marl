# LA NUIT DE L'HÉSITATION — **effet NON RÉSOLU**, et le banc n'a pas bougé

**25/08/2026, 20 h 25.** Prédicat `PREDICAT_NUIT_HESITATION.md` (`80ac6e9`), écrit avant le
premier épisode. Deux bras **entrelacés dans la même nuit**, **même artefact**, mêmes graines
d'action au même rang, τ = 1. Lecteur déposé, inchangé.

| | n | prises | IC95 | condition 2 | coups médians |
|---|---|---|---|---|---|
| **HÉSITANT** | 65 | **29,2 %** | [18,2 ; 40,3] | 1,86 m/pas ✓ | 171 |
| **FIGÉ** | 66 | **39,4 %** | [27,6 ; 51,2] | 2,42 m/pas ✓ | 184 |

> ## Écart = **−10,2 points** · IC95 **[−26,3 ; +6,0]** — **il contient zéro**

## ✅ Ce que la nuit établit franchement : LE BANC N'A PAS BOUGÉ

Le bras figé rend **39,4 %**, dans la fenêtre **33,6 ± 12** posée d'avance.
**Les chiffres du 23/08 tiennent** : natif 30,7 %, politique 33,6 %, et leur « aucune
revendication ». **L'issue 4 ne se déclenche pas.**

## ⛔ L'effet du décodeur : NON RÉSOLU À CE BUDGET

C'était **écrit d'avance** : *à 67 épisodes par bras, cette nuit détecte ~20 points ; en
dessous, c'est non résolu, et c'est une issue acceptée, pas un échec.* L'écart vaut
**−10,2**, son intervalle **contient zéro**. **On ne conclut pas.**

**La direction est cohérente avec le gymnase** (−19,6 pour cet artefact) et **l'amplitude en
fait à peu près la moitié** — mais ça ne se cite pas comme un résultat.

## ⚠️ UNE FAUTE DANS MA FAÇON D'AVOIR CODÉ LES RÈGLES

**Mes quatre issues ne pavaient pas l'espace.** L'issue 1 était définie comme
*« hésitant ≈ figé − 20 »*, l'issue 3 comme *« < figé − 25 »*, l'issue 2 comme
*« > −10 »*. **La bande entre −10 et −20 n'était assignée à personne**, et mon `else`
l'a versée à l'issue 1. Le script a donc imprimé « ISSUE 1 » pour un écart de **−10,2**,
qui n'est pas « ≈ −20 ».

**La règle de puissance, elle, était sans trou, et c'est elle qui tranche : non résolu.**

⭐ **Cliquet : des issues pré-inscrites doivent PAVER l'espace des résultats.** Une bande
non assignée devient un `else`, et un `else` décide à la place du prédicat.

## ⚠️ Et le bras figé est DISCORDANT avec lui-même

Concordance recalculée d'avance pour le n réel : **14 points** sur des moitiés de ~31.

| | première moitié | seconde moitié | écart |
|---|---|---|---|
| hésitant | 25,0 % (n=32) | 33,3 % (n=33) | 8,3 ✓ |
| **figé** | **46,9 %** (n=32) | **32,4 %** (n=34) | **14,5** ⛔ |

**Le bras figé dépasse son propre seuil de concordance.** Son 39,4 % est donc **fragile**,
et le motif est instructif : l'hésitant **monte** au fil de la nuit, le figé **descend**.
⚠️ **Aucun des deux mouvements n'est significatif seul** — mais ils vont en sens opposés, et
c'est précisément le genre de chose qu'un bras unique aurait maquillée en tendance.

## Ce qui en découle pour la décision du 24/08

**Le déclencheur de l'issue 3 ne se déclenche pas** : il fallait une pénalité de plus de
25 points, on mesure −10,2 avec un intervalle qui contient zéro. **La décision « l'agent
hésite » n'est donc pas remise en délibéré.**

**Mais elle n'est pas non plus soutenue par cette nuit.** Elle reste ce qu'elle était :
un choix fondé sur le gymnase et sur le raisonnement — *on lit l'objet qu'on a optimisé* —
et **Arma ne l'a ni confirmé ni infirmé à ce budget**.

## Ce qu'il faudrait pour trancher, et qui n'est pas lancé

Un effet de 10 points demande **~4 fois ce budget** : environ **270 épisodes par bras**,
soit **36 heures**. **Ça ne se lance pas sans arbitrage** : c'est cher pour départager un
choix qui, en l'état, ne coûte rien de mesurable dans Arma.
