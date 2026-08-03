# CRITÈRES FIGÉS V2 — CERTIFICATION ARMA DU SEUIL DE MANŒUVRE (avant les données)

Figés le 2026-07-28 après la sonde de régime, AVANT tout run de certification.
Remplace `CRITERES_CERTIF_SEUIL_ARMA.md` (b764211cf2e274ca), dont le dispositif
(A=4) s'est révélé HORS BANDE sur Arma. Le seuil de lecture, lui, n'est pas touché.

## POURQUOI UNE V2
Sonde du 2026-07-28 (garnison 8 fixe, mode frontal, 2 reps) :

| attaquants | prise frontale | bande 25-75 % |
|---|---|---|
| 4 | 0 % | non |
| 8 | 0 % | non |
| 12 | 50 % | OUI |
| 18 | 50 % | OUI |

À A=4 contre D=8, Arma ne résout rien : 0 % de prise deux fois sur deux. Le sandbox
donnait 54 % au même rapport. **L'échelle absolue du sandbox ne transfère pas.**
On ne peut donc pas certifier le seuil à A=4. On balaie le MÊME AXE (rapport D/A)
à l'intérieur du régime qui se résout.

## DISPOSITIF V2
Théâtre Altis / Pyrgos (vérifié en dur le 28/07 : cinq points à terre, relief 12 m,
asymétrie de couvert flanc/frontal ×1,33 — au-dessus du seuil de 1,30, de peu).
Attaquants **A = 12 fixe** (le plus petit effectif qui entre dans la bande).
Garnison **D ∈ {8, 12, 16, 24}**, soit un rapport D/A de **0,67 · 1,00 · 1,33 · 2,00**.
Modes `frontal` et `envelop`, `--offset 45 --standoff 70 --flank 0.45 --assault_tick 24`
(paramètres du banc FIBUA certifié du 23/07, repris tels quels).
Garnison reposée à l'identique avant CHAQUE épisode. **3 répétitions par cellule**,
8 cellules = 24 opérations.

## PRÉDICTION PRÉ-ENREGISTRÉE
Le sandbox place le seuil à D/A = 2 (rapport de prise flanc/frontal ×1,61 à ce point,
×1,00 à D/A = 1). Donc, sur Arma :
- D/A = 0,67 et 1,00 → le flanc N'ACHÈTE PAS la prise (rapport < 1,50)
- D/A = 2,00 → le flanc ACHÈTE la prise (rapport ≥ 1,50)

## GARDES, inchangées
- **Bande** : une cellule n'est lue que si sa prise frontale tombe entre 25 % et 75 %.
- **Abandon** : opération sans issue dans les `--steps` impartis = exclue ; au-delà de
  25 % d'abandons dans une cellule, la cellule est NON MESURÉE.
- **Coût** : le rapport pertes/prise flanc/frontal est relevé partout ; toute inversion
  est signalée, jamais lissée.

## LES QUATRE ISSUES, décidées d'avance
1. Bascule à D/A = 2 → **le seuil transfère en RAPPORT malgré l'échelle absolue fausse.**
   C'est le résultat fort : le sandbox se trompe sur les effectifs mais dit vrai sur le rapport.
2. Bascule à un autre D/A → le sandbox a la bonne forme, la mauvaise position. On consigne
   le rapport d'Arma comme le vrai, sans retoucher le sandbox pour le faire coller.
3. Aucune bascule dans la plage → le seuil est un artefact du sandbox. Résultat, pas échec.
4. Trop d'abandons ou tout hors bande → rien n'est mesuré. Réparer le régime avant lecture.

## INTERDICTIONS
Aucune retouche des seuils, des répétitions, de la plage de D, du théâtre ou des
paramètres de doctrine après avoir vu un chiffre.
