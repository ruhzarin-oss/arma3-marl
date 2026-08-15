# Amendement au dépôt du couvert — « à couvert » se lit sur `incover`, pas sur `dcover`

Déposé le 15/08/2026. Amendement énoncé **sans référence à un résultat** ⟨règle 13⟩ : il ne
fait que **resserrer** la définition, et il s'applique symétriquement aux deux mondes.

## Ce qui change

Le dépôt initial définissait « à couvert » par `dcover ≤ 0,033`, soit **à une cellule** du
couvert. Ce n'est pas la grandeur que le mécanisme emploie. Dans `assault_terrain.py`, la
formule de dégâts lit :

```python
incover = TG.sample(self.cover, apx, apy, scale).clamp(max=1.0)   # SUIS-JE SUR une cellule de couvert
dmg_a  += _p * los * tir * (1.0 - 0.7 * incover)                   # c est CELA qui protege
```

`dcover` n'apparaît que dans **l'observation** ; il informe l'agent, il ne le protège pas.
Être à une cellule du couvert n'est pas être dessus.

## La définition qui remplace, identique des deux côtés

**« à couvert » = être SUR une cellule de couvert.**

- **gymnase** : `incover > 0,5`, lu directement dans le moteur, là où les dégâts le lisent ;
- **Arma** : `dcover == 0` cellule — par construction du champ de distance, une distance
  nulle signifie exactement « la cellule courante est du couvert ».

⚠️ **Asymétrie assumée et déclarée** : le gymnase échantillonne `cover` en bilinéaire, donc
`incover` y est continu ; Arma calcule une distance entière par anneaux, donc son critère
est net. Les deux nomment la même chose, ils ne l'arrondissent pas pareil.

## Ce qui NE change pas

Les deux contrôles positifs et les trois bandes de lecture sont **repris à l'identique** :

- protection = P(mort | loin) ÷ P(mort | à couvert), **> 1 dans CHAQUE monde** sinon capteur
  muet et aucune lecture ;
- **≥ 30 morts par groupe**, de chaque côté ;
- rapport gymnase ÷ Arma : **> 2** → le gymnase sur-protège, B retenue · **0,5 à 2** → B
  réfutée · **< 0,5** → réfutée dans l'autre sens.

## Pourquoi cet amendement est légitime

Il **resserre** : il remplace un proxy par la grandeur que le mécanisme emploie ⟨règle 16
clause 2⟩. Il ne relâche aucun seuil, n'élargit aucune bande, et s'applique aux deux mondes
de la même façon.

L'hypothèse **A (disponibilité) reste lue sur `dcover`** — c'est la grandeur que l'agent
*observe*, et la question A porte précisément sur ce qu'il trouve de ce qu'il a appris à
chercher.
