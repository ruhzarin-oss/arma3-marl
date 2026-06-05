# CMDP / Lagrangien
### « Réussir la mission sans franchir la ligne rouge »

## Le problème qu'il résout

Ton cahier des charges dit : « remplir la mission **et** rester en vie ». La tentation est de tout
fondre dans une seule récompense : *réussite − pénalité_pertes*. Mauvaise idée. D'abord, comment
fixer le taux de change entre « un objectif pris » et « un homme perdu » ? Tout chiffre est
arbitraire. Ensuite — résultat mathématique — une simple somme pondérée **ne peut atteindre que
certaines solutions** (la partie « convexe » des compromis possibles) : des plans pourtant
excellents deviennent **inatteignables** quel que soit le réglage. La survie n'est pas un objectif à
marchander librement ; c'est une **limite**.

## L'idée centrale

**Maximiser la mission sous une contrainte de pertes**, et non additionner les deux. On ne cherche
pas « un peu moins de morts contre un peu moins de mission » ; on cherche *la meilleure mission
possible, tant que les pertes restent sous un seuil que tu fixes*. Pour résoudre ce problème
« sous contrainte », on le transforme astucieusement en un problème ordinaire avec un **curseur
auto-réglé**.

## Le mécanisme, pas à pas

1. On définit **deux** signaux : la **récompense** (réussite de mission) et le **coût** (les pertes).
2. On fixe un **seuil** de coût acceptable (« je n'accepte pas plus de tant de pertes attendues »).
3. On introduit un curseur **λ** (le « prix du risque »).
4. On entraîne la politique à maximiser : *réussite − λ × (dépassement du seuil)*.
5. **On ajuste λ automatiquement** : si les pertes dépassent le seuil, λ monte (la prudence devient
   chère) ; si elles repassent dessous, λ redescend (l'audace revient). Ce va-et-vient converge vers
   le juste niveau.

## Les formules, traduites

**① L'objectif sous contrainte.**

<div class="formule">maximiser (réussite de mission)  TANT QUE  (pertes attendues) ≤ seuil que tu choisis</div>

> *Pour un littéraire :* l'ordre de mission réaliste — « prends l'objectif, mais je n'accepte pas
> plus de tant de pertes ». Le seuil, c'est le *niveau de risque acceptable*.

**② Le curseur (le « lagrangien »).**

<div class="formule">note = (réussite de mission) − λ · (dépassement du seuil de pertes)</div>

> *Pourquoi ce tour de passe-passe marche :* transformer une contrainte en pénalité réglable est une
> technique classique d'optimisation (les « multiplicateurs de Lagrange »). Le génie ici est que λ
> n'est pas fixé à la main : il s'apprend.

**③ Le réglage automatique de λ.**

<div class="formule">trop de pertes → λ monte (prudence chère) ; pertes sous le seuil → λ baisse (audace permise)</div>

> *En clair :* tu ne règles pas un compromis figé ; tu poses une **limite**, et le curseur trouve
> de lui-même l'agressivité qui la respecte, en se resserrant ou se relâchant au fil de l'apprentissage.

## Un exemple concret

Au début, les agents foncent : pertes au-dessus du seuil. λ grimpe ; soudain, chaque mort « coûte »
très cher dans la note, et la politique apprend à temporiser, à mieux se couvrir, à attendre la
suppression avant d'avancer. Les pertes retombent sous le seuil ; λ se détend ; un peu d'audace
revient. Le système oscille puis se stabilise sur le **plan le plus offensif compatible avec le
seuil de pertes** — exactement ce qu'on voulait.

## Variantes & pièges

- **CPO** : impose la contrainte par une région de confiance (plus rigoureux).
- **MAPPO-Lagrangian / MACPO** : les versions **multi-agents sous contrainte** — celles de ton projet.
- **CVaR** (raffinement avancé) : au lieu de borner la *moyenne* des pertes, borner le *pire cas*
  (la queue de distribution) — plus réaliste pour du combat, mais plus exigeant.
- *Pièges :* λ qui oscille trop (réglage de sa vitesse d'ajustement) ; et la contrainte n'est
  garantie qu'**à convergence**, pas forcément pendant l'exploration (d'où le besoin de sécurité
  pendant l'entraînement).

## Pourquoi on l'utilise ici

C'est la traduction **exacte** de « remplir la mission et rester en vie », avec la survie posée comme
contrainte d'équipe. Le curseur λ régule l'audace tactique tout seul — tu n'as qu'à fixer le seuil
de pertes acceptable, le reste s'ajuste.

<div class="philo">En dernier regard. Ce curseur tranche une vieille querelle morale. Le conséquentialiste met tout dans une même balance et calcule le meilleur solde ; le déontologue pose des limites qu'aucun bénéfice ne saurait acheter. Le CMDP fait les deux à la fois : il maximise un résultat, mais sous une frontière qu'il traite comme inviolable. Et son λ — ce prix du risque qui s'élève à mesure qu'on approche de la limite — dit quelque chose de troublant et de juste : plus on s'approche de l'inacceptable, plus la prudence doit coûter cher, jusqu'à devenir prohibitive. Mettre un prix sur le risque sans jamais mettre un prix sur l'interdit : c'est, peut-être, une définition opératoire de la sagesse pratique.</div>
