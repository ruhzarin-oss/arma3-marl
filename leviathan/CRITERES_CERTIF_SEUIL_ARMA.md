# CRITÈRES FIGÉS — CERTIFICATION ARMA DU SEUIL DE MANŒUVRE (avant les données)

Figés le 2026-07-28, AVANT tout run. Non négociables après coup.

## CE QUE LE SANDBOX PRÉDIT
Balayage `balayage_menace.json` (critères `cfe67bb4d459d5dd`), monde mesuré,
A=4, 200 épisodes/point, graine 7 :

| D | prise flanc/frontal |
|---|---|
| 4 | ×1,00 |
| 8 | ×1,61 |
| 12 | ×2,57 |

**Prédiction pré-enregistrée** : sur Arma, à A=4 attaquants,
- D=4  → le flanc N'ACHÈTE PAS la prise (rapport < 1,50)
- D=8  → le flanc ACHÈTE la prise (rapport ≥ 1,50)
- D=12 → le flanc achète la prise, davantage encore

## DISPOSITIF
Théâtre **Altis / Pyrgos** (port 5826). Choisi parce que son couvert est ASYMÉTRIQUE
(frontal découvert 13, flancs couverts 46, mesure du 25/07) — Stratis a un couvert
uniforme où le flanc ne peut pas se distinguer (finding du 23/07).
`envelop_arma.py` modes `frontal` et `envelop`, `--nag 4`, garnison reposée à
l'identique par `poser_fob.py <D>` AVANT CHAQUE épisode.
4 répétitions par cellule, 6 cellules (3 D × 2 modes) = 24 opérations.

## BANDE DISCRIMINANTE — la garde contre le banc qui ne sépare rien
Un D n'est interprété que si la prise frontale y tombe entre **25 % et 75 %**.
Hors bande (massacre à 0 % ou promenade à 100 %), les ratios ne veulent rien dire
et ne sont PAS lus. C'est la leçon de JALON 2 (14/06) : 4 opérations sur 6 avaient
abandonné en ENLISEMENT et leurs chiffres étaient des combats figés à mi-course.

## CE QUI COMPTE COMME ABANDON
Toute opération qui n'atteint pas une issue (FOB pris ou assaillants détruits) dans
les `--steps` impartis est comptée ABANDON et exclue des moyennes. **Si plus de 25 %
des opérations d'une cellule abandonnent, la cellule entière est déclarée NON MESURÉE.**

## LES QUATRE ISSUES, décidées d'avance
1. **Prédiction confirmée** (flanc <1,50 à D=4 et ≥1,50 à D=8) → le seuil transfère.
   L'énoncé « la manœuvre paie au-dessus de 2 défenseurs par attaquant » est certifié.
2. **Seuil décalé** (le flanc bascule à un autre D) → le sandbox a la bonne FORME mais
   la mauvaise échelle. On consigne le D d'Arma comme le vrai, sans retoucher le sandbox
   pour le faire coller.
3. **Aucune bascule** (le flanc paie partout, ou nulle part) → le seuil est un artefact
   du sandbox. C'est un résultat, pas un échec.
4. **Trop d'abandons** → on n'a rien mesuré. On répare le régime avant toute lecture.

## INTERDICTIONS
Pas de retouche des seuils, du nombre de répétitions, de la plage de D, du théâtre ou
des paramètres de doctrine (`--offset 45 --standoff 70 --flank 0.45 --assault_tick 24`,
repris tels quels du banc FIBUA certifié du 23/07) après avoir vu un chiffre.
