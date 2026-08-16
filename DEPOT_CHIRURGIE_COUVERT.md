# Dépôt — CHIRURGIE DU COUVERT : le TYPE, pas les coefficients. Critères AVANT.

Déposé le 16/08/2026, geste 5 du plan de Fable, pendant que les 67 tournent sur Arma.

> ⟨Fable⟩ *« Retyper le couvert au gymnase — le type, pas les coefficients. Supprimer
> `1 − 0,7·incover`. La protection n'existe que si un masque est **entre moi et le tireur**. »*
> Et : *« Un seul changement, un seul retrain. Deux chirurgies dans un retrain, tu ne sauras
> pas laquelle a agi. »*

## Ce qui justifie l'opération — trois mesures, pas une opinion

1. **Le couvert du gymnase ne cache pas** : `los = _losc(hm, …)` ne consulte que le relief,
   `cover` n'y entre nulle part. Masquage mesuré **1,08**.
2. **Il n'atténue pas non plus comme il le prétend** : sa formule promet ×3,3, il rend
   **×1,21** — `incover` est un échantillonnage bilinéaire qui n'atteint presque jamais 1.
3. **Il est mal typé** : le couvert réel est **relationnel et directionnel** — on est à
   couvert *de* quelqu'un, *derrière* un masque. `slope > 1,4 × moyenne` localise les
   **générateurs** de masque, pas les positions masquées.

## L'OPÉRATION — un seul changement

**Retirer `(1 − 0,7·incover)` du modèle de dégâts.**

La protection ne vient plus alors que de **`los`**, qui est directionnel par construction :
un rayon du tireur vers la cible à travers le champ de hauteur. **Se mettre derrière une
crête protège ; se tenir dessus ne protège plus.**

Posé derrière un **interrupteur** (`couvert_directionnel`), **éteint par défaut** : le monde
existant ne bouge pas tant qu'on ne l'allume pas, et le run Arma en cours n'est pas touché.

## Ce qui N'EST PAS fait dans le même geste

- **le cliquet d'exposition** (somme contre max irréversible) — attend son tour ;
- **la coque à 12 rayons dans l'observation** — c'est un second changement, qui modifie
  l'entrée de la politique et donc son architecture.

Une chirurgie, un retrain.

## CONTRÔLE POSITIF ⟨règle 16⟩

**Après l'opération, être derrière un masque doit protéger.** Mesuré comme le prévol du
gymnase mesure G2, mais sur `los` au lieu de `incover` :

`P(mort | exposé) ÷ P(mort | non exposé)` doit **dépasser 2**. Si la protection ne vient
de nulle part après avoir retiré la seule qui existait, le monde est devenu **sans abri**
— et c'est un monde où arriver redevient inconditionnel, la panne déjà connue.

## La porte, sur le RETRAIN

Le monde opéré doit rester **jugeable** ⟨règle 2⟩ :

| grandeur | porte |
|---|---|
| prise de la politique réentraînée | **dans 20-80 %** |
| létalité par homme-pas | dans 0,01-0,30 |
| les 8 caps déplacent | 8/8 |
| déterminisme | écart < 1e-4 |

C'est le prévol du gymnase, repassé après l'opération. **Pas de vert, pas de verdict.**

## Ce que l'opération DÉTRUIT, et qui doit partir au registre

**Tout ce qui est né dans le gymnase d'avant** : la boucle fermée (57,7 %), les courbes du
gymnase, le classement des quatre bras (FRONTAL 12,8 / FLANC 34,3 / SCRIPT 46,1 /
POLITIQUE 51,1), et le 59,4 % qui sert de référence à tout le calibrage.

⟨Fable⟩ *« Rien de valide n'est invalidé. Les acquis nés dans ce gymnase n'ont jamais été
des certificats — c'est ta propre règle. »* La cohorte **« armure »** rejoint les sursitaires.

**Ce qui survit** : tout ce qui a été mesuré **sur Arma**.

## Ce qui n'est PAS promis

Que le monde opéré donne une meilleure politique. Il peut donner **pire** — un monde sans
abri scalaire est plus dur, et la prise peut tomber. Ce serait un résultat : le nouveau
monde serait alors **plus juste et plus difficile**, et c'est le classement qui trancherait.
