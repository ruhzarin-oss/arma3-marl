# POURQUOI LA PORTE NE PASSE PLUS — **l'entraînement était coupé, la récompense est innocente**

**23/08/2026, 19 h 20.** Règle de décision déposée **avant** ouverture (`a08b7fb`).
Deux bras, prédictions écrites d'avance, un seul changement chacun.

## Le résultat

| bras | itérations | γ_Φ | prise apprise | contre frontale (12,8 %) | contre flanc (34,3 %) |
|---|---|---|---|---|---|
| référence | 140 | 0,99 | **5,7 %** | −7,1 (borne −9,2) | −28,6 |
| **R** | 140 | **1,0** | **5,3 %** | −7,5 (borne −9,8) | −29,0 |
| **B** | **420** | 0,99 | **24,8 %** | **+12,0 (borne +8,7) ✓** | −9,5 |

## R1 est FAUSSE — et la prédiction de Fable avec elle

> **À budget égal, γ = 1,0 rend 5,3 % contre 5,7 % pour γ = 0,99. Aucune différence.**
> **La correction du 17/08 n'est pas la cause.** La rente de survie existe dans
> l'arithmétique ; elle ne pèse rien sur le résultat.

Fable prédisait « R franchit ». **R n'a pas franchi** : 5,3 % contre le seuil de 12,8 %, et
la courbe s'arrête à 83,5 m. Sa prédiction était écrite avant, elle est réfutée, on l'écrit.

## B1 est la bonne piste, et elle n'est pas encore acquise

**420 itérations rendent 24,8 %** et **battent la frontale de 12,0 points, borne inférieure
+8,7** — le premier G1 positif de la journée. Mais **la porte exige de battre les DEUX**, et
le flanc reste devant de 9,5 points.

**Et la courbe montait encore au dernier point** : 0,8 % à l'itération 200, 6,2 % à 360,
10,5 % à 380, **16,4 % à 419**. Elle n'a pas fini de monter.

## Ce que ça dit

> **Le monde a durci — chirurgie du couvert le 16/08, létalité recalibrée — et le budget
> d'entraînement est resté celui d'avant.** 140 itérations dans ce monde, c'est couper une
> courbe qui ne décolle qu'à 380. **L'apprentissage n'est pas cassé : il est affamé.**

⭐ **Cliquet : quand on durcit le monde, le budget d'entraînement ne se garde pas — il se
redérive.** Le nôtre datait d'un monde qui n'existe plus, et personne ne l'avait rouvert.

⭐ **Et un cliquet payé deux fois aujourd'hui : ne pas juger une courbe en plein milieu.**
J'ai écrit « le budget ne répare pas » à l'itération 200, sur une courbe plate qui a décollé
160 itérations plus loin.

## ⚠️ Ce que ça ne dit pas

- **n = 1 par bras.** Fable a été explicite : deux graines par bras avant tout verdict.
  L'écart R−référence (0,4 point) est un **nul**, et un nul à n=1 sur un si petit écart
  suffit à écarter un GROS effet de γ, pas un petit.
- **Les trois défauts trouvés dans le code restent entiers** (`QUATRE_VERIFICATIONS_CODE.md`) :
  le guidage divisé par les morts, l'absence de bootstrap à la troncature, la normalisation
  de l'avantage **pas par pas**. Aucun n'est mesuré. **Ils peuvent expliquer POURQUOI il
  faut 380 itérations** — c'est-à-dire le retard lui-même.
- **Rien ne dit encore que la porte passera.** Elle exige de battre le flanc, et il reste
  9,5 points à combler.

## La suite, telle qu'elle se dérive

Un seul geste : **prolonger**. 1 200 itérations, récompense et monde inchangés, deux graines.
Si la porte passe, l'affaire est close et le budget se redéclare. Si elle plafonne sous le
flanc, alors les trois défauts du code deviennent la piste, **un bras à la fois**.
