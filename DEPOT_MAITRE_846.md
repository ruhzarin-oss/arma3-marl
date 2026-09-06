# LE PROFESSEUR À 84,6 % — dépôt du 26/08/2026

## LE FAIT
`shamal_action` **sans bounding** rend **84,6 %** de prise sur les 6 graines jamais vues,
étendue [79,3 ; 89,1], contre **49,6 %** pour la référence `A` du dépôt et **48,0 %** pour
SHAMAL complet. Doctrine **scriptée** : aucun apprentissage, aucun paramètre.

| configuration | prise | étendue | tenus | danger/h-pas | survivants |
|---|---|---|---|---|---|
| bounding T · flank T (SHAMAL complet) | 48,0 % | [43,8 ; 50,8] | 120,8 m | 0,0919 | 1,34 |
| bounding T · flank F | 57,9 % | [49,6 ; 64,1] | 130,3 m | 0,1137 | 1,71 |
| **bounding F · flank T** | **84,6 %** | [79,3 ; 89,1] | 136,2 m | 0,0785 | **2,68** |
| **bounding F · flank F** | **84,6 %** | [82,4 ; 86,7] | 139,9 m | 0,0890 | **2,76** |

## LES QUATRE CONTRÔLES, PASSÉS AVANT PUBLICATION
1. **Même monde** — A=4, D=4, `fire_range` 110, `secure_r` 25, `max_steps` 60, courbe active :
   MONDE_ARMA, celui de tous les autres chiffres du dossier. Lu sur l'objet construit.
2. **Stable** — six graines, étendue 9,8 points, aucune graine chanceuse.
3. **Il gagne EN COMBATTANT** — deux fois plus de survivants (2,68 contre 1,34), moins de
   danger par homme-pas, 15 mètres de plus. Ce n'est pas un mode dégénéré.
4. **Le « plafond du gymnase » est RÉFUTÉ.** Il avait été supposé vers 61-62 % parce que la
   greffe (61,6) et E2 (61,7) y atterrissaient. Deux coïncidences ne font pas une mesure.

## ⭐ LE GESTE N°1 DU CAHIER NUIT — ET LA RÈGLE DU CAHIER L'A ATTRAPÉ
Le bond par binôme coûte **−36,6 points**. Son fait certifié était *« bounding overwatch perce
96 % / 91 % face à **12 gardes** »* ; ici il y a **quatre** défenseurs. Geler la moitié de
l'escouade pour clouer quatre hommes est un mauvais marché — **le fait ne transfère pas d'une
densité de défense à une autre**.

C'est exactement ce que la règle du cahier existe pour faire : *« un geste dont le professeur
ne bat pas son témoin ne s'enseigne pas »*. Il ne le bat pas, il perd de 37 points.

## LE FILTRE, RÉSULTAT COMPLET (quatre gestes testables par ablation)
| geste | levier | prof | témoin | écart | désaccord | verdict |
|---|---|---|---|---|---|---|
| bond par binôme (cahier 1) | `bounding` | 49,5 | **86,5** | −37,0 | 40,1 % | **NUIT** |
| débordement (cahier 5) | `flank` | 49,5 | 59,5 | −10,0 | 28,7 % | **NUIT** |
| décrochage (cahier 6) | `retreat` | 49,5 | 50,4 | −0,9 | **0,8 %** | pas de leçon |
| posture basse (cahier 4) | `drop_to` | 49,6 | 49,5 | +0,1 | **1,2 %** | pas de leçon |

**AUCUN GESTE NE S'ENSEIGNE.** Et la seconde lame ⟨Fable⟩ — mesurer le désaccord
professeur↔témoin AVANT d'entraîner — a écarté deux gestes pour **0,8 %** et **1,2 %** de
désaccord : ils ne se déclenchent quasiment jamais, il n'y a rien à enseigner, et on le sait
sans un seul gradient. C'est précisément le diagnostic qui manquait à la distillation D1 la
veille (signal redondant à 88 % avec le navigateur).

## CE QUE ÇA CHANGE
Le professeur de l'étape 1 n'est plus la greffe (61,6 %, et qui exige le prix à l'exécution)
mais **cette doctrine scriptée à 84,6 %**, qui n'exige rien. Et le désaccord avec la référence
sera massif, donc la leçon existe — condition que D1 n'avait pas.

## CE QUE ÇA NE DIT PAS
Résultat de **GYMNASE**. Il ne dit rien d'Arma tant qu'il n'y est pas certifié. Et il ne dit
rien du bounding overwatch en général : il dit que **CETTE implémentation, à CETTE densité de
défense, coûte 36,6 points**.

---

# ⭐ DÉPÔT DÉFINITIF — LE MAÎTRE v2 À 91,0 %, ET LE MÉCANISME ÉTABLI (26/08, soir)

## LA RÉSERVE DE FABLE, LEVÉE PAR MESURE
> *« Ce chiffre est le MAXIMUM d'une grille explorée sur les six graines qui l'ont ensuite
> jugé — optimiste par construction. Rejoue la configuration gagnante sur des graines JAMAIS
> vues avant dépôt. »*

Rejoué sur **[301, 302, 303, 304, 305, 306]**, jamais vues ni à l'entraînement, ni à la
sélection, ni au jugement de tout le dossier :

| doctrine | prise | étendue | tenus | survivants |
|---|---|---|---|---|
| **maître v2** (bounding=F, flank=T, postures→TIRER) | **91,0 %** | [87,9 ; 95,3] | 146,7 m | **3,17 / 4** |
| `flanc` — la meilleure doctrine du dépôt | 35,0 % | [31,2 ; 37,9] | 98,9 m | 1,50 |
| `frontal` | 14,3 % | [12,9 ; 18,0] | 112,2 m | 0,06 |

**Écart graines vues / graines neuves : −0,1 point.** Le chiffre n'était pas flatté par sa
propre sélection. **Déposable, avec le tampon de portée « dans ce monde ».**

## ⭐⭐ LE MOTIF DEVIENT CAUSAL — DOSE-RÉPONSE D'IMMOBILITÉ
Protocole ⟨Fable⟩ : on injecte dans le maître gagnant des pauses forcées de 0, 1, 2, 4 pas à
instants aléatoires (~1 homme sur 8 par pas). **Une seule variable manipulée**, rien d'autre
ne change.

| pause forcée | prise | coût | tenus | survivants |
|---|---|---|---|---|
| 0 pas | **91,0 %** | — | 147,0 m | 3,17 |
| 1 pas | 73,2 % | **−17,8** | 131,3 m | 2,34 |
| 2 pas | 64,5 % | **−26,6** | 123,3 m | 1,95 |
| 4 pas | 52,4 % | **−38,6** | 112,9 m | 1,54 |

**Monotone**, et les trois grandeurs descendent ensemble. *« Tout ce qui fige un homme coûte »*
cesse d'être un récit posé sur trois ablations : c'est **établi causalement dans ce monde**.

## ⭐ LA COHÉRENCE QUANTITATIVE QUE JE N'AVAIS PAS PRÉVUE
Le **bond par binôme coûte −37,0**. Une **pause forcée de 4 pas coûte −38,6**. Or le bond gèle
exactement la moitié de l'escouade par cycles de **4 pas**. Les deux chiffres, obtenus par des
manipulations indépendantes, se recoupent. **L'explication mécanique tient sur ses chiffres,
pas seulement sur son histoire.**

## LE CONTRÔLE S3 EST PROPRE
Deux appels sur le MÊME état diffèrent sur **87,4 %** des hommes : le cap aléatoire est retiré
à chaque décision. ⚠️ J'avais déjà payé 3,9 points pour une permutation figée le 25/08 — la
faute n'est pas répétée.

## LA PORTÉE, ET ELLE EST ÉTROITE
· Résultat de **GYMNASE**. Interdiction d'en tirer une phrase tournée vers Arma ⟨Fable⟩ :
  l'avantage du flanc est un mécanisme dont ce dossier a montré qu'il **disparaît** quand on
  corrige la létalité ×4 du bac à sable. Une part du 91,0 peut être du parfum de gymnase.
· Le verdict sur les gestes ne dit **pas** « les gestes ne valent rien ». Il dit :
  **« les gestes de manœuvre ne s'enseignent pas DANS CE MONDE »** — `secure_only` dans un
  monde qui sous-facture l'exposition récompense la course, donc tout geste qui échange du
  temps contre de la sécurité **paie le temps sans encaisser la sécurité**. Le bond a une
  marge mesurée ailleurs, et une porte certifie dans son monde.
· Durcissement non fait, à garder au registre : balayer l'effectif défenseur (5-8). Une
  doctrine qui gagne en combattant se dégrade proprement ; un exploit s'effondre.
