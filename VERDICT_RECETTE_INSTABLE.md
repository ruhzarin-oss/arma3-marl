# ⛔ LA RECETTE EST UNE LOTERIE — et la panne n'est pas où je la cherchais

**23/08/2026, 23 h 15.** Prédiction déposée avant (`ae53703`) : *« à 1 200 itérations la
porte passe, sur les DEUX graines »*, avec ce cas écrit d'avance :
> *« Si les deux graines DIVERGENT, on ne cite ni l'une ni l'autre : c'est la recette qui
> est instable, et c'est un résultat en soi. »*

**Elles divergent. Le cas s'applique. Aucun des deux chiffres ne se cite.**

| | graine 0 | graine 1 |
|---|---|---|
| **à la porte (argmax, graines jamais vues)** | **49,6 %** | **3,3 %** |
| G1 contre frontale (12,8 %) | +36,8 (borne +34,3) ✓ | −9,4 (borne −10,9) ✗ |
| G1 contre flanc (34,3 %) | +15,3 (borne +12,2) ✓ | −31,0 (borne −33,8) ✗ |
| G3 mètres | 113,5 ✓ | 79,4 ✗ |
| verdict | **LA BOUCLE EST FERMÉE** | LA PORTE NE PASSE PAS |

**Même recette, même budget, même monde. Seule la graine de `torch` diffère.**

## ⭐⭐⭐ Et la graine 1 avait APPRIS

Sa courbe d'entraînement monte **tout du long**, et finit **plus haut que la graine 0** :

| itération | 0 | 320 | 640 | 960 | **1199** |
|---|---|---|---|---|---|
| prise en entraînement | 0,0 % | 3,5 % | 27,0 % | 39,5 % | **44,1 %** |

> ## 44,1 % en entraînement, **3,3 % à la porte**.
> **Ce n'est pas un échec d'apprentissage. C'est un effondrement à l'évaluation.**

**La différence entre les deux mesures est une seule ligne** : l'entraînement **échantillonne**
(`Categorical(logits).sample()`), la porte prend l'**argmax** (`boucle.py:194`).

**La graine 1 a appris une politique qui ne marche QUE stochastique.** Figée, elle s'effondre.
La graine 0 a appris une politique qui supporte d'être figée : 38 % en échantillonnant,
**49,6 %** en argmax.

**Rien dans l'entraînement ne contrôle cette propriété** — et c'est cohérent avec deux des
défauts trouvés cet après-midi (`97b996e`) : **aucun terme d'entropie** dans la perte, et
l'**avantage normalisé pas par pas**, qui gonfle le bruit des pas où rien n'arrive.

## Ce que ça retire à ce qui a été dit aujourd'hui

- **« C'était le budget »** devient **incomplet**. Le budget fait monter la courbe
  d'entraînement des deux côtés ; il ne dit rien de la survie à l'argmax.
- **Les 50,7 % de l'artefact du 13/08 sont probablement une queue de distribution** —
  Fable l'avait écrit et j'avais glissé dessus. Une graine sur deux.
- **Le 49,6 % de la graine 0 ne se cite pas non plus.** C'est la règle, elle était déposée.

## ⛔ Et le pipeline détruit ses propres preuves

`pol_1200_g1.pt` **n'existe pas** : le `torch.save` est **à l'intérieur** du `if ok1 and ok2
and ok3`. **La recette ne garde que les politiques qui passent** — donc elle efface
exactement celles qu'il faudrait ouvrir pour comprendre pourquoi elles échouent.

Je ne peux **pas** faire le test à deux minutes qui trancherait — rejouer la graine 1 en
échantillonnant au lieu de l'argmax — parce que l'objet a été jeté.

⭐ **Cliquet : un banc qui ne garde que ses réussites ne peut pas expliquer ses échecs.**

**Correction à faire** : toujours sauvegarder, sous un nom qui porte le verdict
(`..._PASSE.pt` / `..._TOMBE.pt`). Ça ne change aucun seuil et ça ne rend rien vert.

## La suite, telle qu'elle se dérive

1. **Réparer la sauvegarde** (aucun effet sur les critères).
2. **Rejouer la graine 1** et, sur l'artefact conservé, mesurer **argmax contre
   échantillonnage sur les MÊMES graines**. Deux issues : si l'échantillonnage rend ~44 %,
   c'est une **dégénérescence de l'argmax** ; s'il rend aussi 3 %, c'est un
   **sur-apprentissage** aux graines d'entraînement. Les deux appellent des gestes opposés.
3. **Rien d'autre.** Pas d'entropie ajoutée avant de savoir laquelle des deux c'est —
   sinon on aurait un banc vert et aucune compréhension.
