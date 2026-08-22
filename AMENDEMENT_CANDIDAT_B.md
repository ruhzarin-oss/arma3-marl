# AMENDEMENT AU CANDIDAT B — deux observables sur quatre ne sont pas des mesures

**22/08/2026, écrit AVANT toute mesure du candidat B.** Règle 13 : un amendement s'énonce
**sans référence à un résultat** et ne peut que **RESSERRER**.

## Le fait, lu dans le code, pas déduit

La pré-inscription demande quatre observables. Deux d'entre eux **n'existent pas** comme
comportement du côté gymnase — ce sont des **paramètres tapés dans le monde**, et ils ont
été **ajustés sur Arma** :

| observable | côté gymnase | origine |
|---|---|---|
| distance du premier tir | la courbe de toucher s'éteint d'elle-même | `courbe_toucher_monotone.json`, **mesurée sur Arma le 26/07** |
| coups par pas | `tir_par_pas = 1,15`, constante | commentaire du code : *« balles tirées par un défenseur pendant un pas (**mesure sur Arma**) »* |

Le gymnase ne fait pas tirer un défenseur : il applique
`p = p_balle(dist) × tir_par_pas × degat_par_impact`, un **dégât espéré par pas**.

> **Comparer ces deux-là entre les deux mondes, c'est comparer Arma à son propre calque.**
> Le résultat est connu d'avance dans les deux sens : ils concordent parce qu'on les a
> ajustés, ou ils divergent et c'est un **défaut d'ajustement**, pas une différence de
> tactique.

## Ce que l'amendement change — il ne fait que retirer

**B1 ne peut plus être satisfaite par ces deux observables.** Elle doit passer sur l'un des
**deux qui restent**, et qui sont **émergents des deux côtés** :

- **fraction du temps où l'attaquant est touché** — dépend de l'exposition que la manœuvre crée ;
- **pertes attaquantes à la fin** — l'issue.

**B1 passe donc de quatre chances à deux.** C'est strictement plus dur. **B2 est inchangée**,
et reste la prédiction importante : l'**ordre** des trois manœuvres.

## Ce qui ne change pas

Les deux observables ajustés seront **quand même mesurés et publiés**, comme **contrôle de
calibration** : si la courbe mesurée sur Arma le 26/07 ne se retrouve pas dans Arma
aujourd'hui, c'est le **gymnase** qui a dérivé, et il faut le savoir. Ils ne comptent
simplement **pas** pour B1.

Seuils inchangés : **30 %**, posés dans `82101f9`. Manœuvres inchangées : **frontale
directe**, **flanc**, **arrêt à mi-distance**. Liste des candidats toujours **fermée**.

⭐ **Cliquet : un observable ajusté sur le monde qu'il doit juger ne juge plus rien.**
Il ne mesure que la qualité de son propre ajustement — et il le fait passer pour un résultat.
