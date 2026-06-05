# Le modèle expert, traduit en clair (sans mathématiques)

Ce document reprend les formules du corpus théorique
([arma3-marl-theorie-complete.md](arma3-marl-theorie-complete.md)) et dit, en langage ordinaire
et sobre, **ce que chaque objet mathématique affirme**. Rien n'est simplifié au point d'être
faux : c'est la même chose, dite autrement.

---

## Ce que décrit la formule du problème

Le modèle s'ouvre sur une liste de symboles — `⟨I, S, {Aᵢ}, T, R, {Ωᵢ}, O, h, γ⟩`. C'est
l'inventaire complet de la situation, les pièces du jeu :

- **les acteurs** : les quatre soldats ;
- **l'état du monde** : la vérité complète de la scène à un instant donné (positions réelles de
  tous, ennemi compris, munitions, terrain). Personne ne la connaît entièrement ; elle existe ;
- **les actions possibles** de chaque soldat ;
- **la règle d'évolution du monde** : telle situation + tels gestes → ce qui s'ensuit. Cette
  règle n'est pas écrite : **c'est Arma 3 qui la joue** ;
- **la récompense** : le signal « c'est bien / c'est mal » ;
- **ce que chacun perçoit** : sa fraction du monde, son champ de vision et d'ouïe.

Deux lettres importantes :
- **γ (« gamma »)**, entre 0 et 1 : une réussite obtenue tout de suite vaut un peu plus que la
  même réussite plus tard. L'impatience raisonnable — et ce qui empêche les calculs de partir à
  l'infini.
- **𝔼 (« espérance »)** : « en moyenne, sur un très grand nombre de parties ». Comme l'ennemi et
  le hasard rendent chaque partie différente, on juge un comportement sur sa moyenne, pas sur un
  coup de chance.

## Les deux lois, en une ligne

La formule *maximiser 𝔼[Σ γᵗ R] sous contrainte 𝔼[Σ γᵗ C] ≤ c* dit, simplement :

> **Accomplir la mission le mieux possible, en moyenne, à condition que les pertes attendues ne
> dépassent pas un seuil que tu fixes.**

`Σ γᵗ R` = la totalité de ce que le comportement rapporte au fil du temps, additionné, le futur
lointain pesant un peu moins. `C` = le compteur des pertes ; `c` = le seuil acceptable. La forme
« maximiser… sous contrainte… » est délibérée : **la survie n'est pas mise en balance avec la
mission comme deux objectifs de même rang** ; elle est une *limite à ne pas franchir*. On cherche
la meilleure mission possible **à l'intérieur** de ce que la prudence autorise.

## Pourquoi l'on renonce à la solution parfaite

Le tableau des complexités (P, PSPACE, **NEXP**) dit une seule chose, capitale : **trouver la
stratégie parfaitement optimale d'une équipe est d'une difficulté si démesurée qu'elle est hors
de portée, même pour une poignée d'agents.** Ce n'est pas « long à calculer » : c'est démontré
inatteignable. D'où la suite : on vise *l'excellent atteignable*, en s'appuyant sur la structure
de l'équipe (rôles, hiérarchie).

## Comment on mesure la valeur d'un geste

La lettre **Q** est une **note** : elle évalue « faire tel geste dans telle situation » par tout
le bien que ce geste rapportera *ensuite*, jusqu'à la fin. Apprendre = affiner ces notes par
l'expérience. Il y a la note de chaque soldat et la note de l'équipe.

Le **principe IGM** (`argmax Q_tot = (argmax Q₁, …, argmax Qₙ)`) dit :

> **Si chaque soldat choisit ce qui paraît le meilleur de son propre point de vue, le résultat
> doit coïncider avec le meilleur choix pour l'équipe entière.**

Ce n'est pas automatique : il faut *construire* les notes pour que cette coïncidence soit
garantie. Trois façons :
- **L'addition** (`Q_tot = Σ Qᵢ`) : la valeur d'équipe = somme des valeurs individuelles.
  Commode mais aveugle aux interactions.
- **La monotonie** (`∂Q_tot/∂Qᵢ ≥ 0`) : **« si la situation d'un seul membre s'améliore, sans
  toucher aux autres, la note de l'équipe ne peut que monter ou rester égale. »**
- **La limite** : un débordement à deux est excellent ; un seul homme qui s'élance sans couverture
  est *pire que de ne rien faire*. Là, améliorer le geste d'un seul **dégrade** l'ensemble — ce
  que la monotonie interdit de représenter. Pour les manœuvres en tout-ou-rien, il faut un modèle
  plus expressif.

## Comment on apprend, et comment on attribue le mérite

Le **gradient de politique** (`∇J = 𝔼[∇ log π · A]`) :

> **Ajuster le comportement par petites touches, dans le sens qui, en moyenne, a donné un
> résultat meilleur que prévu.** (`A`, « l'avantage » = de combien le geste a fait mieux
> qu'attendu.)

L'**avantage contrefactuel** (COMA) répond à « grâce à qui ? » :

> **Pour mesurer la contribution d'un soldat, on compare ce qui s'est passé à ce qui se serait
> passé, en moyenne, s'il avait agi autrement — les trois autres faisant la même chose.**

Si tout se passe aussi bien quel que soit son geste, il n'a rien apporté de décisif ; si son
geste a fait basculer l'issue, son mérite est réel.

## Le curseur du risque

Le **lagrangien** (`ℒ = Q^R − λ(Q^C − c)`) :

> **On note un plan par sa valeur de mission, dont on retranche une pénalité proportionnelle au
> dépassement du seuil de pertes acceptable.**

Le **λ (« lambda »)** est un **curseur — le prix du risque — qui se règle tout seul** : tant que
les pertes dépassent le seuil, il monte (la prudence devient chère) ; dès qu'elles repassent
dessous, il redescend (l'audace revient). Tu ne fixes pas un compromis figé ; tu fixes une
**limite de pertes**, et le curseur trouve le juste niveau d'audace qui la respecte.

## Qui est qui, et qui commande

Le geste d'un spécialiste (`π(a | oᵢ, rᵢ, gᵢ)`) :

> **Le geste d'un soldat dépend de trois choses : ce qu'il perçoit à l'instant, qui il est (sa
> capacité fixe — médecin, mitrailleur), et la tâche qu'on vient de lui confier.**

La capacité ne change jamais ; la tâche change au gré de la mission, et c'est le chef qui la fait
changer. La fonction du chef, les **options** (`⟨I, π, β⟩`), tient en trois mots :

> **quand une manœuvre peut commencer, comment elle se déroule, à quelle condition elle s'achève.**

Le chef ne dicte pas chaque pas : il déclenche des manœuvres qui *durent*, à une cadence plus
lente que ses soldats.

## Agir sans tout voir

La **croyance** (`b(s) = P(s | historique)`) :

> **À défaut de connaître la vérité du terrain, chaque soldat entretient une estimation — une
> carte mentale probable de ce qui l'entoure — fondée sur tout ce qu'il a vu et entendu.**

D'où le besoin de **mémoire** (le passé sert à deviner le présent caché), et la **valeur de la
reconnaissance** (lever l'incertitude vaut, en soi, une récompense).

## Encourager sans corrompre le but

Le **façonnage par potentiel** (`F = γΦ(s') − Φ(s)`) résout : la mission ne se récompense qu'à la
fin, trop rarement pour guider l'apprentissage. On voudrait des encouragements en chemin — mais à
trop récompenser des gestes intermédiaires, la machine apprend à *collectionner les
encouragements* au lieu de gagner.

> **C'est la seule manière prouvée de distribuer des encouragements sans jamais détourner le but
> final.** Un garde-fou : tout autre encouragement bricolé risque de produire un soldat zélé qui
> perd la guerre.
