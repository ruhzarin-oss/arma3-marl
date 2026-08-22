# ⛔ LA COMPARAISON DU 22/08 EST RETIRÉE — les deux nuits ne partaient pas du même endroit

**22/08/2026, soir.** Retire `VERDICT_COMPARAISON_22-08.md` (commit `b1d0109`) et son
écart de **−15,4 points**. Trouvé en cherchant le mécanisme, pas en cherchant une sortie.

## La cause, lue dans le code

| ligne | ce qui se passe |
|---|---|
| `banc_live.py:192` | **si le bras est « natif »**, le groupe reçoit son ordre d'assaut (`addWaypoint`, SAD, COMBAT) — **à l'intérieur du bloc SCENE** |
| `banc_live.py:266` | la scène est envoyée au jeu |
| `banc_live.py:297-326` | **le prévol commence**, et dure **60 à 180 s** |

> **L'IA d'Arma marche pendant tout le prévol.** Les hommes de la politique ont
> `AUTOCOMBAT` et la FSM coupés : ils attendent un ordre qui n'arrive qu'au pas 0.

## Ce que ça a produit — mesuré

| | départ médian | déjà à moins de 150 m au pas 0 | départ minimum |
|---|---|---|---|
| **NATIF** | **135 m** | **88 sur 113 — 78 %** | **49 m** |
| **POLITIQUE** | **164 m** | 13 sur 112 — **12 %** | 91 m |

**Même scène, même consigne de 170 m.** L'écart de départ vaut **29 mètres de médiane**, et
un épisode natif sur trois commence à moins de 120 m — une bande où la politique n'a
**que 2 épisodes**.

**Et le budget MORD** : 90 % des arrivées se font au pas **52-56** sur un budget de **60**.
Vingt-neuf mètres d'avance, à ~5 m par pas, valent environ **six pas** sur un budget qui
n'en a plus.

## Le second biais, même origine

`VERDICT_BANC_SANS_ADVERSAIRE.md` (`61e8800`) : **26 épisodes natif et 31 politique n'ont
aucun défenseur** — ils meurent aussi pendant le prévol. **Les deux biais naissent du même
endroit et poussent dans le même sens.**

## Ce que la stratification NE répare PAS

À départ apparié (150-168 m, la seule bande peuplée des deux côtés) l'écart **s'inverse** :
natif **36,4 %** (n=22) contre politique **39,3 %** (n=61), soit **−3,0 points**.

⚠️ **Ce chiffre ne remplace pas le verdict retiré, et il ne dit pas que la politique vaut
le natif.** Conditionner sur la distance de départ, c'est conditionner sur une variable
**produite par le traitement lui-même** : les épisodes natif restés à 150-168 m sont ceux où
l'IA n'a **pas** avancé pendant le prévol — donc un sous-ensemble particulier, probablement
accroché ou fixé. **On ne répare pas un appariement cassé en le stratifiant après coup.**

## Le standard, appliqué à moi-même

Le 21/08 le natif à 68,2 % a été retiré pour **5 306 erreurs de script**, avec ce motif :
*ne pas le retirer serait une justice à deux vitesses, et elle pencherait du côté qui flatte.*
**Ici le biais penche du côté qui flatte le natif, c'est-à-dire du côté de ma conclusion.**
Deux issues, pas trois : **re-mesurer sous un protocole apparié, ou déclarer la comparaison
impossible.** « L'écart est sans doute réel quand même » n'en est pas une.

⭐ **Cliquet : un banc qui laisse un bras jouer avant le départ ne mesure pas les deux bras.**
Le prévol devait certifier le monde. Il est devenu une **avance de course** pour un seul camp.

## Ce qui SURVIT

- **La politique vaut 44,2 %** sous ses propres conditions — le chiffre n'a jamais dépendu
  du natif.
- **La politique échoue 13 fois sur 31 dans un monde SANS aucun ennemi** (7 lentes,
  4 dépassements, 2 gelées). C'est un fait **sur elle seule**, sans comparaison.
- **Le candidat A** est intact : il ne touche jamais à Arma ([[VERDICT_CANDIDAT_A_22-08]]).

## La réparation, si Younes la veut

**Déplacer l'`addWaypoint` du natif après le prévol**, au pas 0, à l'instant même où la
politique reçoit son premier ordre. Une ligne. Puis **rejouer les deux nuits** — environ
**14 heures**. Rien n'est relancé sans son arbitrage : c'est un changement de protocole.
