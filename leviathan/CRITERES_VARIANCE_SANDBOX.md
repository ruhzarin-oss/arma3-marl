# CRITÈRES FIGÉS — LA VARIANCE DU SANDBOX (avant les données)

Figés le 2026-07-28, AVANT tout run. Miroir exact de `CRITERES_VARIANCE_BANC.md`.

## POURQUOI
On mesure ce soir de combien le banc Arma bouge tout seul. La même question se pose au
sandbox, et personne ne l'a jamais posée : **tous les verdicts du jour reposent sur la graine 7**.
Le re-verdict du flanc, le balayage de la menace, la matrice du manuel, le seuil D=8 — une
seule graine à chaque fois.

Si le sandbox bouge de 20 points d'une graine à l'autre, le seuil de manœuvre « D=8 » n'est pas
un seuil, c'est un tirage.

## DISPOSITIF
Monde MESURÉ figé (courbe n°1, n°2, `cible_unique=True`), A=4, D=8, 200 épisodes,
manœuvre `debordement_simple`, doctrines scriptées. **12 graines : 1 à 12.**
Rien d'autre ne varie.

## CE QUI EST MESURÉ
Prise par graine. Étendue (meilleure − pire) et écart-type.

## SEUILS PRÉ-ENREGISTRÉS
- **Étendue ≤ 5 points** → le sandbox est stable ; une graine suffit, les verdicts du jour
  tiennent tels quels.
- **Étendue 5-15 points** → il faut rapporter une moyenne sur au moins 5 graines. Les verdicts
  du jour restent valides en DIRECTION mais leurs chiffres sont à re-publier en moyenne.
- **Étendue > 15 points** → **le seuil D=8 n'est pas un seuil, c'est un tirage.** Tous les
  verdicts sandbox du 28/07 sont à refaire en multi-graines avant d'être cités.

## INTERDICTIONS
Pas de retouche des seuils ni du nombre de graines après un chiffre.
