# Le couvert du gymnase NE CACHE PAS — confirmé. Côté Arma : INDÉCIS, et mes bandes ont un trou.

Mesuré le 15/08/2026. Critères déposés dans `DEPOT_CACHER.md`. Contrôle positif passé
(≥ 100 pas par case des deux côtés). Portes exécutées avant les données ⟨règle 18⟩.

## Ce qui est ÉTABLI — côté gymnase

```
SUR le couvert : 1333 pas · P(exposé) = 0,229
hors couvert   : 4802 pas · P(exposé) = 0,212
RAPPORT DE MASQUAGE = 1,08
```

**Le couvert du gymnase ne cache rien.** La lecture de code l'annonçait —
`los = _losc(self.hm, …)` ne consulte que le relief, `incover` n'entre que dans les dégâts —
et la mesure le confirme : 1,08, indiscernable de 1.

**Au gymnase, être à couvert retire 70 % des dégâts et laisse parfaitement visible.**

## Ce qui n'est PAS tranché — côté Arma

```
SUR le couvert :  150 pas · P(exposé) = 0,727
hors couvert   : 1164 pas · P(exposé) = 0,530
RAPPORT DE MASQUAGE = 1,37
```

Sur Arma, se tenir sur ce que le capteur appelle « couvert » est associé à **plus**
d'exposition, pas moins. Physiquement cohérent : une cellule pentue est une crête ou un
versant — de la hauteur, donc de la silhouette.

**Mais 1,37 tombe HORS de toutes mes bandes.** J'avais prévu « Arma cache » (< 0,7) et
« Arma ne cache pas » (≈ 1) ; jamais « Arma expose davantage ». **La lecture déposée est
INDÉCIS et je m'y tiens.**

## Ce que ça apprend sur la règle 18 — cinquième critère troué

Le banc de la règle 18 a fait passer mes **quatre** cas fabriqués : chaque bande était
atteignable et rejetable. **Il ne vérifie pas que les bandes PARTITIONNENT l'espace.**

Un résultat réel est tombé dans un trou et s'est lu « indécis » alors qu'il dit quelque
chose de fort. C'est la cinquième fois aujourd'hui qu'un de mes critères a un défaut
démontrable **sans données** — il suffisait de balayer le domaine des couples possibles.

**Clause à ajouter à la règle 18** : le banc énumère le domaine des valeurs possibles et
vérifie qu'**aucune région n'est sans lecture**. Une bande « indécis » doit être **choisie**,
jamais **subie**.

## Ce que la mesure ne dit pas

- Le chiffre d'Arma reste **confondu** : conditionner sur le couvert ne fige pas les onze
  autres colonnes, exactement comme pour le verdict « exposition CHOISIE ».
- 150 pas sur le couvert côté Arma contre 1333 côté gymnase : précision très asymétrique.
- Et rien ici ne dit comment corriger. Deux voies existeraient — donner à Arma un couvert
  qui protège, ou retirer au gymnase son multiplicateur — et **la seconde changerait le
  monde d'entraînement, donc invaliderait tout ce qui y a été mesuré.**

## Ce qui reste debout

Le fait du gymnase est net et il est gros : **son couvert protège sans cacher.** Un agent
qui y apprend peut rationnellement rester visible sur un abri. Sur Arma, aucun multiplicateur
de ce genre n'existe — la seule protection est de rompre la vue. **Ce désaccord de mécanisme
est lu dans le code des deux côtés ; ce qui manque, c'est sa taille mesurée sur Arma.**
