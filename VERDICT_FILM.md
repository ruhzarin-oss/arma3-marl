# LE FILM — **R2, bifurcation précoce** : l'argmax de la graine 1 n'a JAMAIS été bon

**24/08/2026, 19 h.** Règles **déposées avant ouverture** (`8b687a7`), appliquées
mécaniquement par le script. 24 points par graine, évalués sur **GRAINES_SELECT**
— jamais sur TEST.

## La mesure

| graine 1, itération | 100 | 250 | **300** | 700 | 950 | **1150** |
|---|---|---|---|---|---|---|
| **argmax** | 6,4 % | 6,2 % | **0,0 %** | 1,8 % | 7,9 % | **1,7 %** |
| échantillonnage | 0,1 % | 0,9 % | 1,4 % | 24,5 % | 32,4 % | **39,6 %** |

- **graine 1** : maximum de l'argmax sur les 24 points = **7,9 %**. Aucun point au-dessus
  de 30 %. Aucun couple consécutif.
- **graine 0** : maximum **52,5 %**, minimum après décollage **43,0 %**, écart-type des huit
  derniers points **2,0** — **stable**.

## Les trois règles, telles qu'elles étaient écrites

| règle | verdict |
|---|---|
| **R1 intermittence** | **ne s'applique pas** — zéro point au-dessus de 30 % |
| **R3 oscillation de G0** | **ne s'applique pas** — écart-type 2,0 : le **49,6 % de la graine 0 n'était pas la chance de l'itération d'arrêt** |
| **R2 bifurcation précoce** | **S'APPLIQUE** — G₁ < 10 % partout, G₀ tient ≥ 30 % de façon stable |

> ## Le sort se scelle tôt. **Sélectionner un point de sauvegarde ne peut pas sauver cette graine** : il n'y a jamais eu de bon point à choisir.

## Le détail qui affine

L'argmax de la graine 1 vaut **6-8 % entre les itérations 100 et 250**, tombe à
**exactement 0,0 % à l'itération 300**, et ne repasse jamais durablement au-dessus.
**Il y a bien un effondrement**, daté — mais il part d'un niveau qui n'était **déjà pas
utilisable** (8 % contre les 34,3 % du flanc). **Ce n'est pas une chute d'un sommet, c'est
l'extinction d'une lueur.**

Et pendant tout ce temps, la lecture **échantillonnée monte sans discontinuer**, 0 → 39,6 %.
**Les deux lectures divergent dès le départ et ne se rejoignent jamais.**

## Ce que ça établit

**La loterie est au niveau de la GRAINE, pas de l'instant d'arrêt.** Une graine
s'engage tôt vers un mode utilisable ou n'y va jamais. Le geste praticable devient donc :

> **entraîner plusieurs graines · choisir sur SELECT · juger sur TEST, une fois, après le
> choix.**

⚠️ **Et c'est une recette, pas une réparation.** Fable l'avait nommé d'avance : *acheter un
tirage n'est pas améliorer une recette.* Ça rend le pipeline **utilisable** et ça laisse la
cause de la bifurcation **entière**.

⭐ **Cliquet : quand une panne est un tirage, la réponse honnête est une recette de
sélection déclarée — pas un correctif qui ferait croire à une compréhension.**

## Le compte des hypothèses

**Huit tombées en deux jours, toutes sur mesure** : la rente de γ · le budget seul · le
continuum de netteté · le portefeuille d'équipe · la normalisation comme cause du signal
rare (**partiellement — la question du gradient aux états décisifs reste ouverte**) · la
colinéarité biais-compas · le biais qui capturerait le mode · et enfin l'intermittence.
**Quatre étaient de Fable, quatre étaient de moi.**

**Aucune réparation n'a été faite sur une cause supposée.** C'est ce que ces rejeux ont
acheté, et c'est leur seule justification.

## Ce qui reste ouvert, et qu'on écrit tel quel

**Pourquoi une graine s'engage-t-elle tôt vers un mode utilisable et l'autre pas ?**
Inexpliqué. Les deux lectures divergent dès les premières dizaines d'itérations : c'est là
qu'il faudrait regarder, avec des points beaucoup plus serrés (toutes les 5 itérations sur
les 100 premières) — **si on décide un jour que la cause vaut son prix.**
