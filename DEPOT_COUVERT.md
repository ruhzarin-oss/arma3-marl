# Dépôt — LE COUVERT : protège-t-il autant, et l'agent le cherche-t-il ? Critères AVANT

Déposé le 15/08/2026, avant toute mesure. Fait suite à `VERDICT_TARIF.md` : la piste du
tarif est fermée (Arma facture l'exposition **moins** cher, 2,87 contre 5,77), mais l'agent
s'y expose **2,5 fois plus souvent** — 55,0 % des pas contre 21,6 %.

**Ce n'est pas le prix, c'est la quantité.** Deux causes possibles, et elles se départagent.

## Les deux hypothèses

- **(A) DISPONIBILITÉ** — le couvert est plus loin sur Arma (`dcover` médiane 0,100 contre
  0,035), donc même un agent qui le cherche bien reste exposé plus longtemps.
- **(B) VALEUR** — le couvert du gymnase protège trop (mesure ancienne du projet : **11×
  trop**, +856 % contre +75 %). L'agent aurait appris à se fier à un abri qui ne tient pas
  ses promesses sur Arma.

Elles ne s'excluent pas. La mesure doit dire **laquelle porte l'écart**, ou si aucune ne le porte.

## Les grandeurs, définies une seule fois pour les deux mondes

Seuil unique, absolu, le même des deux côtés : **« à couvert » = `dcover` ≤ 0,033**
(une cellule de 6,25 m — la médiane du gymnase). Colonne 6 des douze, celle que la
politique reçoit ⟨règle 6⟩.

1. **PROTECTION** = P(mort | loin du couvert) ÷ P(mort | à couvert). **> 1 = le couvert protège.**
2. **DISPONIBILITÉ** = part des pas où l'agent est à couvert, par monde.
3. **RECHERCHE** = `dcover` moyen de l'agent comparé au `dcover` moyen du TERRAIN au même
   site (mesuré séparément par la sonde). Si l'agent vaut le terrain, **il ne cherche pas**.

## CONTRÔLES POSITIFS ⟨règle 16 clause 1⟩

1. **La protection doit être > 1 dans CHAQUE monde.** Un couvert qui ne protège pas est un
   capteur muet : aucune comparaison n'est admissible pour ce monde.
2. **Au moins 30 morts dans chaque groupe** (à couvert / loin), de chaque côté. En dessous,
   on ne lit pas. *Je sais déjà qu'Arma totalise 63 morts : ce seuil peut donc échouer, et
   je le laisse tel quel plutôt que de l'ajuster à ce que je sais.*

## Les lectures, déposées

**Sur la VALEUR (hypothèse B)** — rapport protection gymnase ÷ protection Arma :

| rapport | lecture |
|---|---|
| **> 2** | le gymnase **sur-protège**. L'agent a appris un abri qui ne tient pas sur Arma. B RETENUE. |
| **< 0,5** | Arma protège plus. B réfutée dans l'autre sens. |
| **0,5 à 2** | les deux couverts protègent pareil. **B RÉFUTÉE.** |

**Sur la DISPONIBILITÉ (hypothèse A)** — part des pas à couvert :

| écart gymnase − Arma | lecture |
|---|---|
| **> 15 points** | le couvert manque sur Arma. **A RETENUE.** |
| **≤ 15 points** | il y en a autant. **A RÉFUTÉE**, et l'agent ne s'en sert simplement pas. |

## Ce qui rendrait la mesure fausse

- protection ≤ 1 dans un monde → capteur muet, pas de lecture ;
- moins de 30 morts dans un groupe → pas de lecture pour ce monde ;
- `dcover` quasi constant dans un monde → il ne sépare rien.

## Ce qui n'est PAS promis

Si A et B sont toutes deux réfutées, l'écart d'exposition reste **inexpliqué** et il faudra
chercher ailleurs. C'est une issue admise, pas un échec de la mesure.
