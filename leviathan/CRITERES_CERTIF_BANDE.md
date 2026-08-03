# CRITÈRES FIGÉS — CERTIFICATION DANS LA BANDE (avant les données)

Figés le 2026-07-28, AVANT tout run.

## POURQUOI ICI ET PAS AILLEURS
La sonde de régime du 28/07 15h37 (`sonde_regime_arma`, jamais lue jusqu'à 18h30) a établi la
bande discriminante contre une garnison de 8 :

| attaquants | prise frontale | dans la bande 25-75 % |
|---|---|---|
| 4 | 0 % | non |
| 8 | 0 % | non |
| **12** | **50 %** | **OUI** |
| 18 | 50 % | OUI |

Trois runs ont été dépensés sur 12 contre 12 — hors bande, 0 % — alors que cette table
existait déjà. Elle est désormais la référence : **aucune certification hors bande.**

## CE QUI EST MESURÉ
A=12 vs D=8 (rapport D/A = 0,67), frontal contre envelop, 6 répétitions par bras, 120 pas,
Altis/Pyrgos. **Ordre d'assaut final DÉSACTIVÉ** : la bande a été mesurée sans lui, on ne
change pas deux choses à la fois. Son effet est une question distincte, pour plus tard.

## LA PRÉDICTION DU SANDBOX, À RÉFUTER
`balayage_menace.json` place le seuil de manœuvre à D/A = 2. À D/A = 0,67 — ici — le sandbox
prédit donc que **le flanc n'achète PAS la prise** : rapport envelop/frontal < 1,50.
Il prédit en revanche qu'il achète des VIES : coût envelop/frontal ≤ 0,60.

## SEUILS PRÉ-ENREGISTRÉS
1. **Bande** : la prise frontale doit retomber entre 25 % et 75 %. Sinon la cellule est NON
   MESURÉE et rien ne se lit (la sonde n'avait que 2 opérations par point).
2. **Abandons** : plus de 25 % d'opérations non résolues dans un bras → bras NON MESURÉ.
3. **Prise** : rapport envelop/frontal. ≥1,50 → la prédiction du sandbox est RÉFUTÉE, le flanc
   achète la prise à un rapport de forces où le sandbox dit que non. <1,50 → prédiction tenue.
4. **Coût** : rapport pertes-par-prise envelop/frontal. ≤0,60 → prédiction tenue.

Les quatre issues se consignent telles quelles. Une prédiction démentie est un résultat.

## INTERDICTIONS
Pas de retouche des effectifs, du théâtre, des paramètres de doctrine ni des seuils après un
chiffre. Pas d'activation de l'ordre d'assaut final dans ce run.
