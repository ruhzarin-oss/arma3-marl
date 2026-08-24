# LE REJEU INSTRUMENTÉ — deux causes éliminées, la panne reste inexpliquée

**24/08/2026, 12 h 38.** Rejeu de la graine 1 à l'identique, instrumentation **passive**
(`681c65c`). **Preuve qu'elle ne change rien : la porte rend exactement les mêmes chiffres**
qu'au rejeu non instrumenté — G1 −9,4 contre la frontale, −31,0 contre le flanc.

## ⛔ La prédiction de Fable est réfutée

> *« part de la prise ~0 % sous la normalisation actuelle, substantielle sous une
> normalisation globale »*

| itération | entrées de prise | avantage **brut** | avantage **normalisé pas par pas** |
|---|---|---|---|
| 500 | 128 | 1,07 % | **1,66 %** |
| 700 | 240 | 1,45 % | **2,19 %** |
| 950 | 408 | 1,35 % | **2,52 %** |
| 1150 | 412 | 1,45 % | **2,61 %** |

**La normalisation pas par pas AMPLIFIE la part des pas de prise, elle ne l'écrase pas.**
Sa mécanique en trois coups ne se vérifie pas sur données réelles.

## ✅ Sa remarque annexe, elle, est confirmée — et elle explique son propre bras R

**Le centrage retire 18 à 43 % de l'amplitude brute** sous forme de **composante commune**.
C'est exactement là que part la rente de γ : elle est un soulèvement identique pour tous les
environnements, donc elle disparaît dans la moyenne soustraite **avant d'atteindre le
gradient**.

> **γ = 1,0 contre 0,99 ne donnait rien non pas parce que la rente est négligeable, mais
> parce que le pipeline la filtre.** L'arithmétique de Fable était juste ; son effet est
> annulé un étage plus bas.

## Ce que la courbe dit, et qui est SAIN

Les prises deviennent **trente fois plus nombreuses** (12 → 412) et leur part de l'avantage
**reste plate à ~1,4 %**. Ce n'est pas une panne : **c'est le critique qui fait son travail.**
Une réussite qui devient prévisible voit son avantage se réduire. C'est l'attribution de
crédit qu'on veut.

## ⛔ Donc : la non-condensation reste INEXPLIQUÉE

| hypothèse | état |
|---|---|
| la rente de γ (17/08) | **éliminée** — 5,3 % contre 5,7 % à budget égal, et on sait maintenant pourquoi |
| le budget seul | **insuffisant** — 1 200 itérations des deux côtés, une graine sur deux échoue |
| le continuum de netteté | **éliminée** — le 13/08 est presque aussi plat et réussit |
| le portefeuille (dispersion d'équipe) | **éliminée** — les trois groupent pareil, celui qui groupe le plus réussit |
| **la normalisation pas par pas** | **éliminée comme cause du signal rare** — elle l'amplifie |

**Ce qui reste établi et non expliqué** : l'argmax de la graine 1 est un **champ
spatialement constant** (87 % des décisions sur deux actions, écart top1−top2 de 0,152) qui
marche en ligne droite et manque l'objectif de 103 m, alors que la même politique
échantillonnée rend 42 %.

⭐ **Cliquet : éliminer proprement vaut mieux qu'expliquer vite.** Cinq hypothèses sont
tombées sur mesure en deux jours, dont deux de Fable et deux de moi. **Aucune réparation n'a
été faite sur une cause supposée** — c'est exactement ce que ces rejeux ont acheté.

## ⚠️ Limite de cette mesure

J'ai mesuré la part de **|avantage|**, pas la **norme du gradient**. C'est un proxy : le
gradient réel pondère aussi par ∇log π. Fable demandait la seconde, je livre la première.
Un pas de prise pourrait porter peu d'avantage et beaucoup de gradient. **À refaire si la
piste revient.**

## La suite prescrite par Fable, et qui reste entière

**Le film au lieu de la dernière image** : rejouer les graines 0 et 1 en sauvant un point
toutes les K itérations, puis évaluer **argmax et échantillonnage sur chaque point**.

- Si l'argmax de la graine 1 **n'a jamais** été bon → le sort se scelle tôt, c'est une
  bifurcation d'initialisation.
- S'il a été bon **puis s'est défait** → la condensation est un événement fluctuant, et
  **sélectionner le point sur l'argmax résout le problème sans toucher à la perte.**

⚠️ Et son garde-fou, à respecter dès maintenant : **ne jamais sélectionner sur les graines
de test de la porte.** Il faudrait un troisième jeu — entraînement / sélection / test —
sinon la porte cesse d'être une porte.
