# La LOI-PRÉDICTEUR — décisions de conception, déposées avant le code

*6 août 2026, 18h20. Rien n'est codé. Le verdict des trois bras n'est pas lu.*

## Ce qui change, en une phrase

La mort dans la sandbox cessera d'être une **chaîne composée à la main** — courbe de toucher ×
cadence × dégât par impact × détection — pour devenir **la sortie du prédicteur appris sur
563 383 observations réelles d'Arma**.

> La question de Younes, le 06/08 : *« tu ne devais pas découvrir ça en faisant un réseau de
> neurones sur la matrice Arma ? »*

Le prédicteur **est** la mortalité d'Arma. Il porte déjà ce que la chaîne n'avait pas : le
couvert, la durée d'engagement, le nombre de tireurs, la résolution des accrochages — et la
**pente montante avec la distance**, celle que la chaîne obtenait à l'envers.

**Classe d'erreur enterrée : le maillon recomposé.** Reconstruire à la main un objet déjà
appris du monde réel. Deuxième fois qu'elle coûte des nuits ; la première s'appelait `expo`.

> **Règle : avant de composer une loi depuis des mesures, vérifier qu'aucun artefact appris
> ne la porte déjà.**

## Décision 1 — l'horizon : taux constant, assumé et daté

Le prédicteur rend `p(mort dans les 30 s)`. Un pas vaut **3,28 s** (conversion mesurée), donc
**9,1 pas** par fenêtre.

```
p_pas = 1 − (1 − p30)^(1/9,1)
```

**C'est un maillon assumé**, et il s'écrit comme tel. Sa défense : c'est l'hypothèse qui
**invente le moins** — elle n'ajoute aucun paramètre, elle dit seulement « je ne sais rien de
la répartition à l'intérieur des 30 secondes ». Toute forme prétendument moins inventée
exigerait d'inventer davantage : une répartition qu'on ne possède pas.

Et sa nature la borne : la transformation est **monotone**. Elle peut fausser l'amplitude,
**jamais le sens** — la pente vient du corpus et y reste.

**Sa cage** : le banc v3 journalisera le **délai avant la mort**, pas seulement la mortalité à
30 s. Si l'hypothèse du taux constant est mauvaise, c'est v3 qui le dira. Chiffre rapporté,
pas porte.

## Décision 2 — la survie en ESPÉRANCE pour entraîner, les DÉS pour juger

**À l'entraînement**, la mort ne se tire pas au sort : elle **pondère**. L'agent porte une
flamme ; chaque pas risqué en mange une part ; sa récompense finale pèse ce qui reste.

⟨mon inclination allait au tirage. Elle était fausse pour deux raisons. Traverser un état à
50 % de mort **divise par deux l'espérance d'arriver** : l'agent paie le plein tarif, à chaque
passage — aucune moyenne ne triche. Et le tirage aurait changé **le monde ET l'estimateur**
dans la même nuit : si ça échoue, aucun verdict n'a de cause.⟩

**Au jugement**, la mort se **tire au sort**. PORTE 0 et tous les bancs évaluent en monde
stochastique.

> **On entraîne sur la flamme, on certifie aux dés.** Et l'écart entre les deux devient
> lui-même un chiffre rapporté à chaque verdict.

## Décision 3 — plus de terme de risque dans la récompense

Le terme de risque était **un échafaudage pour un monde sans mort** : on payait le risque en
monnaie parce que rien ne le faisait payer en conséquence. Avec la mort installée, le garder
serait **compter deux fois**.

> **Récompense = arriver. La mort est un événement, pas un prix.**

Et le suspect n°1 déposé ce matin — « la récompense paie le pic, mauvaise monnaie » —
**disparaît sans débat** : il n'y a plus de monnaie du tout. La question « pic ou survie »
était un artefact de l'échafaudage.

## Le danger, nommé d'avance

**Un agent entraîné contre une loi apprise cherchera les trous de la loi.** Il trouvera les
états où le réseau se trompe vers le bas et y logera sa trajectoire. C'est le mécanisme exact
qui a fait échouer le MPC d'AQUILON contre son modèle de monde.

On ne peut pas l'empêcher en sandbox. On peut le mesurer :

> **L'écart entre réussite sandbox et réussite Arma EST la mesure de l'erreur exploitable du
> prédicteur.** Arma reste juge précisément pour ça.

**Écrit d'avance : si l'étage 1 passe en sandbox et échoue sur Arma, suspect n°1 =
exploitation du modèle.**

## Décision 4 — l'empreinte du monde au démarrage

Ma faute du 06/08 : j'ai édité le monde pendant que trois bras tournaient. Reverté à temps,
vérifié par MD5 (`39f4588a…` des deux côtés), zéro dégât — mais **rien ne l'empêchait**.

> Tout run long **imprime au démarrage l'empreinte du fichier de monde qu'il a chargé**, et
> **le juge REFUSE de comparer des bras aux empreintes différentes.**

Détection, pas prévention : la faute devient impossible à **rater**, à défaut d'être
impossible à commettre. Le verrou d'interdiction de démarrage est écarté — machinerie à états,
verrous morts-vivants, chantier sur incident.

## Ce qui reste de la chaîne faite main

La chaîne meurt. Mais ses instruments vivent : la méthodologie de comparaison des pouls, le
critère de forme à 2,5, la conception du v3 par injection. Ils changent de rôle sans changer
d'une ligne — ils ne jugent plus une chaîne, ils jugent **le prédicteur-comme-loi**.

⟨l'après-midi du 06/08 n'a pas produit une loi ; il a produit **le tribunal de la loi**.⟩

Et les constantes mesurées restent mesurées : la courbe de toucher n'a pas démérité, elle
servira ailleurs.
