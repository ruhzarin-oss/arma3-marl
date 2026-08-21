# ⛔ LA PORTE DU 20/08 EST RETIRÉE — elle tournait sur un placeur cassé

**21/08/2026.** Retrait de `VERDICT_PORTE_20-08.md`, qui déclarait *« les quatre lignes
vertes ensemble, 59/60, le banc sort de panne diagnostique »*.

## LE MOTIF

`socle.sqf` — ligne de retour de `HMT_G_PRATICABLE` — lisait `round _m`.
**`_m` était défini par l'ACTE 2, que j'ai supprimé le 20/08** en retirant le sélecteur.
Je ne l'ai pas relu. Le placeur **plantait sur son retour**, donc rendait `nil`, donc son
appelant lisait `nil`.

> **102 erreurs `Undefined variable: _m` sur les cinq lots de cette porte.**

**Quatrième variable orpheline de la semaine** après le `reveal`, le sabotage du tir et la
télémétrie du geste. Même geste à chaque fois : *je supprime un bloc et je ne relis pas ce
qui en dépendait.*

## POURQUOI AUCUNE LIGNE NE L'A VU

**Aucune ligne du juge ne regardait les erreurs de script.** Je l'avais proposée le 19/08
et **jamais câblée**. C'est la ligne 5, posée depuis — et son témoin est que **le juge
amendé condamne la porte qu'il avait bénie** : verdict `['1','5']`.

⚠️ *Un instrument qui ne regarde pas les pannes de son propre monde bénira n'importe quoi.*

## CE QUI EST RETIRÉ, ET CE QUI NE L'EST PAS

**Retiré** : le verdict « quatre lignes vertes », et la phrase « le banc sort de panne
diagnostique ». La porte n'a **rien certifié**.

**Non retiré** : les mesures brutes de cette nuit-là (60 tirages, T5=0, T7=0, muet=0)
restent des observations. Elles ne sont pas **fausses** — elles sont **non certifiées**,
ce qui n'est pas la même chose. Archives et empreintes dans
`/mnt/data/preuves/2026-08-20_porte_valide` (nom conservé tel quel : renommer une archive
après coup effacerait la trace de ce qu'on a cru).

## LA PORTE REJOUÉE — 21/08, socle 5.5.0, commit `b120cdf`

| ligne | | |
|---|---|---|
| 1 · les actes du prévol répondent-ils ? | **1 canal mort / 60** | **⛔ ROUGE** |
| 2 · muets décomposés | 0 planté · 0 pont · 0 lent · 0 écarté | ✓ |
| 2bis · rebut d'instrument | 0 sur 60 | ✓ |
| 3 · regroupement par serveur | X² = 4,07 (seuil 11,07) | ✓ |
| 4 · les cinq sabotages | tous PASSE, **socle 5.5.0 des deux côtés** | ✓ |
| **5 · erreurs de script** | **0** — contre 102 la veille | ✓ |

**Le T5 rouge est une vraie mesure, pas un défaut :**
`x 4344 · y 5396 · max_joues 11,9 · med_joues 0 · min_joues 0 · plancher 15,2 · azimuts 8`
Huit azimuts joués, **médiane zéro** : l'homme n'a bougé dans aucune direction sauf une, et
11,9 m, sous le plancher. **Ce lieu bloque réellement.**

## LA QUESTION QUI RESTE, ET ELLE EST SOUMISE

**Un lieu vraiment bloqué doit-il condamner la session ?** Le critère certifie une SESSION
mais se joue sur **un** lieu tiré par le placeur — il hérite donc du lieu. Trois lectures
possibles, aucune choisie ici : (1) c'est juste ; (2) c'est du rebut d'instrument — mais
déplacer un échec vers le seau qui le tolère est ce que la carte des juridictions devait
empêcher ; (3) le critère se joue sur 2-3 lieux et prend le max.

⚠️ **La 3 est celle qui rend la porte verte.** C'est une raison de s'en méfier, pas de
l'écarter. Décision en attente de revue.
