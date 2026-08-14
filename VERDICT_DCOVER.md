# `dcover` étalonné — la porte passe, mais pas au centre de la cible

Mesuré le 14/08/2026. Critères déposés avant dans `DEPOT_DCOVER.md` (commit `7fd76e7`).
Sonde sur les points que les hommes **traversent** (rayons de 170 m vers 30 m), pas sur un
disque uniforme — l'échantillonnage uniforme est ce qui m'avait fait prédire 0,167 quand
l'épisode rendait 0,033.

## Les deux contrôles positifs PASSENT

**1. La moyenne locale est non nulle** — 0,400 m/cellule sur le site plat, 2,080 sur le
nouveau. Pas de dégénérescence (seuil nul → tout devient couvert).

**2. La sonde reproduit la panne connue.** Site plat, ancien seuil : **95,3 % de garde-fou**
là où le banc en mesurait 78,3 %. Même ordre, même mécanisme. *Un instrument qui ne
reproduit pas la panne ne prouve pas qu'il l'a réparée* — ce contrôle-là, je ne l'aurais
pas posé il y a douze heures.

## Ce que le seuil local change, chiffré

| site | moyenne locale | seuil NOUVEAU | seuil ANCIEN | rapport |
|---|---|---|---|---|
| plat (1734,5391) | 0,400 | 0,560 | 3,241 | **×5,8** |
| banc (4644,5652) | 2,080 | 2,912 | 3,241 | ×1,1 |

**Le ×5 parasite est confirmé quantitativement.** Et le tableau explique tout : sur un site
à relief doux, le seuil global était six fois trop haut et ne trouvait jamais rien ; sur le
nouveau site il n'était trop haut que de 10 %, ce qui l'a fait passer presque inaperçu.

## La porte

| | médiane `dcover` | garde-fou |
|---|---|---|
| banc, ANCIEN seuil | 0,133 | 16,1 % |
| **banc, NOUVEAU seuil** | **0,100** | **0,0 %** |
| gymnase | 0,035 | — |
| plage gymnase [1 % ; 99 %] | [0,000 ; 0,131] | |

**La porte PASSE** : 0,100 tombe dans [0,000 ; 0,131]. Et le garde-fou disparaît
complètement — plus aucun point ne rend la sentinelle.

## Ce que je ne dis PAS

**0,100 n'est pas 0,035.** La médiane d'Arma reste à trois fois celle du gymnase, tout près
du haut de la plage plutôt qu'en son centre. La porte que j'ai déposée était « dans la
plage », et elle est franchie ; mais **ce n'est pas un appariement propre**, et le dire
autrement serait mentir par omission.

Ce qui est réellement acquis, c'est la disparition du garde-fou : la colonne mesure enfin
quelque chose partout, au lieu de rendre une constante d'échec 16 % du temps.

## Ce qui n'est pas promis

Réparer `dcover` ne dit rien de la prise. **Le 0/20 reste à remesurer**, et il peut très
bien rester 0.
