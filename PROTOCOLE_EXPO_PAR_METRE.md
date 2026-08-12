# REFAIRE L'EXPOSITION PAR MÈTRE GAGNÉ — protocole déposé avant lecture

*11 août 2026. Premier des six sursitaires repris.*

## POURQUOI CELUI-LÀ D'ABORD, ET CE QUI EST RÉELLEMENT EN SURSIS

Trois des six sursitaires sont bâtis sur cette grandeur. Et en relisant la fiche, **la mesure
d'origine n'était pas née en sandbox** : 36 parties Arma à Pyrgos, conditions vérifiées, plein
jour. Ce n'est donc pas le LIEU de la mesure qui est en cause.

**Ce qui est en sursis, c'est le NUMÉRATEUR.** La grandeur était bâtie sur `expo`, mesurée depuis
à **AUC 0,5005** — le hasard. On ne refait donc pas la même mesure ailleurs : **on la refait avec
un numérateur qui informe.** Le registre le nomme : la **SUPPRESSION SUBIE** porte **92 %** de
l'écart entre le modèle qui prédit (0,6549) et `expo` qui ne prédit rien.

## LA GRANDEUR, REDÉFINIE

> **Coût = suppression subie par mètre gagné.**
>
> **Suppression subie** d'un attaquant = le nombre d'échantillons `HMT|G|VISE` où **un défenseur
> l'a désigné**, × 2 s. Le témoin d'intention échantillonne toutes les 2 secondes, que le
> défenseur tire ou non — donc il compte aussi les accrochages où personne ne tire, qui sont
> justement ceux où le sursis a joué à fond.
>
> **Mètres gagnés** = distance de départ moins distance minimale atteinte.

⚠️ **Ce n'est pas la même grandeur que celle de juillet**, et on ne prétend pas le contraire.
C'est la même IDÉE — *combien coûte chaque mètre* — avec la seule quantité dont on ait mesuré
qu'elle informe.

## LE CORPUS

Les accrochages du banc de mission n°2, **dans le monde calibré du 10/08** — 13 défenseurs,
taux de prise 65 %, aiguille dans la bande. Aucune intervention : **lecture pure d'un journal
déjà écrit.** Le monde n'est pas touché, le banc continue.

## LA LECTURE ⟨règle 14⟩

Cet acquis décide si un sursitaire revient au registre : **cher et asymétrique → la borne.**

> **L'acquis est rétabli si la borne inférieure de l'intervalle à 95 % du rapport
> `coût(non pris) / coût(pris)` dépasse 1.**

⚠️ **Aucun seuil chiffré n'est repris de juillet.** Le 1,86 d'origine (1,21 contre 0,65) était
mesuré avec l'autre numérateur. ⟨Fable, 11/08 : *« ce qui se transporte, c'est le SIGNE et
l'ordre, jamais le chiffre »*⟩ La nouvelle valeur sera **rapportée, pas comparée**.

## LES CONTRÔLES — lus AVANT la grandeur

- **POSITIF — une séparation connue doit sortir** : les accrochages non pris doivent montrer
  **plus de pertes** que les pris. Si le dépouilleur ne trouve pas ça, il ne lit pas le journal.
- **NUL — une étiquette permutée ne doit rien séparer** : on retire au hasard l'étiquette
  pris/non-pris 1000 fois ; le rapport observé doit sortir de la distribution permutée. Sinon
  ce qu'on voit est du bruit d'échantillonnage.
- **TAILLE** : au moins **30 accrochages par bras**. En deçà : insuffisant, jamais « pas d'effet ».
- **DÉNOMINATEUR NON NUL** : un accrochage qui n'a gagné aucun mètre a un coût infini. Ils sont
  **comptés et nommés**, jamais silencieusement exclus.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **La borne n'atteint pas 1** → l'acquis **ne revient pas**, et il reste au registre des
  sursitaires. On le dit.
- **Le contrôle positif tombe** → mon lecteur est cassé, on ne lit rien d'autre ce jour-là.
- **Le contrôle nul passe** (la permutation reproduit l'effet) → ce n'est pas la grandeur qui
  sépare, c'est le hasard.
- **Le rapport tient mais seulement sur une poignée d'accrochages à zéro mètre** → l'effet est
  un artefact de dénominateur, et on le dira.

---

## ⛔ LA PREMIÈRE LECTURE EST NULLE — 11/08, 11 h

Le dépouillement a rendu « acquis rétabli » : rapport 2,17, borne inférieure 1,49, permutation
p = 0,0010, trois contrôles sur trois passés. **Cette lecture ne vaut rien**, et voici pourquoi.

**Le dénominateur n'était pas ce que le protocole disait.** J'avais écrit « mètres gagnés =
distance de départ moins distance minimale atteinte », et j'ai lu le champ `_dmin` du journal.
Lu sur pièces dans le générateur, `_dmin` est **la distance minimale entre un attaquant et un
défenseur VIVANT** — et la boucle qui la met à jour ne parcourt que les vivants. Quand les
défenseurs sont éliminés, elle ne s'exécute plus et la valeur **reste à son initialisation** :
d'où 3935 m sur une prise réussie, et 214 accrochages sur 359 déclarés « à gain nul » dont
**168 avaient pris l'objectif**.

⚠️ **Aucun de mes quatre contrôles ne pouvait attraper ça.** Ils vérifiaient la taille, une
séparation connue, le témoin d'intention, et ils comptaient les gains nuls — mais **aucun ne
demandait si le champ mesurait la chose qu'il nomme**. C'est la règle 6 retournée contre moi
pour la troisième fois de la campagne : j'ai vérifié l'abstraction commode au lieu de la
propriété que le mécanisme emploie.

**Ce qui manque au journal** : la distance à l'objectif au fil du temps. Elle n'y est pas, et
aucune combinaison des champs existants ne la reconstitue. `ARR` donne un franchissement binaire
par axe, pas des mètres.

> **CONSÉQUENCE : l'acquis NE REVIENT PAS aujourd'hui.** Il reste au registre des sursitaires.
> La grandeur déposée exige un banc dédié qui journalise la position au fil du temps ; ce banc
> se dépose et se lance à part, sans toucher la campagne du n°2 qui tourne.

**Ce qui est acquis quand même, et qui n'est pas rien** : le témoin d'intention `VISE` rend
**31 778 échantillons de désignation** sur 359 accrochages. La **suppression subie est
mesurable** sur ce banc. C'est le numérateur qui manquait depuis juillet — il est là. C'est le
dénominateur qui manque maintenant.
