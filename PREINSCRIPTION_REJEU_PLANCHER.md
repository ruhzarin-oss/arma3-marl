# REJEU DU PLANCHER SUR TIRAGE FRAIS — pré-inscription écrite AVANT la mesure

**20/08/2026, 00 h 30.** Le critère `CRITERE_CANAL_VIVANT.md` (`d2f97ae`) a été dérivé sur
des **données déjà vues**. Ce rejeu le confronte à un **tirage neuf**.

## LE SEUIL EST FIXÉ — IL NE SERA PAS REDÉRIVÉ

> **plancher = 15,2 m sur le MAXIMUM des 8 azimuts.**

C'est ce qui distingue un **rejeu** d'un nouvel ajustement. Le nombre entre dans la mesure
comme une **constante**, et il en ressort validé ou mort. Aucune re-dérivation, aucun
ajustement du plancher aux résultats : ce serait la faute que la soirée a passé cinq
tentatives à ne pas commettre.

| | |
|---|---|
| question | le canal de locomotion est-il vivant dans cette session ? |
| grandeur | distance parcourue en 4 s, canal `sv_vz_preserve_10hz`, socle 4.0.0 |
| échantillon | les 8 azimuts de la couture |
| statistique | le **MAXIMUM** sur les 8 |
| **seuil** | **15,2 m — FIXÉ** |
| tirage | **graine 23** (la dérivation utilisait 19), ±250 m autour de 4644/5652, **aucun filtre** |
| n | 60 sains + 60 sabotés + 60 répétés |

## LES PRÉDICTIONS

| n° | prédiction |
|---|---|
| **P1** | **zéro faux-rouge** : les 60 lieux sains ont tous max ≥ 15,2 m |
| **P2** | **zéro faux-vert** : les 60 lieux sabotés (jambes, vy=0) ont tous max < 15,2 m |
| **P3** | le **creux se retrouve** : max des sabotés < min des sains |
| **P4** | **verdict stable** : 0 désaccord entre deux passages des mêmes 60 lieux sains |

## LE FALSIFICATEUR

> **Un seul faux-rouge ou un seul faux-vert tue le plancher tel qu'énoncé.**
> Il ne sera pas déplacé pour survivre : il sera **retiré**, et la dérivation reprise
> avec un n plus grand — ou la statistique remise en question.

## CE QUE ÇA BORNE ⟨règle 19⟩

Avec 60 par bras et zéro erreur, la règle de trois borne chaque taux d'erreur à **≤ 5 %**
en confiance à 95 %. C'est la résolution que ce rejeu achète, et pas davantage.

## L'ANGLE MORT DÉCLARÉ ⟨règle 20⟩

- Même monde, même région (±250 m autour de 4644/5652) : ce rejeu teste **le tirage**, pas
  la généralisation à une autre carte ni à une autre zone.
- Serveur **au repos** — pas de scène. La cadence d'impulsions y est la même qu'en monde
  éveillé (nt 39-40 des deux côtés), mais rien n'est dit d'une charge plus lourde.
- « max ≥ plancher » prouve que **les impulsions arrivent**, **pas** que l'homme marche au
  sol : un azimut parcouru en vol compte comme preuve de vie du canal.
