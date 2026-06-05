# PLR — Curriculum automatique
### « Apprendre toujours au bord de sa compétence »

## Le problème qu'il résout

Si tu entraînes ton équipe sur **une seule** mission, elle la **mémorise** sans rien comprendre de
général : déplace l'objectif de cent mètres, change la position ennemie, et elle s'effondre. C'est le
**sur-apprentissage de l'environnement**. La parade évidente — tirer des missions au hasard — est
inefficace : la moitié sont trop faciles (l'équipe n'y apprend rien) ou trop dures (elle ne fait
qu'échouer sans rien comprendre). On gaspille l'essentiel du temps d'entraînement.

## L'idée centrale

**Ne pas tirer les missions au hasard : rejouer en priorité celles où l'équipe a le plus à
apprendre.** Ni trop faciles, ni impossibles — celles, justement, qui sont *en train* de
s'apprendre. Et laisser ce choix se faire **tout seul**, à partir des erreurs de l'équipe.

## Le mécanisme, pas à pas

1. On dispose d'un vivier de missions (positions, cartes, dispositifs ennemis variés — éventuellement
   générés automatiquement).
2. Quand l'équipe joue une mission, on mesure son **potentiel d'apprentissage** : à quel point ses
   pronostics y sont encore démentis (l'ampleur de ses « surprises »).
3. On garde un **score de priorité** par mission.
4. Pour la suite, on **rejoue plus souvent** les missions à fort potentiel, **moins souvent** celles
   déjà maîtrisées (où l'équipe ne se trompe plus).
5. À mesure que l'équipe progresse, les priorités **se recalculent** : le programme se déplace tout
   seul vers la nouvelle frontière de difficulté.

## Les formules, traduites

**① Le potentiel d'apprentissage d'une mission.**

<div class="formule">priorité d'une mission ∝ ampleur des surprises qu'elle provoque (à quel point l'équipe s'y trompe encore)</div>

> *Pour un littéraire :* une mission est « intéressante » tant qu'elle nous surprend. Quand elle ne
> nous surprend plus, c'est qu'elle est maîtrisée : on passe à autre chose. Le symbole « ∝ » se lit
> « proportionnel à ».

**② Le tirage priorisé.**

<div class="formule">on rejoue souvent les missions à fort potentiel, rarement celles déjà acquises</div>

> *Pourquoi ça généralise :* en restant en permanence à la frontière, l'équipe est forcée de
> rencontrer sans cesse du *nouveau* difficile — donc d'apprendre des principes transférables, pas
> une carte par cœur.

## Un exemple concret

Au début, la mission « objectif à découvert, sans couverture » est ingérable : l'équipe échoue
toujours, surprise maximale → forte priorité, on la rejoue souvent. Une fois la tactique de
progression par bonds maîtrisée, cette mission cesse de surprendre → sa priorité chute, on la rejoue
peu. Entre-temps, une mission « objectif en zone urbaine » devient la nouvelle frontière → sa
priorité monte. Le « programme scolaire » de l'équipe s'écrit ainsi de lui-même, toujours calé sur
ce qu'elle est mûre pour apprendre.

## Variantes & pièges

- **PAIRED / ACCEL** (conception non supervisée d'environnements) : un **générateur adverse**
  fabrique des missions *juste assez* dures (curriculum par « regret »).
- **Randomisation de domaine** : la version la plus simple (tout varier au hasard) — moins efficace,
  mais une bonne base.
- *Pièges :* mal mesurer le « potentiel » (on peut sur-rejouer des missions juste bruitées, pas
  réellement instructives) ; et oublier de garder un peu de missions faciles pour ne pas désapprendre.

## Pourquoi on l'utilise ici

C'est ce qui fait passer d'agents qui **mémorisent une carte** à des agents qui **généralisent** à
des missions variées — la condition pour qu'ils soient compétents *au combat*, et pas seulement sur
le terrain d'entraînement. Indispensable dès qu'on veut de la robustesse.

<div class="philo">En dernier regard. PLR redécouvre une vérité de toute pédagogie : on n'apprend que de ce qui résiste — mais pas trop. Vygotski l'appelait la « zone proximale de développement », cet étroit territoire entre l'ennui du déjà-su et le découragement de l'impossible, où se joue tout progrès réel. La machine y ajoute une élégance : c'est l'élève lui-même, par ses erreurs, qui désigne la prochaine leçon. Apprendre, ici, ce n'est pas subir un programme imposé, c'est revenir sans cesse là où le monde nous dément encore, et faire de cette résistance le moteur même de la croissance. Le bon maître, au fond, ne fait pas autre chose.</div>
