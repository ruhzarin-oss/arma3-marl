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

> ⛔ **CE DEPOT EST REFUTE.** Banc des jambes II du 17/08 (plan 2x2 lieu x comportement) :
> sur un lieu certifie praticable, le corps rend **20,5 m sur 19,7**, soit **104 %**.
> Le 62 % mesurait le TERRAIN, pas le corps. Voir `VERDICT_CORPS_NON_LIMITE.md`.

# CHARGE DE FIDÉLITÉ — le corps rend 62 % des jambes que le gymnase suppose

16/08/2026. Sorti de `RETRACTATION_JAMBES.md` sur l'audit de Fable : *un document de
rétractation rétracte ; les verdicts neufs prennent leur propre banc.*

## La mesure

| | mètres par ordre de 3,28 s |
|---|---|
| ce que le gymnase suppose (6 m/s × 3,28 s) | **19,7 m** |
| ce qu'Arma rend, primitive en service | **12,2 m** — 7 essais sur 7, 100 % au sol, 11,6–12,5 |
| **rapport** | **62 %** |

Banc des jambes v3, commit `11fa45c`. Banc de **laboratoire** : un homme seul, hors du feu.

## Pourquoi c'est une charge et pas un détail

Elle rejoint la famille des écarts de fidélité déjà mesurés — le couvert qui protège
**11× trop**, la létalité **4× trop forte**. Ce sont les écarts qui décident si un résultat
du gymnase veut dire quelque chose dehors.

## Le sursis qu'elle pose, et il est NEUF

**Sur le transfert gymnase → live.** Parmi les douze colonnes que la porte tient « dans la
plage du gymnase », **lesquelles encodent le déplacement** ? Si le gymnase suppose des
jambes 60 % plus rapides que le monde n'en donne, la plage est peut-être inatteignable, ou
atteinte à la marge — auquel cas la porte tiendrait sur une coïncidence.

**Non mesuré. Non tranché. Ouvert.** À traiter avant de citer un transfert, pas avant de
mesurer NATIF — le natif ne passe pas par le canal de la consigne.

## Ce que ça ne dit pas

Que la primitive doive changer : aucune ne fait nettement mieux au sol (meilleur 13,3 m ;
celui qui monte à 15,8 m est écarté à 58 % au sol, c'est du vol). Voir le § CHOIX de
`RETRACTATION_JAMBES.md`.
