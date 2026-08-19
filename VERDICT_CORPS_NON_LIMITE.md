> ## ⚠️ EN SURSIS — 19/08/2026, 20 h
> **→ Le dossier est tranché ailleurs : [`VERDICT_LA_PENTE_DANS_LE_SENS_DE_LA_MARCHE.md`](VERDICT_LA_PENTE_DANS_LE_SENS_DE_LA_MARCHE.md).** Ce document-ci reste MORT : il n'est ni réfuté ni restauré, il est **expliqué**. Son chiffre mesurait un régime de pente sans le savoir.
>
>
> **Le corps n'est pas jugé par ce document.** Sa mesure passait par des **lieux reçus**
> d'un placeur dont le critère à 23 m est franchi par **0 acte sur 150 finissant au sol**
> et par **101 sur 111 finissant en l'air** (n = 261, cinq lots de la porte 3.1.0 du 19/08,
> journaux archivés avec empreintes dans `/mnt/data/preuves/2026-08-19_porte_31_tronquee`).
> La population de lieux sur laquelle ce document a mesuré est donc **sélectionnée sur le vol**,
> et **le régime du corps pendant la mesure n'est témoigné nulle part** : la télémétrie du geste
> (`HMT|SOCLE|GESTE`) écrivait `any` sur tous ses champs d'animation et de vitesse depuis le
> **17/08 23:02** (socle 2.8.0), et ses champs `sol`/`posture` interrogeaient un homme qui
> n'avait jamais marché.
>
> **Le vol est entretenu par notre propre code** : `setVelocity [vx, vy, 0]` remet la
> composante verticale à zéro dix fois par seconde, donc un homme lancé par le terrain
> ne peut plus redescendre tant que les impulsions durent. Le canal de la couture
> (`arma_couture.py:185`), celui que la politique emploie en production, fait de même.
>
> **Ce document ne se lit plus comme un verdict jusqu'à la mesure dédiée**, qui doit porter
> un témoin de régime **par tick** (fraction au sol, hauteur au-dessus du terrain).
> Voir `SURSIS_19-08_LE_VOL.md`.
>
> ⚠️ Le retrait de ce document **ne restaure pas** ce qu'il avait réfuté : une rétractation
> à rétracter rouvre la question, elle ne rétablit pas l'original. Les deux chiffres sont
> aujourd'hui **non soutenus**.

# ⭐ VERDICT — LE CORPS N'EST PAS LIMITÉ. LE « 62 % » ÉTAIT UNE MESURE DE TERRAIN.

17/08/2026. Banc des jambes II, socle `2.7.0` (`c37cb5f`), plan 2×2 lieu × comportement,
8 essais par condition, critères écrits avant avec grandeur, statistique et `n` minimum.

## Le résultat

| lieu | comportement | n | médiane | min–max |
|---|---|---|---|---|
| hasard | AWARE | 8 | 12,6 m | **2,2 – 20,6** |
| hasard | COMBAT | 8 | 13,4 m | **2,2 – 19,9** |
| **reçu** | AWARE | 8 | **20,5 m** | 18,4 – 20,9 |
| **reçu** | COMBAT | 8 | **20,5 m** | 17,7 – 21,0 |

- **effet du LIEU** : **+7,9 m** en AWARE, **+7,1 m** en COMBAT — présent dans les **deux**
- **effet du MODE** : **+0,0 m** sur lieu reçu, **−0,8 m** sur lieu hasard — **nul**

Seuil pré-écrit : 3 m. Le lieu le franchit deux fois et demie ; le mode ne l'approche pas.

> ## ➤ LE LIEU EXPLIQUE. LE COMPORTEMENT N'EXPLIQUE RIEN.
> ## Sur un lieu praticable, le corps rend **20,5 m sur les 19,7 m** que le gymnase suppose — **104 %**.

## Ce que ça RETIRE du registre

**`CHARGE_FIDELITE_JAMBES.md` — « le corps rend 62 % des jambes du gymnase » — est RÉFUTÉ.**

Ce n'était pas une propriété du corps : c'était une propriété du **terrain sur lequel on le
mesurait**. Le banc des jambes tirait ses positions au hasard dans ±60 m et ne filtrait que
l'eau ; **la moitié de ses lieux bloquaient un homme**, et la moyenne des deux populations a
été lue comme une capacité.

Le sursis « n = 1 lieu » posé par Fable ne se lève pas : **il se confirme et se dépasse**.
Ce n'était pas un problème de taille d'échantillon, c'était bien une **grandeur composite** —
et le facteur composite pesait 38 points.

## Ce que ça dit de la VARIANCE, et c'est aussi net

| | dispersion |
|---|---|
| lieux reçus | **17,7 – 21,0 m** (étendue 3,3) |
| lieux au hasard | **2,2 – 20,6 m** (étendue 18,4) |

**Le lieu n'explique pas seulement la moyenne, il explique la variance.** Sur un lieu certifié,
la mesure est reproductible à ±1,5 m. Sans certification, elle couvre presque tout le domaine
possible — et toute mesure faite dessus héritait de ce bruit.

## Ce que ça n'établit PAS

- Rien sur le **tir**. Ce banc mesure le déplacement ; la divergence certificateur/servi sur
  `reveal` et sur le comportement reste entière côté feu, et B2 reste à faire.
- Rien sur le **44,8 %** de prise, qui garde ses conditions de réhabilitation.
- Le mode est écarté **pour le déplacement seulement** — AWARE et COMBAT donnent le même
  résultat aux jambes, ce qui ne dit rien de ce qu'ils font au feu.

## Conséquence pour le gymnase

Le corps d'Arma **atteint** la vitesse que le gymnase suppose, et la dépasse de 4 %. La
famille des écarts de fidélité — le couvert ×11, la létalité ×4 — **perd un membre** : celui-ci
n'a jamais existé, il était une erreur de mesure.
