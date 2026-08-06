# PORTE 0 — le certificat de naissance du banc

*6 août 2026, 14h30. Critères déposés AVANT toute exécution. Aucun chiffre du nouveau tarif
n'a été lu.*

> **Règle de gouvernement, déposée par Fable et valable pour tout banc futur :**
> aucun banc ne juge un agent avant d'avoir séparé **deux comportements scriptés dont l'ordre
> est connu**. Un banc qui ne distingue pas un crochet d'une ligne droite n'a rien à dire sur
> un agent appris.

## Pourquoi le banc a échoué hier soir

Les trois bras — champ, placebo, agent gelé — montaient tous au dernier barreau, 100 %
d'arrivée partout. Et surtout :

```
agent appris  expo 8,26   ·   agent GELE  8,21   ·   ligne DROITE  8,34
```

**Aller tout droit coûtait le même prix que manœuvrer.** Dans un monde où la ligne droite est
gratuite, aucun agent ne peut montrer quoi que ce soit, et aucun placebo ne peut perdre.

## 1. Le tarif — dérivé, pas réglé

Le tarif fixe le prix du risque contre celui d'arriver. Il vaut **4,7**, et la table de
provenance l'a signalé comme héritier : `1,75 × 2,67`, où le 1,75 datait de l'`expo` morte.

**La dérivation, et elle ne regarde aucun résultat :**

La récompense d'arrivée totale vaut `0,05 × (250 − 40) = 10,5`. C'est ce que vaut l'objectif,
tout entier.

Le risque appris est entraîné sur la **mortalité réelle** : sa sortie est en unités de « je me
fais tuer ». Or un assaillant tué ne prend rien.

> **Identité : un pic de risque de 1,0 doit coûter exactement l'objectif entier.**
> Donc **tarif = 10,5**.

À 4,7, le risque était payé **45 % de sa conséquence réelle**. C'est précisément pour ça que la
ligne droite était gratuite : elle achetait l'objectif à moitié prix.

⟨provenance : identité sur l'échelle de récompense, 06/08. Ce n'est pas un réglage — c'est
dire que mourir coûte ce que mourir coûte.⟩

**INTERDICTION DÉPOSÉE, recopiée de Fable :** on ne pousse pas le tarif au-delà de cette valeur
pour forcer la discrimination. Si la porte n'ouvre pas à 10,5, le banc est disqualifié pour
cette question et l'étage 1 déménage sur Arma. **Un banc qu'on doit forcer à voir n'est plus
un instrument.**

## 2. Les deux comportements scriptés, dont l'ordre est connu

**LA DROITE** — on va au but, cap direct. Existe déjà (`Directe`).

**LE CROCHET** — on achète l'écart **au tarif du long** puis on rentre en ligne droite. C'est
la doctrine mesurée le 27/07 : le crochet fait **74 % de son mouvement latéral au-delà de
160 m**, contre 21 % pour l'agent appris. Le côté se choisit en comparant le risque à gauche
et à droite — c'est un **regard**, pas un oracle sur la réponse.

L'ordre est connu : sur le monde mesuré, **le crochet prend 2,37 fois plus souvent pour
0,51 fois le coût**. Si le banc ne retrouve pas cet ordre, il est aveugle.

## 3. Les seuils, déposés

**DÉSATURATION** — la ligne droite doit cesser d'être gratuite :

> arrivée de la DROITE **< 95 %**, au départ de 250 m.

Tant qu'elle arrive à 100 %, il n'y a rien à arbitrer et le reste ne se lit pas.

**PORTE 0** — le crochet doit battre la droite, sur l'une **ou** l'autre de ces deux voies :

> **expo du crochet ≤ 0,85 × expo de la droite** (au moins 15 % de moins)
> **ou** arrivée du crochet **≥ +10 points** au-dessus de celle de la droite.

Une seule suffit — le crochet peut payer moins cher, ou arriver plus souvent, ou les deux.

**Sur 512 configurations jamais vues**, chaque bras évalué sans échantillonnage.

## 4. Ce qui la fait échouer — écrit maintenant

- **La droite arrive encore à 100 %** au tarif dérivé → le monde reste gratuit, la sandbox est
  **disqualifiée pour cette question**, et l'étage 1 se juge sur Arma. Pas de second essai de
  tarif.
- **Le crochet ne bat pas la droite** → le banc ne distingue pas deux doctrines dont l'ordre
  est mesuré. Même conséquence : disqualifié.
- **Le crochet bat la droite** → le banc a son certificat, et l'étage 1 se relance dans la
  foulée à **trois bras contemporains** : champ, placebo, sans-champ. Critères de l'étage 1
  inchangés, réserve sur l'AUC 0,6549 inchangée.

## 5. Instrumentation permanente, à partir de maintenant

Les trois bras de référence — **droite, agent gelé, crochet** — restent journalisés à chaque
run du banc. Ils viennent de servir de plancher et de plafond gratuits ; ils ne s'enlèvent plus.
