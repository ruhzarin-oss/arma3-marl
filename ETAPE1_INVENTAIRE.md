# Inventaire de l'étape 1 — sur pièces, pas sur souvenir

*4 août 2026, 23h10. Établi en relisant les artefacts sur disque, après avoir déclaré à
tort à Fable que « les trois sondes n'ont jamais été lancées ».*

## Pourquoi cet inventaire

J'ai affirmé ce soir que l'étape 1 était vierge. C'était faux, et je l'ai affirmé **de
mémoire**. Puis j'ai déduit que la sonde 1 avait tourné parce que `monde_somme.pt` et
`monde_attention.pt` existaient — faux aussi : la sonde 1 ne sauvegarde aucun modèle.

Deux suppositions de suite sur le même sujet. D'où la règle appliquée ici : **rien n'est
déclaré fait ou non fait sans une pièce datée à l'appui.**

## Sonde 1 — la somme contre l'attention : FAITE, et elle PASSE

Les résultats ne sont conservés dans aucun journal : la sonde n'imprime qu'à l'écran.
Ils sont retrouvés **cités dans l'en-tête de `monde.py`**, écrit le 3/08 à 14h — donc
postérieur, et par la même main.

| critère écrit avant | mesuré | verdict |
|---|---|---|
| 1. les ennemis doivent apporter | **+44,6 %** de pouvoir prédictif | PASSE |
| 2. l'attention bat la somme de ≥ 5 % du gain | **+6,1 %** | PASSE |
| 3. sur un seul ennemi, écart ≈ 0 | **0,0025** | PASSE |

> **L'attention lit ce que la somme détruit. Le verrou de l'encodeur est confirmé.**

Le troisième critère est le plus important : il écarte l'explication par l'architecture.
Avec un seul ennemi, pondérer ou additionner revient au même — et c'est ce qu'on observe.
L'avantage vient donc bien de la lecture des liens.

## Sonde 3 — le verdict connu du flanc : FAITE, et elle PASSE

Citée dans `CRITERES_AGENT.md` : être dans le champ ennemi multiplie le risque par
**1,75**, sur **563 000 observations**, avec une pente mesurée de +45 % à 80 m à +84 % à
300 m. C'est le fait qui fonde tout le travail sur l'angle mort.

## Sonde 2b — le brouillage des arêtes : AUCUNE TRACE

Le fichier existe (écrit le 3/08 à 10h11) et porte la correction de son premier jet — qui
mesurait la persistance au lieu des arêtes. Mais **aucun résultat n'est consigné nulle
part**, ni journal, ni citation, ni artefact.

Statut : **non faite**. Elle teste la *nécessité* des liens (les brouiller dégrade-t-il la
prédiction ?), là où la sonde 1 teste la *lecture* des liens. Les deux ne se remplacent pas.

## Ce que l'inventaire a trouvé en plus, et qui n'a jamais été jugé

`monde.py` — **l'étape 3, la prédiction** — a tourné le 3/08 à 14h et laissé
`monde.json`. **Son verdict n'a jamais été écrit.** Le voici, contre ses propres critères :

```
persistance   err 0,015786          le modèle bête « rien ne change »
somme         err 0,015829   −0,27 %  contre la persistance
attention     err 0,015619   +1,06 %  contre la persistance
attention contre somme : +1,32 %    (critère 2 : ≥ 3 %)
AUC : 0,9996 et 0,9995              (critère 3 : > 0,6)
```

| critère | verdict |
|---|---|
| 1. battre la persistance | **la somme ÉCHOUE** (elle fait pire). L'attention passe de 1,06 % |
| 2. l'attention bat la somme de ≥ 3 % | **ÉCHOUE** — 1,32 % |
| 3. AUC > 0,6 | passe, mais **sans valeur** : 0,9996 sur « sera-t-il vivant au pas suivant » est trivial à 5 Hz, presque personne ne meurt en 0,2 s |

> **Le modèle du monde n'apporte presque rien face à « rien ne change ».**
> Et l'écart attention/somme, qui valait +6,1 % sur « qui va mourir à 30 s », tombe à
> +1,32 % sur « que devient le monde au pas suivant ».

Ce n'est pas contradictoire, c'est instructif : à 5 Hz, prédire le pas suivant est une
tâche presque vide. La structure relationnelle ne paie que sur un horizon où elle a le
temps d'agir — 30 secondes, pas 0,2 seconde.

## État réel de l'étape 1

**Deux sondes sur trois faites, toutes deux positives.** Le verrou de l'encodeur est
confirmé par mesure. L'étape 1 n'est ni vierge ni close : il lui manque la 2b.

## Ce que ça change pour la suite

1. **Ne pas relancer la sonde 1.** Son verdict existe, il est positif, il est ici.
2. **La 2b reste à faire**, et elle est peu coûteuse.
3. **`monde.py` doit être rejugé, pas relancé** : son échec est dû à l'horizon, pas à
   l'architecture. Un pas de 0,2 s ne laisse rien à prédire.
4. Et surtout — le verrou de l'encodeur étant confirmé, **l'agent qui échoue au banc 150 m
   agrège toujours ses ennemis d'une manière que la sonde 1 a mesurée comme inférieure.**
   C'est le lien direct entre l'étape 1 et le refus de l'étape 4.
