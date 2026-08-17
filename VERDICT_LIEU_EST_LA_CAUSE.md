# ⭐ VERDICT — LE DESTIN SUIT LE LIEU. LE PLACEUR EST LA CAUSE.

17/08/2026. Socle `1.14.0`, levier `HMT_LIEU_FORCE`, **cinq lieux alternés dans les MÊMES
sessions**, 2 sessions × 15 tirages. Signatures écrites avant, avec grandeur, statistique
et `n` minimum.

## Le résultat

| lieu | n | échecs | taux | détail |
|---|---|---|---|---|
| **vif** `4776,5196` | 6 | 1 | **16 %** | `. . . . T5 .` |
| **vif** `4445,6138` | 6 | 2 | **33 %** | `. . T5 . . T5` |
| **mort** `4210,5369` | 6 | 6 | **100 %** | `T5 T5 T5 T5 T5 T5` |
| **mort** `4716,5207` | 6 | 6 | **100 %** | `T5 T5 T5 T5 T5 T5` |
| **mort** `4989,5877` | 6 | 6 | **100 %** | `T5 T5 T5 T5 T5 T5` |

**18 échecs sur 18** aux lieux morts. **3 sur 12** aux lieux vivants.
Pire lieu vivant **33 %** contre meilleur lieu mort **100 %** : la séparation exigée par la
signature (a) est franchie sans recouvrement.

> ## ➤ LE DESTIN SUIT LE LIEU. LE PLACEUR EST FAUTIF.

## Pourquoi ce protocole est décisif

Les cinq lieux **alternaient dans la même session**. Un lieu mort échoue donc **dans la
session même où un lieu vivant vient de réussir**. L'effet de session — le phénomène qui a
occupé toute la journée — **cesse d'être une explication concurrente** : il n'était que la
conséquence d'un lieu fixé une fois par session.

## Le mécanisme complet, du code au chiffre

1. `socle.sqf:166-177` — le placeur balaye **24 points FIXES** autour du premier attaquant :
   angles `k·15°`, rayons 250/290/330/370 m. **Aucun aléa.**
2. Cet homme naît **une fois**, à la création de la scène → **le lieu est fixé pour toute la
   session**.
3. Le placeur retient le point de **pente moyenne minimale**, et s'arrête dès qu'elle passe
   sous 0,10.
4. **La pente ne prédit pas la praticabilité** : la session 8 était à 0,01 — parfaitement
   plate — et mourait 5 fois sur 6. Ce qui bloque un homme, c'est l'**encombrement**, invisible
   pour une pente moyennée sur un carré de 60 m.

**D'où :** ~2 lieux sur 3 parmi les candidats sont impraticables → **68 % de sessions mortes**,
stable à travers tous les protocoles, tous les socles et les deux ères de pont.

## Ce que ce verdict explique, d'un coup

- l'**unité** est la session — parce que le lieu l'est ;
- le caractère **quasi binaire** — un lieu est praticable ou non ;
- le **temps ne guérit pas** — le lieu ne change pas ;
- l'absence de lien avec la **charge**, l'**heure**, l'**ordre**, le **co-locataire**, le **pont** ;
- **quel canal meurt** : un lieu encombré tue T5, un lieu sans ligne de vue tue T4/T7
  (session 1 : 4 échecs T7, zéro T5).

## Ce qu'il RETIRE de ma journée

**Sept hypothèses causales** ont été énoncées et réfutées avant celle-ci. Aucune ne pouvait
aboutir : je cherchais une cause **temporelle ou logicielle** à un phénomène **géométrique**.
La sonde du pont, celle de l'unité, celle du geste, celle de l'échauffement — toutes ont
mesuré les conséquences d'un lieu qu'aucune ne regardait.

**Et c'est la LECTURE DU CODE qui a tranché**, sur suggestion de Younes, en vingt minutes et
zéro serveur, après une nuit de sondes. À inscrire au registre : contre un phénomène
reproductible, **lire le mécanisme avant de sonder ses effets**.

## LE CORRECTIF, maintenant justifié — et pas encore appliqué

Le placeur doit juger un lieu sur **ce que le témoin doit y faire**, non sur une pente
⟨règle 6 : vérifier la propriété que le mécanisme EMPLOIE⟩ :

1. **test de traversabilité** — l'homme parcourt-il réellement ses 24 m depuis ce point ?
2. **test de ligne de vue** — voit-il à 40 m dans la direction du mannequin ?
3. **contrôle positif** pour chacun ⟨règle 16⟩, et le lieu n'est retenu que s'il passe les deux.

Le levier `HMT_LIEU_FORCE` reste en place : il permet de **rejouer** un lieu, et les cinq
lieux mesurés ici deviennent le **jeu d'épreuve** du placeur corrigé — les trois morts doivent
être rejetés, les deux vivants acceptés.
