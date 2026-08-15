# Dépôt — `setVelocity` est-il une impulsion ou une consigne ? Critères AVANT mesure

Déposé le 15/08/2026. Fait suite à `VERDICT_CORPS.md` : les hommes se déplacent 2,8× moins
par pas que dans le gymnase, à rendement de pilotage identique.

## L'hypothèse, et d'où elle vient

`ACT_TPL` émet `setVelocity` **une fois par pas**, et le pas dure 3,28 s. À 6 m/s soutenus
cela ferait **19,7 m par pas** ; on en mesure **1,43**. Facteur 13,8.

Un commentaire de mesure déjà présent dans `banc_live.py` (11/08) dit : *« poussée
**continue** de 6 m/s pendant 8 s, ~48 m attendus … aucun `disableAI` : 48 m »*. Donc la
poussée **tient quand on la réémet**. L'hypothèse est que `setVelocity` est une impulsion
d'une frame, pas une consigne de vitesse.

## Le dispositif

Un homme, cap fixe, trois bras, 10 périodes de 3,28 s chacun, même session :

- **bras A — UNE émission par période** : exactement ce que le banc live fait aujourd'hui ;
- **bras B — réémission à 10 Hz** pendant toute la période ;
- **bras C — aucune émission** (contrôle nul : il ne doit pas avancer).

## CONTRÔLES POSITIFS ⟨règle 16 clause 1⟩

1. **Le bras A doit reproduire ce que le banc mesure** — de l'ordre de 1,4 m par période.
   Si la sonde ne retrouve pas la lenteur connue, elle ne mesure pas le banc et rien ne se lit.
2. **Le bras C doit rendre ~0 m.** Un homme qui avance sans ordre invaliderait les deux autres.

## La porte

**Le bras B doit dépasser 10 m par période.** À 6 m/s soutenus la cible est 19,7 m ;
le seuil est posé à la moitié pour laisser la place aux frottements du moteur, aux
obstacles et à la pente.

## Les trois lectures, déposées

| B par période | lecture |
|---|---|
| **> 10 m** | `setVelocity` est une **impulsion**. Le limiteur est la fréquence d'émission, et il se retire. |
| **< 3 m** | la réémission ne change rien : la lenteur vient d'ailleurs (posture, `COMBAT`, terrain). **Hypothèse RÉFUTÉE**, on cherche ailleurs. |
| **3 à 10 m** | indécis. On ne conclut pas et on ne rejoue pas ce même essai. |

## Ce qui n'est PAS promis

Retirer le limiteur ne promet aucune prise. `VERDICT_TRANSFERT.md` reste tel quel tant que
les 20 épisodes n'ont pas été refaits avec un corps réparé — et ils pourront très bien
rendre 0 de nouveau.

Et une réserve de sincérité : un homme qui court trois fois plus vite se fera peut-être
tuer trois fois plus. **Le corps réparé n'est pas le corps meilleur** ; c'est seulement le
corps que le gymnase supposait.
