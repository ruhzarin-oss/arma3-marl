# GESTE N°3 — CERTIFICATION DES LIEUX. Protocole **redéposé entier**.

*10 août 2026, 15 h 30. **Le protocole du matin est déclaré cassé et remplacé.** Aucun lieu
n'était certifié sous lui ; rien n'est réinterprété.*

**Fiches relues ⟨règle 10⟩** : `courbe1-toucher-mesuree`, `etre-vu-tue-deux-fois-plus`,
`posture-couche-est-observation`, `arma-cover-envelope`, `arc-tir-sursis-mesure`,
`knowsabout-est-de-camp-pas-de-soldat`, `mesure-doit-savoir-echouer`.

## POURQUOI IL EST REDÉPOSÉ, ET NON AMENDÉ

Le protocole du matin déposait une tolérance : *les deux chemins doivent s'accorder sur au moins
80 % des pas*. La mesure a rendu ceci :

| lieu | vue moteur | mes rayons | accord |
|---|---|---|---|
| 2 | 94 % | 94 % | **100 %** |
| 7 | 76 % | 76 % | **100 %** |
| 8 | 86 % | 77 % | 91 % |
| 1 | 67 % | 62 % | 95 % |
| 3 | 32 % | 16 % | 84 % |
| 4 | 76 % | 60 % | 84 % |
| 5 | 63 % | 44 % | 81 % |
| 6 | 63 % | 50 % | **75 %** |

**L'accord vaut 100 % quand la vue est franche, et s'effondre quand elle est partielle.**

**L'analogie qui l'explique** : deux médecins lisent la même radio. L'un dit « tumeur / pas de
tumeur », l'autre dit « 30 % de chances ». Sur les cas francs ils s'accordent toujours ; sur les
cas ambigus ils divergent **forcément**, non parce que l'un se trompe, mais parce que l'un a le
droit de dire « à moitié » et l'autre non. Leur taux de désaccord ne mesure alors pas leur
compétence — **il mesure la difficulté des cas.**

Et c'en devient absurde : un terrain plein de demi-couvert est **précisément** ce que le geste
n°3 exige. Le contrôle recalait donc les terrains qui conviennent le mieux au geste.

**Mais la faute est plus profonde, et elle est dans mon application de la règle 11.** Elle
demande deux chemins indépendants vers **LA MÊME GRANDEUR**. Or les miens n'en mesuraient pas
une seule : `lineIntersectsSurfaces` demande *« y a-t-il un obstacle solide sur la ligne ? »*,
`checkVisibility` demande *« quelle part est visible ? »*. Ce n'étaient pas deux mesures d'une
chose, mais **une mesure de chacune de deux choses**.

**Aucune valeur de tolérance n'aurait sauvé cela.** Le contrôle était mal formé dès sa
conception — donc il ne s'amende pas, il se refait. ⟨règle 13 : *« quand ce n'est plus la
campagne qu'on amende, on déclare le protocole cassé et on le redépose entier »*⟩

## LE SECOND CHEMIN, REFAIT POUR MESURER LA MÊME GRANDEUR

La grandeur qui décide est : **quelle part de cet homme est exposée depuis le poste**.

- **Chemin 1 — le moteur.** `checkVisibility` d'œil à œil, entre deux hommes réels. C'est la vue
  que l'IA emploie pour décider si elle tire, donc **elle fait foi** ⟨règle 6⟩.
- **Chemin 2 — la silhouette.** **Cinq rayons** vers cinq points du corps : tête, poitrine, deux
  épaules, genoux. On compte la **fraction** qui passe. Il rend désormais une fraction, comme le
  moteur, et mesure la même chose.

> **TOLÉRANCE DÉPOSÉE : les deux fractions ne doivent pas différer de plus de 0,35 en moyenne
> absolue sur la traversée.** Au-delà : instrument en panne, on cherche la cause.

**Justification, dérivée du mécanisme et non des lieux** : cinq rayons discrétisent en pas de
0,2 ; le moteur rend un continu qui intègre en outre le feuillage. Un écart moyen d'un tiers est
ce que cette différence de résolution peut produire ; au-delà, les deux ne regardent plus le même
monde.

## LE SONDAGE COMPORTEMENTAL — contre l'aveuglité commune

⚠️ **Les deux chemins ci-dessus restent GÉOMÉTRIQUES**, donc aveugles ensemble à ce que le moteur
ajoute — le feuillage traversé à moitié. Une tolérance ne détecte **jamais** deux chemins qui se
trompent ensemble ; c'est écrit ici pour qu'on ne l'oublie pas.

D'où un **troisième chemin, en sondage** : sur **cinq pas tirés au hasard** par traversée, on
pose un vrai défenseur armé au poste et un vrai marcheur sur le pas, on laisse l'IA agir **six
secondes**, et on lit ce que le camp sait de lui.

**Sa limite, nommée d'avance** ⟨fiche `knowsabout-est-de-camp-pas-de-soldat`⟩ : `knowsAbout` est
**de camp, pas de soldat** — il voit à 300 m devant et reste aveugle à 50 m de flanc. Ce sondage
mesure donc ce que le **camp** sait, pas ce que ce défenseur voit. Il ne certifie rien : il sert
uniquement à attraper le cas où les deux chemins géométriques se tromperaient de concert.

> **Le sondage ne décide d'aucun lieu.** Il est journalisé, et s'il contredit massivement les
> deux autres — un camp qui ne sait rien là où la géométrie voit tout — on s'arrête et on
> cherche, au lieu de certifier.

## LA CERTIFICATION

Seuils **inchangés depuis le premier dépôt**, aucun assoupli, aucun resserré :

- ≥ **70 %** de pas servis en couvert (boîte englobante : > 2 m × 2 m × 0,5 m)
- ≥ **60 %** de pas vus depuis le poste, **lus sur le chemin du moteur**
- **aucun trou** de plus de 2 pas consécutifs sans couvert
- le lieu doit être **stable** : deux lectures consécutives identiques
- et les deux chemins doivent s'accorder à la tolérance ci-dessus

**Il faut ≥ 5 lieux certifiés** pour instruire le geste — 3 instruits, 2 tenus à l'écart.

## CE QUI FERAIT ÉCHOUER LA CERTIFICATION — écrit avant

- **Un lieu où les deux fractions diffèrent de plus de 0,35** → instrument en panne sur ce lieu,
  on cherche la cause, on ne réconcilie pas.
- **Le sondage contredit massivement la géométrie** → on s'arrête, quel que soit le reste.
- **Moins de 5 lieux certifiés** → on le dit, le banc tourne sur ce qu'on a, on ne compense pas.
- **Les contrôles tombent** — bâti dense mal servi, pleine mer non nulle → c'est le compteur qui
  est cassé, pas le terrain, et on ne lit rien d'autre ce jour-là.

**Le registre des amendements de cette campagne repart à zéro** : ce protocole est neuf.
