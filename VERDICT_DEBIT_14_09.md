# Débit du monde en boîtes — mesuré, et ce qu'on a trouvé en route
**14 septembre 2026.** Critères écrits avant : `CRITERES_DEBIT_14_09.md`.
Banc : `p2/banc_debit.py`, écrit le 15/08, **jamais lancé jusqu'ici**.

## LA MESURE DEMANDÉE
4096 environnements × 3 agents = 12 288 rayons, RTX 3090.
Contrôle de justesse passé **avant** tout chronomètre : les 5 segments de référence
répondent comme Unreal, jeu mixte (2 non, 3 oui).

| monde | ms/pas | rapport au champ de hauteur | débit |
|---|---|---|---|
| champ de hauteur (l'existant) | **0,80** | — | — |
| boîtes, 185 (un bâtiment) | **8,72** | **×10,9** | 0,3 G rayons-boîtes/s |
| boîtes, 1 000 | **20,35** | ×25,4 | 0,6 G/s |
| boîtes, 5 000 | **121,13** | ×151 | 0,5 G/s |

**Verdict selon le critère écrit d'avance : > ×10 ⇒ ce n'est pas un échange.**
Même un seul bâtiment coûte onze fois la 2,5D. Et c'est un **plancher** : un rayon par agent.
À 12 rayons par agent (la coque du projet), multiplier par ~12.

**Le levier est la proximité, et il est linéaire.** De 1 000 à 5 000 boîtes, le temps est
multiplié par 5,9 pour 5× le travail : le coût suit le nombre de boîtes testées. Ne tester que
les boîtes proches (~30 par environnement) ramènerait le surcoût au niveau du champ de hauteur.
C'est un filtre à écrire, pas une structure d'accélération à inventer.
Le noyau est par ailleurs lent pour la carte (0,5 G/s) : il enchaîne des dizaines de petits
noyaux élémentaires au lieu d'un seul fusionné.

## ⛔ CE QUE LA MESURE DU DÉNOMINATEUR A RÉVÉLÉ
Je voulais rapporter ce coût à un **pas** du gymnase. Deux choses sont tombées.

**1. Le « 3,28 s/pas » n'est pas un temps de calcul** — c'est la conversion en temps de jeu.
Il ne pouvait pas servir de dénominateur.

**2. LE GYMNASE NE TOURNAIT PLUS DU TOUT.** `assault_terrain.py:934` :
`torch.zeros_like(active).scatter_(1, _k, 1.0)` — `active` est le **défenseur** (largeur 1),
pas l'attaquant. Le one-hot visait donc une colonne unique avec un indice d'attaquant, et le
monde mourait dès qu'un défenseur choisissait une cible d'indice ≥ 1, c'est-à-dire presque
toujours (au 2ᵉ pas dans le cas témoin). La ligne date du **4 août** (`a405a3a`) et
`cible_unique=True` est le défaut. Même `scripted_compare.py` non modifié plante.
> ⭐ Personne ne s'en est aperçu pendant six semaines parce que tout le travail était passé
> côté Arma. Un outil qu'on n'exerce plus ne signale pas sa panne.

**Réparé** : le one-hot prend la forme de `_elig`, qui est bien (N, attaquants).

## ÉTAT DES CONTRÔLES — deux sur trois ne passent pas, et je ne les habille pas
- ✅ **Forme** : 60 pas sur CPU sans erreur (le plantage tombait au pas 2).
- ✅ **Sémantique de la branche** : à 2 défenseurs contre 4 attaquants sur terrain plat,
  **au plus 2 attaquants touchés par pas, exactement un par défenseur**, tir dans 100 % des
  environnements. C'est ce que « un défenseur tire sur un homme » veut dire.
- ⛔ **Comparaison prévue, inutilisable** : le bras `cible_unique=False` ne touche
  **personne** (0,000 attaquant, 0 % des environnements). Le bras de référence est inerte dans
  cette configuration — **anomalie ouverte**, à chasser séparément.
- ⛔ **Le pas chronométré TOMBE sur son propre falsificateur** : 70,75 ms à 4096 environnements
  contre 75,67 ms à 1024 — le temps **ne dépend pas de la taille**. Le pas est donc borné par
  le lancement des noyaux, pas par le calcul. Je n'utilise pas ce nombre comme dénominateur, et
  le « ~300 000 pas/s » d'une note du projet n'est pas retrouvé (ici ~58 000 pas-env/s).

## AUTRES DÉFAUTS RENCONTRÉS
- `scripted_compare.py` lit `info["reached"]`, champ qui n'existe plus (c'est `took`).
- Le bâtiment de référence a changé depuis l'accord 5/5 avec Unreal : empreinte
  `8ff46b06…` aujourd'hui contre `efecae3b…` au 15/08. Le contrôle de justesse compare donc
  à des réponses d'Unreal obtenues sur une **autre version du bâtiment**. Il passe, mais cet
  accord doit être rejoué avant d'être invoqué.

## CE QUI RESTE
Filtrer les boîtes par proximité, puis remesurer — c'est la seule chose qui décide si le monde
3D entre dans le gymnase. La létalité sur ce monde-là (courbe de toucher, suppression) n'est
toujours pas accordée.
