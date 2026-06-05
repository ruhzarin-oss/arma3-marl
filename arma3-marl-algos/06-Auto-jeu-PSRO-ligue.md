# Auto-jeu & PSRO / ligue
### « Se forger contre un adversaire qui apprend aussi »

## Le problème qu'il résout

Une équipe entraînée contre un ennemi **scripté** (figé) devient experte… à battre cet ennemi-là.
Face à un adversaire intelligent et imprévu, elle s'effondre : elle a appris des recettes contre un
mannequin, pas l'art du combat. On dit qu'elle **sur-apprend** son adversaire. Il faut un opposant
qui **progresse**, pour forcer l'équipe à progresser elle aussi.

## L'idée centrale

**Faire apprendre les deux camps l'un contre l'autre** — une course aux armements qui les hisse tous
les deux. Mais avec une discipline : s'entraîner *seulement* contre sa version du moment fait
**tourner en rond** (on oublie comment battre les anciennes tactiques) et peut même **cycler** sans
fin (pierre-feuille-ciseaux). La théorie des jeux fournit la discipline qui évite ces pièges.

## Le mécanisme, pas à pas (du naïf au robuste)

1. **Auto-jeu naïf** : l'équipe s'entraîne contre une copie d'elle-même, mise à jour en continu.
   Simple, mais oublie et cycle.
2. **Jeu fictif** : l'équipe s'entraîne contre un **mélange de toutes ses versions passées** — elle
   reste bonne contre l'ancien comme contre le nouveau.
3. **PSRO** (la version disciplinée) :
   - on garde une **population** d'équipes (et d'adversaires) ;
   - on dresse la table « qui bat qui » en les faisant s'affronter ;
   - un **méta-solveur** (théorie des jeux : équilibre de Nash) calcule la **bonne dose** de chaque
     adversaire à affronter ;
   - on entraîne une **meilleure réponse** à ce mélange, qu'on **ajoute** à la population ;
   - on répète. La population s'enrichit de styles de plus en plus variés.
4. **Ligue** (façon AlphaStar) : on ajoute des agents aux rôles spécialisés — des « exploiteurs »
   dont **le seul but est de trouver les failles** de l'équipe principale, qui doit apprendre à les
   colmater (mécanisme dit *PFSP* : on affronte en priorité ceux qui nous mettent en difficulté).

## Les formules, traduites

**① La meilleure réponse.**

<div class="formule">nouvelle équipe = la meilleure réponse possible au mélange d'adversaires du moment</div>

> *Pour un littéraire :* à chaque tour, on fabrique le meilleur « contre » à ce que joue l'autre camp.

**② Le jeu fictif (pour ne pas oublier).**

<div class="formule">adversaire d'entraînement = un MÉLANGE des versions passées, pas seulement la dernière</div>

> *Pourquoi :* s'entraîner contre le seul présent fait perdre les parades du passé — et l'ennemi
> pourrait ressortir une vieille ruse. Le mélange immunise contre l'oubli.

**③ La dose d'adversaires (méta-jeu).**

<div class="formule">on choisit COMBIEN affronter chaque style, selon la table « qui bat qui » (équilibre de Nash)</div>

> *En clair :* un tournoi permanent, où l'on choisit ses sparring-partners non au hasard, mais pour
> qu'ils corrigent précisément nos faiblesses du moment.

## Un exemple concret

Ton équipe bleue apprend à déborder par la droite. L'équipe rouge, qui apprend aussi, finit par
**anticiper** ce débordement et poster un guetteur à droite. Bleu doit alors inventer la feinte (menacer
à droite, frapper à gauche). Rouge réplique en gardant des réserves… À chaque tour, le niveau monte.
La ligue ajoute un « exploiteur » qui ne fait *que* chercher la faille du moment (« bleu néglige ses
arrières ») : bleu est forcé de la corriger, et devient robuste là où il était fragile.

## Variantes & pièges

- **NFSP, α-PSRO, JPSRO** : variantes selon le concept de solution (Nash, α-Rank, équilibres
  corrélés).
- *Pièges :* le **cyclage** (A bat B bat C bat A) si l'on ne garde pas l'historique ; l'**explosion**
  de la population (coûteux) ; et le piège du miroir — s'entraîner seulement contre soi peut produire
  une virtuosité qui tourne à vide, d'où la nécessité de la **diversité** (ligue, exploiteurs).

## Pourquoi on l'utilise ici

C'est **le** saut qualitatif vers des agents de combat **crédibles** : robustes face à des styles
variés, et non sur-spécialisés contre un seul comportement scripté. On y vient *après* qu'une équipe
sache déjà se battre contre un ennemi simple.

<div class="philo">En dernier regard. Il y a là une loi profonde de la formation de soi : on ne se forge que contre une résistance. Hegel en fit une dialectique — la conscience ne se révèle qu'au contact de ce qui lui résiste ; Nietzsche, une éthique de l'épreuve ; le judoka, un principe d'entraînement. Mais la méthode garde aussi un avertissement : s'affronter seulement soi-même mène au solipsisme, à une habileté tournant à vide. D'où la ligue, qui réintroduit l'altérité — des adversaires assez divers pour nous surprendre. On ne grandit ni dans le miroir seul, ni sans miroir ; on grandit face à d'autres, et c'est leur différence qui nous révèle nos angles morts.</div>
