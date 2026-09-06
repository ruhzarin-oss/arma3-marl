# DEPOT N1 — LE NIVEAU EST MESURABLE ET REPRODUCTIBLE. LA COURBE DU 26/07 EST FAUSSE DE FORME.

Criteres : `CRITERES_N1_NIVEAU.md` puis `CRITERES_N1B_REPLICATION.md` (ecrit avant la relance).
Bancs : `n1_niveau.py`. Donnees : `courbe_toucher_hitpart_B1/B2/CUMUL.json`.
Trois passes, **~42 000 balles**, aucune mort du pont.

## 1. L INSTRUMENT — ce qui a ete reparé pendant la nuit
- **Passe A** (un impact par APPEL de l ecouteur) : 2 164 impacts pour 1 759 balles a 25 m
  couche, **taux 1,23 — impossible**. Le moteur appelle `HitPart` PLUSIEURS FOIS pour un
  MEME projectile. Passe classee ⛔.
- **Instrument B** : deduplication par **IDENTITE DU PROJECTILE** (`_e select 2`). Plus aucun
  taux > 1 sur 36 conditions.
  ⭐ Troisieme occurrence du meme mode d echec dans ce projet, un cran plus fin chaque fois :
  `HandleDamage` 1,9 appel/balle (26/07) -> parties du corps (03/09) -> appels repetes par
  projectile (04/09).

## 2. LA FAUTE DE METHODE, NOMMEE
La bande [0,45 ; 0,66] du bloc 0 etait calibree sur l instrument **A**. Je l ai comparee a
l instrument **B**. Elle ne mesurait donc rien. **Le critere n a PAS ete reecrit** : il a ete
declare inapplicable, N1 classee ⛔ instrument, et un banc neuf (N1b) ouvert avec son critere
propre, ecrit avant la relance.
⭐ **Cliquet : quand on repare un capteur en cours de mesure, sa reference de controle meurt
avec l ancien capteur. Elle se REMESURE, elle ne se transpose pas.**

## 3. LE VERDICT DE N1b — REPRODUCTIBILITE : ✔
| passe | 100 m debout | IC95 | n |
|---|---|---|---|
| B1 | 0,402 | [0,371 ; 0,435] | 902 |
| B2 | 0,383 | [0,335 ; 0,434] | 368 |

**Intervalles RECOUVRANTS -> l instrument B est REPRODUCTIBLE.**
⚠️ Reserve portee par le critere lui-meme : n = 368 en B2 contre **600 exiges**. La
replication est **consistante mais sous-dimensionnee** ; elle n est pas annulee, elle est
moins precise que promis.

## 4. LA COURBE MESUREE (cumul B1+B2, 15 conditions rendues sur 18)

| dist | debout | accroupi | couche | 26/07 debout | rapport |
|---|---|---|---|---|---|
| 25 m | 0,562 | 0,556 | 0,670 | 0,75 | **x0,75** |
| 50 m | 0,631 | 0,600 | 0,565 | 0,57 | x1,11 |
| 75 m | 0,485 | 0,535 | 0,428 | 0,41 | x1,18 |
| 100 m | 0,397 | 0,466 | 0,269 | 0,30 | x1,32 |
| 150 m | 0,458 | 0,446 | 0,319 | 0,24 | **x1,91** |
| 200 m | non rendu (n=239) | non rendu | non rendu | | |

> ⭐ **L ERREUR N EST PAS UN FACTEUR, C EST UNE FORME.** Le rapport croit avec la distance —
> 0,75 · 1,11 · 1,18 · 1,32 · 1,91. **La courbe du 26/07 est TROP RAIDE** : elle sur-estime
> le proche et sous-estime le lointain. Un facteur median de x1,18 la resumerait mal.
> C est exactement ce que Fable annoncait en refusant l argument « la pente est invariante ».

**Consequence directe** : le monde du gymnase punit trop le rapprochement et paie trop la
distance. C est le parametre qui a refuse de transferer trois fois.

## 5. CE QUI CORROBORE LE 26/07, ET C EST A PORTER AU CREDIT DE L ANCIENNE MESURE
Profil de posture normalise au debout : a 100 m, **couche = 0,68** — soit un risque divise par
**1,47**. Le 26/07 avait mesure **1,4**. Les deux instruments s accordent sur la posture, ils
ne divergent que sur la distance. Et le couche ne protege **pas du tout** a 25 m (1,19).

## 6. CE QUI RESTE OUVERT
- **200 m n a jamais atteint n = 300** dans aucune posture : trois conditions non rendues.
  Il faut soit plus de blocs, soit des duels dedies au long.
- `degat_par_impact` **n a pas ete re-derive** : le bras vulnerable n a pas ete joue, la nuit
  est passee a reparer le capteur. **0,233 reste en service, non verifie.**
- N1b reste sous-dimensionnee a 100 m (n = 368 contre 600).

## 7. CE QUI NE SE CONCLUT PAS
Aucun chiffre de prise, aucun verdict de transfert. On a mesure un instrument et une courbe.
