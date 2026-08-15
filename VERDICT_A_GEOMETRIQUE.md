# VERDICT — A EST RETENUE, et cette fois sur la carte seule

Mesuré le 15/08/2026. Critères déposés avant dans `DEPOT_A_GEOMETRIQUE.md` (`ab542c3`).
Portes exécutées avant les données ⟨règle 18⟩ : chaque bande s'est montrée atteignable et
rejetable.

## Le contrôle positif passe des deux côtés

L'échantillonnage **carte seule** doit retrouver, à un facteur 2 près, le `dcover` que les
agents ont réellement traversé :

| | carte seule | vécu par les agents | facteur |
|---|---|---|---|
| GYMNASE | 0,042 | 0,041 | **1,02** |
| ARMA | 0,097 | 0,123 | **0,79** |

Le couloir échantillonné **est** celui qui est parcouru.

## Le résultat

| | n | 1 % | **médiane** | 99 % |
|---|---|---|---|---|
| **GYMNASE** | 12 288 | 0,000 | **0,033** | 0,132 |
| **ARMA** | 192 | 0,000 | **0,100** | 0,333 |

**Rapport = 3,00. A EST RETENUE.**

Le couvert est **trois fois plus loin** sur le couloir d'approche d'Arma que sur celui du
gymnase — une cellule contre trois. **Aucun agent n'intervient dans cette mesure.**

## Ce que la reprise de Fable a corrigé

Ma première lecture d'A — 44,8 % contre 11,6 % de « temps passé près du couvert » —
**mélangeait la carte et la politique**. Un agent qui cherche bien le couvert gonfle ce
temps là où il en trouve. Elle ne mesurait pas la disponibilité et **A n'était pas établie**.
Elle l'est maintenant, sur une grandeur où aucune politique n'intervient.

## Ce n'est pas un artefact de mon choix de site

`DEPOT_CHOIX_SITE.md` (14/08) déclarait **d'avance** : *« dcover restera décalé — au seuil
en service, Stratis au hasard rend 0,100 de médiane quand le gymnase veut 0,035. Changer
le site ne le corrigera pas. »*

Le couloir du site retenu rend exactement **0,100**. C'est donc une propriété de **Stratis
contre le terrain généré du gymnase**, pas du terrain que j'ai choisi.

## Ce que ça donne avec le verdict précédent

Les deux tiennent ensemble, et ils ne disent pas la même chose :

- **A (carte)** : sur Arma, le couvert est **trois fois plus loin**. Établi proprement.
- **CHOISIE (comportement)** : quand le couvert **est** à une cellule, l'agent s'expose
  quand même 73 % du temps contre 23 %. Établi selon son critère, **mais confondu** — la
  comparaison ne fige pas les onze autres colonnes.

**L'agent a moins de couvert disponible ET emploie moins celui qui est là.**

## Réserve de taille

192 points côté Arma contre 12 288 côté gymnase. La médiane d'Arma repose sur un seul site
et 24 rayons. Le rapport de 3,00 est net, mais sa précision est asymétrique — et je ne cite
pas « exactement trois fois » comme une constante.

## Ce que ça ne dit pas

Pourquoi l'agent s'expose 73 % du temps quand un abri est à une cellule. A explique la
rareté, pas le non-emploi.
