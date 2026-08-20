# NATIF MESURÉ — 68,2 %, et la comparaison n'est PAS encore permise

**20/08/2026, 20 h 54.** Prédicat `DEPOT_NATIF.md`, écrit le **16/08 avant tout épisode**.
Socle 5.4.0, canal `sv_vz_preserve_10hz`, minuteur dérivé à 640 s.
134 épisodes lancés, 124 relevés écrits.

## LE CHIFFRE

**PRISE** = un attaquant **VIVANT** à moins de **25 m** (`assault_terrain.py:814`, « comme Arma »).

| | prises | n | taux |
|---|---|---|---|
| passe 1 | 39 | 54 | **72,2 %** |
| passe 2 | 34 | 53 | **64,2 %** |

**Écart 8,1 points — sous le seuil de 10 déposé. LES DEUX PASSES CONCORDENT.**

> ## ➤ NATIF = 68,2 %   ·   n = 107   ·   IC95 [59,4 ; 77,0]

C'est la **première mesure valide de NATIF**. Toutes les tentatives précédentes tournaient
avec un prévol absent ou rouge — le 16/08, 35 épisodes, 35 prévols rouges, zéro relevé.

## LES CONDITIONS ÉLIMINATOIRES, UNE PAR UNE

| n° | condition | état |
|---|---|---|
| 1 | **prévol VERT** | **levée** — 123 sur 134 ; les 11 refus sont nommés |
| 2 | **le natif BOUGE** (> 1 m/pas) | **levée** — médiane 3,05 m/pas ; **16 épisodes écartés** pour l'avoir manquée |
| 3 | **le natif TIRE** (≥ 1 coup médian) | **⛔ NON LEVÉE** |
| 4 | 12 colonnes dans la plage du gymnase | non contrôlée ici |

### ⛔ La condition 3 ne peut pas être vérifiée sur ces données

**`banc_live.py` n'enregistre aucun compte de coups.** Le seul indice disponible est la
colonne `def` : **52 %** des épisodes voient au moins un défenseur mourir. Ce n'est **pas**
la mesure déposée, qui exige un coup médian par épisode.

⚠️ Le prédicat dit qu'un épisode manquant une condition **n'entre pas dans le compte**. Je ne
peux donc pas affirmer que les 107 épisodes la satisfont — seulement qu'aucun ne l'a démentie.
**À réparer : un compteur de coups dans `banc_live.py`, avant la nuit politique.**

## LA TAILLE, DÉCLARÉE

Le prédicat fixait **67 épisodes par passe**, « le même nombre que la politique, pour que la
comparaison soit **appariée** ». On a **54 et 53**. Cause nommée : 11 refus de prévol (dont
**neuf T7 à `vue:0`** — l'anneau fixe par session qui refait surface à l'échelle de la nuit)
et 16 écarts sur la condition 2. **L'appariement n'est plus exact.**

## ⛔ CE QU'ON NE PEUT PAS ENCORE DIRE

La politique vaut **44,8 %** dans les dépôts. NATIF vaut **68,2 %**. Il serait tentant de
conclure que **l'IA native bat la politique de 23 points** — et l'IC95 de NATIF ne recouvre
pas 44,8.

> ### **CETTE COMPARAISON N'EST PAS PERMISE.**
> Le 44,8 % a été mesuré **sous un autre prévol**, dans un monde qui n'était pas certifié.
> `VERDICT_PORTE_QUATRE_LIGNES.md:59` le disait déjà : *« la politique rejouée sous le même
> prévol — sans quoi le 44,8 % et NATIF viennent de deux mondes »*.
>
> **Comparer maintenant reproduirait exactement la faute de la semaine :** lire deux chiffres
> nés d'instruments différents comme s'ils mesuraient la même chose.

## CE QUE LE PRÉDICAT AVAIT DÉCIDÉ D'AVANCE

> *« NATIF ≥ politique → la politique n'apporte rien sur ce banc, et le 44,8 % ne se cite plus
> comme un acquis. C'est l'issue la plus coûteuse, et elle est acceptée d'avance. »*

Cette issue est désormais **plausible et non établie**. Elle le deviendra — ou non — quand la
politique aura rejoué **sous ce prévol, sur ce socle, avec ses tampons**.

## LA SUITE, DANS L'ORDRE

1. **Un compteur de coups** dans `banc_live.py` — la condition 3 doit pouvoir se lever.
2. **La sonde du gel** (le serveur est libre maintenant).
3. **La politique**, 2 × 67, canal inchangé, minuteur déjà dérivé (`rejeu.sh`, 640 s).
4. **Alors seulement** : la comparaison, appariée, avec son intervalle.
