# Dépôt — les BASELINES LIVE, critères AVANT mesure

Déposé le 15/08/2026, sur le premier geste demandé par Fable après le recadrage de Younes :
**l'objectif est un agent qui joue, pas un dossier.**

> *« Aujourd'hui 11,9 % n'a pas de sens : si le meilleur corps connu prend l'objectif 25 %
> sur ce banc, ton agent est à mi-chemin, pas à terre. »*

## QUELLE DÉCISION CETTE MESURE FAIT-ELLE BASCULER ⟨nouveau garde-fou⟩

**Si l'IA native d'Arma prend l'objectif nettement plus souvent que 11,9 %** → le banc est
gagnable, l'agent est mauvais, et l'effort va sur **l'agent** (remonter la couture aux
intentions, retyper le couvert).

**Si elle fait aussi mal ou pire** → le banc est très dur pour tout le monde, les 11,9 %
ne condamnent pas l'agent, et l'effort va sur **la mission** (objectif, effectifs, durée).

Aucune autre mesure ne fait basculer cette décision, et elle coûte 90 minutes.

## Les trois bras, même banc, même site, 4 contre 4, 20 épisodes chacun

- **NATIF** — l'IA d'Arma joue seule. Aucun `disableAI`, un point de passage vers
  l'objectif, `COMBAT`/`RED`. C'est le **meilleur corps connu** sur ce banc.
- **FLANC** — la doctrine écrite à la main, portée telle quelle depuis `boucle.py`
  (`2 fixes qui appuient à moins de 0,9 × portée, les autres crochètent 14 pas`), pilotée
  par **le même corps réparé** que la politique. Comparaison à cerveau différent, corps
  identique.
- **POLITIQUE** — déjà mesurée : **8/67 = 11,9 %**, IC [4,2 ; 19,7]. Non rejouée.

## Ce qui se lit

La prise, par le critère déjà codé (`dmin < 25` **et** `vivants > 0`). Les trois bras
s'ordonnent, ou ne s'ordonnent pas.

## CONTRÔLES POSITIFS ⟨règle 16⟩

1. **Chaque scène confirmée par le JEU** : `def=4 att=4`.
2. **Le bras NATIF doit BOUGER** : déplacement médian par pas > 1 m. Un bras natif immobile
   ne mesure pas l'IA d'Arma, il mesure un point de passage qui n'est pas pris.
3. **Le bras FLANC doit produire au moins 3 actions distinctes** — sinon la doctrine n'est
   pas exécutée et le bras ne juge rien.

## Ce qui ferait échouer

- moins de 15 épisodes valides sur 20 dans un bras ;
- contrôle 2 ou 3 en défaut → ce bras ne se lit pas.

## Ce qui n'est PAS promis

Ces baselines ne réparent rien. Elles disent seulement **où l'agent se situe**, et donc sur
quoi travailler. Si les trois bras rendent tous 10 à 15 %, la réponse est que **le banc est
la mauvaise mission**, et c'est un résultat.
