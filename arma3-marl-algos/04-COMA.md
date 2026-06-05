# COMA
### « Quel a été ton mérite, à toi, dans ce succès commun ? »

## Le problème qu'il résout

La récompense est commune : l'équipe gagne ou perd ensemble. Mais alors, **comment savoir qui a
contribué ?** Si l'on récompense tout le monde pareil après une victoire, le soldat resté à couvert
sans rien faire reçoit le même crédit que celui qui a pris le risque décisif. Pire : son signal
d'apprentissage lui dit « continue comme ça » — donc « reste planqué ». C'est le **fléau de
l'assignation de crédit**, et il étouffe l'apprentissage : le bon signal de chacun est noyé dans le
bruit des actions de tous.

## L'idée centrale

**Mesurer la contribution propre d'un agent en le comparant à lui-même.** On se demande : *« et si
ce soldat avait fait autre chose, les trois autres agissant exactement de la même façon — le
résultat aurait-il changé ? »* On isole ainsi ce que *son* geste, et lui seul, a apporté.

## Le mécanisme, pas à pas

1. Un **critique central** (qui voit tout, à l'entraînement) apprend à noter la situation pour
   *toutes* les combinaisons d'actions de l'équipe.
2. Pour évaluer l'agent *i*, on calcule la note réelle obtenue avec son action.
3. On calcule ensuite la note **moyenne** qu'on aurait eue s'il avait choisi *n'importe quelle
   autre* de ses actions — **en gardant les actions des autres figées**.
4. La différence entre les deux est son **avantage contrefactuel** : sa contribution nette.
5. On pousse sa politique dans le sens de cet avantage (à la manière d'un gradient de politique).

## Les formules, traduites

**① L'avantage contrefactuel.**

<div class="formule">mérite du soldat i = (note de ce qui s'est passé) − (note moyenne s'il avait agi autrement, les autres inchangés)</div>

> *Pour un littéraire :* on rejoue mentalement la scène en ne changeant **que** ce soldat. S'il
> obtient à peu près le même résultat quoi qu'il fasse, c'est qu'il n'a rien apporté de décisif. Si
> son geste précis a fait basculer l'issue, son mérite est réel — et chiffré.

**② Ce qu'on neutralise, et pourquoi.** En gardant les autres figés, on **soustrait** tout ce qui ne
dépendait pas de lui : la chance, l'action des coéquipiers, le contexte. Ce terme soustrait
s'appelle une *baseline* (un point de référence). Mathématiquement, le retirer **ne fausse pas** la
direction de l'apprentissage, mais **réduit énormément le bruit** — c'est là toute l'astuce.

> *En clair :* COMA calcule une **récompense de différence** — la différence que fait sa présence et
> son choix, et rien d'autre.

## Un exemple concret

L'équipe nettoie un bâtiment et réussit. Le médecin, lui, est resté en couverture à l'arrière.
Question contrefactuelle : s'il avait fait autre chose (avancer, tirer), le résultat aurait-il
changé ? Non — la pièce était déjà tenue. Son avantage est donc proche de zéro : pas de gros crédit,
mais pas de blâme non plus. En revanche, le voltigeur qui a neutralisé le défenseur d'angle : sans
son geste précis, l'assaut échouait. Avantage fortement positif → son comportement est renforcé.

## Variantes & pièges

- **Récompenses de différence** (Wolpert & Tumer, l'ancêtre conceptuel) : COMA en est la version
  neuronale apprise.
- **Lien avec la décomposition de valeur** (QMIX) : même but — démêler le crédit — mais côté
  *valeur* plutôt que côté *contrefactuel*.
- *Pièges :* le calcul exige un critique central précis ; et il suppose qu'on puisse énumérer les
  actions de l'agent (plus dur en actions continues).

## Pourquoi on l'utilise ici

Sans ce démêlage, le signal d'apprentissage d'équipe est inexploitable (« on a gagné, donc tout le
monde a bien joué », même le passif). COMA fait remonter le **vrai** mérite de chacun, ce qui
accélère l'apprentissage et **combat directement le « lazy agent »** (l'agent qui se planque) — un
risque qu'on a justement voulu éviter dans ton modèle.

<div class="philo">En dernier regard. COMA repose sur l'intuition morale la plus tenace : la responsabilité se mesure au contrefactuel. « Aurais-tu pu agir autrement, et cela aurait-il changé quelque chose ? » — c'est la question des juges, des philosophes du libre arbitre, et de chacun à l'heure des regrets. L'algorithme porte d'ailleurs en germe la leçon du film « La vie est belle » : la valeur d'une existence se révèle en imaginant le monde sans elle. Attribuer un mérite, ici, ce n'est pas flatter ni punir ; c'est reconnaître, froidement et justement, la différence qu'un être a réellement faite.</div>
