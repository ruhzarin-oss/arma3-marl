# Critères pré-enregistrés — confirmation du réglage 900 m, fenêtre entière

*19/09/2026, écrits avant le premier épisode. La grille du matin (`GRILLE-PERCEPTION-19-09`, 67 épisodes lus) a retenu
le canal `moteur_entendu` à 600 m : sensibilité 53 %, spécificité 100 %. Les champs journalisés par anticipation
montrent qu'à 900 m la sensibilité serait de 87 % sans un seul faux positif, et qu'en comptant « entendu au moins
une fois depuis le début de la fenêtre » elle monte encore. **Ces deux réglages ont été choisis APRÈS avoir vu les
données** : trouvés et confirmés sur les mêmes épisodes, ils ne vaudraient rien. Cette grille les confirme sur des
épisodes neufs.*

## Ce qui change, et ce qui ne change pas

- `CHACAL_PORTEE_SON` passe de 600 à **900 m**.
- Le canal retenu devient `moteur_depuis_fenetre` : **1 si un moteur a été entendu au moins une fois depuis le début
  de la fenêtre d'observation**, et non plus seulement à l'instant du choix. Un détachement qui observe se souvient
  de ce qu'il a entendu — c'est la définition honnête, et c'est celle que la sonde permettait déjà de calculer.
- Rien d'autre ne bouge : mêmes mondes, même vignette, même observation à 260 m, balayage réparé, Oracle à 0.

## Le dispositif

| bras | `menace_p2` | épisodes |
|---|---|---|
| PATROUILLE motorisée seule | 4 | 24 |
| POSTE de contrôle seul | 5 | 24 |
| AUCUNE menace | 0 | 8 |

8 mondes × 3 graines de situation (5, 6, 7) pour les deux premiers bras — **des graines neuves**, jamais jouées dans
la grille du matin, pour que la confirmation ne rejoue pas les mêmes situations. 56 épisodes, environ 1 h 15.

## Les critères, écrits d'avance

- **Confirmé** si la sensibilité de `moteur_depuis_fenetre` est **≥ 80 %** dans le bras PATROUILLE **et** si les faux
  positifs restent à **zéro** dans les bras POSTE et AUCUNE.
- **Infirmé** si la sensibilité tombe sous 65 %, ou si un seul faux positif apparaît. On revient alors à 600 m, qui
  est, lui, pré-enregistré et tenu.
- **Indécis** entre les deux : on garde 600 m et on double les épisodes avant de trancher.

## Falsificateur

« Si un moteur est entendu ne serait-ce qu'une fois dans le bras POSTE ou dans le bras AUCUNE à 900 m, la portée est
trop grande : elle capte autre chose que la patrouille, et le canal retombe à 600 m. »

## Ce qu'on en fait

Confirmé, le réglage devient celui de la campagne P2 rejouée avec la perception — celle qui dira si la règle établie
ce matin (verdict 843118c) est **apprenable** et non plus seulement vraie.
