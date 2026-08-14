# VERDICT — la politique se fige parce que ARMA LA NOURRIT HORS DE SA DISTRIBUTION

Mesuré le 14/08/2026, sur décision de Fable (relevé **+ rejeu hors-ligne**, les deux
mâchoires). Relevé : `/tmp/releve_live.npz`, `statut=montage` ⟨règle 17⟩, 186 décisions
sur 24 pas. Gymnase : graine 101, **held-out**, 10 240 décisions.

## Les trois hypothèses, départagées d'un coup

### 1. La politique est-elle dégénérée ? NON — contrôle positif PASSÉ ⟨règle 16⟩

Le **même `.pt`**, nourri par le gymnase :

```
GYMNASE   {0:2750, 1:1441, 2:1144, 3:1459, 5:2115, 6:873, 7:342, 9:116}
          action dominante 26,9 %   ·   8 actions distinctes sur 10   ·   prise 59,4 %
```

**La politique sait varier.** Les colonnes ne sont pas innocentées par défaut.

### 2. La plomberie vive ment-elle ? NON

```
ARMA en vif             {0:174, 1:12}    dominante 93,5 %
ARMA rejoué hors-ligne  {0:174, 1:12}    dominante 93,5 %
accord : 100,0 % sur 186 décisions
```

Les mêmes observations donnent les mêmes actions. **Aucun décalage d'index entre la tête
du réseau et le SQF, aucun écart entre obs livrées et obs relevées.**

### 3. Les colonnes sortent-elles de la distribution ? OUI, massivement

| colonne | gym 1 % | gym 50 % | gym 99 % | arma 1 % | arma 50 % | arma 99 % | |
|---|---|---|---|---|---|---|---|
| apx/S | −0,863 | −0,057 | 0,834 | 0,159 | 0,237 | 0,363 | ok |
| **apy/S** | −0,715 | 0,018 | 0,792 | −0,883 | **−0,796** | −0,683 | **HORS** |
| dgx | −0,834 | 0,057 | 0,863 | −0,363 | −0,237 | −0,159 | ok |
| **dgy** | −0,792 | −0,018 | 0,715 | 0,683 | **0,796** | 0,883 | **HORS** |
| alive | 0,000 | 1,000 | 1,000 | 0,000 | 1,000 | 1,000 | ok |
| **slope** | 0,066 | 0,368 | 0,894 | 0,000 | **0,000** | 0,277 | **HORS** |
| **dcover** | 0,000 | 0,035 | 0,131 | 0,493 | **0,533** | 0,533 | **HORS** |
| los | 0,000 | 0,000 | 1,000 | 0,000 | 0,054 | 1,000 | ok |
| **nd** | 0,035 | 0,414 | 0,767 | 0,703 | **0,824** | 0,938 | **HORS** |
| post_debout / accroupi / couché | 1 / 0 / 0 | | | 1 / 0 / 0 | | | ok |

**5 colonnes sur 12 ont leur médiane Arma hors de la plage 1-99 % du gymnase.**
**100 % des décisions d'Arma sont hors distribution sur au moins une colonne.**

## Ce que les cinq disent, une par une

- **`apy/S` et `dgy`** (position et direction au but) : sur Arma les hommes tiennent une
  bande étroite d'un seul côté (apy ∈ [−0,883 ; −0,683]) là où le gymnase les étale de
  −0,715 à 0,792. **C'est le banc qui les fait naître au même endroit** — une faute de
  géométrie, pas de capteur.
- **`slope`** : médiane Arma **0,000** contre 0,368 au gymnase. La réparation du 13/08 a
  corrigé l'ÉCHELLE ; la colonne rend zéro quand même. Site plat, ou capteur toujours muet.
- **`dcover`** : médiane 0,533, plage [0,493 ; 0,533] — **quatre fois le 99ᵉ centile du
  gymnase, et quasi CONSTANTE**. Une constante est la signature d'un capteur cassé.
  **Troisième fois que `dcover` est faux** ; il a été « réparé » aujourd'hui même.
- **`nd`** : 0,824 contre 0,414 — hors par le haut.

## Le verdict

**La faute est dans la perception, pas dans le corps.** Fable l'avait désignée sans
mesurer, sur trois indices : l'aveu du docstring (à 200 m, quatre colonnes hors plage —
et on avait déplacé le décor à 170 m **au lieu de réparer**, cachant le symptôme dans le
scénario) ; neuf colonnes jamais vérifiées ; et la signature d'une **émission** uniforme,
qui est en amont de l'exécution.

Un réseau nourri hors de sa distribution sature et crache une constante. Le gel n'est
d'ailleurs pas attaché à une action : trois épisodes l'ont vu tomber sur 0, puis sur 6-7,
puis sur 0 — il tombe où l'entrée le pousse.

## Ce que ça NE dit pas

Un seul épisode Arma, un seul site, 186 décisions. Les plages Arma sont minces. Mais
**100 % de décisions hors distribution n'est pas un résultat marginal**, et il est
cohérent avec l'aveu déjà écrit dans le code.

## Aveu de méthode

Ma première passe affichait des **noms de colonnes inventés** — je les avais devinés au
lieu de lire l'ordre déclaré en tête de `arma_couture.py`. Le résultat est positionnel,
donc il tient ; les étiquettes étaient fausses. Corrigé, relancé, table ci-dessus juste.

## Suite

Aucune campagne de répétitions sur le live tant que ces cinq colonnes ne sont pas rendues
à leur plage. **Mesurer précisément un instrument dégénéré est la faute qui a coûté
quatre campagnes à l'étage 1.**
