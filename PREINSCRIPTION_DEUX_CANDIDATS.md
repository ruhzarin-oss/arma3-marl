# LES DEUX CANDIDATS À L'ÉCART — pré-inscription écrite AVANT toute mesure

**22/08/2026.** Suite de `VERDICT_COMPARAISON_22-08.md` : l'IA native bat la politique de
**15,4 points**. Le verdict dit **rien de la cause**. Deux candidats étaient notés et non
mesurés ; on les mesure ici, **sans réentraîner**.

---

## CANDIDAT A — « l'agent voit la pente sans la payer »

Dans le gymnase, la pente est dans l'**observation** mais **n'agit pas sur le déplacement** :
le pas fait 14 m qu'on monte ou qu'on descende. Arma sépare les deux régimes à **1,47×**.

### L'instrument — ABLATION À L'ÉVALUATION, zéro pas d'entraînement

La politique **déjà entraînée** est rejouée dans le gymnase, sur les **mêmes graines**, avec :
- **bras témoin** : observation intacte ;
- **bras brouillé** : la colonne `slope` est **permutée entre environnements** — la dimension
  reste, l'information meurt.

⚠️ On **permute** au lieu de **retirer** : retirer changerait la taille de l'entrée et le
réseau ne saurait plus lire. Une ablation doit tuer l'information, pas casser l'instrument.

### Les prédictions

| n° | prédiction |
|---|---|
| **A1** | l'écart de taux de prise entre intact et brouillé est **< 3 points** |
| **A2** | il reste **< 3 points** sur au moins **2 graines sur 3** |

**Justification de A1** : rien n'a jamais payé la pente pendant l'entraînement, donc la
politique n'a aucune raison de l'avoir apprise. **Si A1 passe, elle est aveugle à la pente**,
et lui faire payer le terrain ne servirait à rien tant qu'elle ne le regarde pas.

### Le falsificateur

> **Si l'écart dépasse 3 points, la politique LIT la pente** — et le candidat A change de
> sens : elle la lit sans la payer, donc lui faire payer deviendrait un levier réel.

---

## CANDIDAT B — « l'adversaire du gymnase n'est pas l'IA d'Arma »

### L'instrument — DIFFÉRENTIEL SCRIPTÉ, zéro pas d'entraînement

**Les mêmes manœuvres scriptées** jouées contre les deux adversaires, et **leurs réponses
comparées** sur des observables présents des deux côtés :

| observable | |
|---|---|
| distance du premier tir | à quelle portée l'adversaire ouvre le feu |
| coups par pas | sa cadence |
| fraction du temps où l'attaquant est touché | sa létalité effective |
| pertes attaquantes à la fin | l'issue |

Manœuvres : **frontale directe**, **flanc**, **arrêt à mi-distance**. Trois, fixées ici.

### Les prédictions

| n° | prédiction |
|---|---|
| **B1** | au moins **un** observable diffère de plus de **30 %** entre les deux adversaires |
| **B2** | l'**ordre** des trois manœuvres n'est pas le même des deux côtés |

**B2 est le plus important** : si l'adversaire du gymnase classe les manœuvres autrement que
l'IA d'Arma, alors **le gymnase enseigne une tactique que le monde ne récompense pas** — et
c'est un mécanisme d'écart, pas une différence de décor.

### Le falsificateur

> **Si les quatre observables concordent à moins de 30 % ET que l'ordre des manœuvres est le
> même, le candidat B tombe** : l'adversaire du gymnase se comporte comme l'IA d'Arma, et
> l'écart vient d'ailleurs.

---

## CE QUI EST INTERDIT ICI

- **Réentraîner quoi que ce soit.** Ces deux mesures portent sur des artefacts existants.
- **Ajouter un troisième candidat** si les deux tombent. La liste est fermée : si A et B
  tombent tous les deux, l'écart de 15,4 points reste **inexpliqué**, et c'est ce qu'on écrira.
- **Choisir le seuil après avoir vu les nombres.** 3 points et 30 % sont posés ici.
