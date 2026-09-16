# Critères pré-enregistrés — chercheur de causes CHACAL, v1

*16/09/2026. Amendement de `CRITERES_CHERCHEUR_CAUSES_V0.md` (commit 6bedbad). Écrit et commité AVANT la recherche v1.*

## Pourquoi un v1

Le v0 a été lancé et **n'est pas cru** : C−2 échoue (les 5 placebos ont 19 à 32 « découvertes » intermédiaires)
et C+4 échoue. Diagnostic mesuré avant d'écrire ce texte :

1. **Faute de calcul.** Les découvertes du placebo 0 sont des variables **constantes dans chaque strate** (géométrie
   du monde `ok|distances|…`, `ok|enceinte|…`, ou événements présents dans toute une strate). Le levier ne peut pas
   les bouger ; la statistique permutée est constante ; son écart-type vaut le bruit d'arrondi, et le z (jusqu'à
   19) sort de ce bruit. Avec 20 000 permutations réelles, leur p vaut 1,0.
2. **Faute de pré-enregistrement.** C+4 portait sur l'effet du délai du porteur sur les charges. Or ce verdict est
   **AMENDE** : l'effet sur l'issue n'est pas démontré (p passé de 0,031 à 0,219). Ce qui est établi, c'est le
   **mécanisme** : porteurs arrivés 90,1 % à 45 s contre 95,0 % à 180 s, sur 838 porteurs. Un contrôle positif ne
   se choisit que sur un verdict établi.

**Ce qui a été vu du v0** : la liste des découvertes de la famille E, les pistes, les contrôles ; pour le délai du
porteur, seulement les lignes `fini|charges` et `fini_issue=SUCCES`. Les lignes de la famille M du délai du porteur
n'ont **pas** été lues.

## Ce qui change

1. Une variable n'est testée que si elle **varie à l'intérieur des strates** de la comparaison : écart-type
   intra-strate > 1e−9 × (1 + |moyenne|).
2. **p empirique** : (1 + nombre de permutations dont |T − moyenne permutée| ≥ |T observé − moyenne permutée|) / (P + 1),
   avec **P = 20 000** permutations dans les strates. Plus d'approximation normale.
3. Même garde de variance intra-strate pour les pistes.
4. Les raisons sont rangées en deux listes : **décomposition** (corrélation intra-strate ≥ 0,8 avec l'effet sur tous
   les épisodes : l'effet redit autrement, par exemple « moins de charges manquées ») et **raisons** (en dessous).
   Au-delà de 0,95, c'est toujours une tautologie, écartée.

Tout le reste du v0 est inchangé : données, strates, familles E et M, BH à 5 %, placebos, seuil de confiance.

## Contrôles

| contrôle | v1 |
|---|---|
| C+1, C+2, C+3, C−1, C−2 | **inchangés** (C+3 : top 5 de la liste « raisons ») |
| **C+4 remplacé par C+4′** | lecture non entrelacée, `delai_porteur` 45 → 180 : en famille M, la variable `n|e|charge_manquee|cause=PORTEUR_N_ARRIVE_PAS` est découverte et **diminue** |
| C+4 d'origine | rapporté à titre **informatif** seulement |

**Le chercheur v1 est cru si tous les contrôles testables passent, avec au moins 3 contrôles positifs testables.**
S'il échoue encore, il n'y aura pas de v2 le même jour : on écrit ce qui échoue.
