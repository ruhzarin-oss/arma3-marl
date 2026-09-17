# Plan — l'Architecte et l'Oracle

*17/09/2026, matin ; complété à midi (§ 4 bis : casser au maximum ; § 4 ter : voir ce que le détachement ne voit pas). Demandé par Younes après les lectures de P2 et P1 (deux choix « indifférents », témoin au plafond).
Son image : l'Architecte de Matrix cherche l'équation la plus propre, l'Oracle passe son temps à la perturber, et leur
lutte améliore les deux. Plan à valider : aucune ligne de code avant.*

## Pourquoi changer de modèle

- Jusqu'ici, l'expérimentateur devine une hypothèse, lance une campagne et obtient oui ou non. Chaque réponse ouvre une
  nouvelle question (type de menace, distance, moment) : le puzzle n'est jamais assemblé.
- Le témoin sans menace a pris la moitié des épisodes de P1 et P2, pour une issue toujours à 100 %.
- « Menace de niveau 3 » mêle deux menaces et une distance. Si elles demandent des options opposées, leurs effets
  s'annulent.

**Nouveau principe.** Deux camps se disputent le budget d'épisodes :
- l'**Architecte** apprend la règle de décision la plus simple ;
- l'**Oracle** cherche à **casser au maximum** les plans de l'Architecte, et y envoie les épisodes suivants ;
- l'Oracle **voit ce que le détachement ne voit pas** (la situation vraie θ) et dit quoi rendre visible.

La pression de l'Oracle doit pousser l'Architecte à se dépasser : corriger ses coefficients, puis inventer de
nouveaux termes, puis demander de nouvelles perceptions ou de nouvelles options (§ 4 bis et § 4 ter).

L'expérimentateur n'écrit plus les hypothèses. Il écrit les **règles du duel**, commitées avant le premier tour.

## 1. Les objets

```
θ ∈ Θ          la situation tirée par l'Oracle : type de menace, distance, moment, côté, monde w
ξ              le hasard propre de l'épisode (IA d'Arma, graine)
x = φ(θ, ξ)    ce que le détachement perçoit au moment du choix (ligne de décision : alarme, véhicule vu,
               défenseurs connus, vivants…)
a ∈ {0, 1}     l'option jouée
Y ∈ {0, 1}     l'issue primaire de la phase (phase discrète, observation utile…)
```

- **L'Architecte ne voit que x.** θ et `verite_defenseurs` sont réservés à l'Oracle et à la lecture. Sinon, la règle
  apprise utiliserait ce que le détachement ne peut pas savoir : elle serait injouable.
- **L'option est tirée à pile ou face**, avec une probabilité connue p = 1/2 écrite dans le job. L'option ne dépend
  alors de rien d'autre que la pièce : l'effet mesuré est causal.

## 2. L'Architecte : l'équation la plus propre

**Le modèle**

```
logit P(Y = 1 | x, a) = α + β·x + a·(γ₀ + γ·x)
```

En clair : β dit ce qui rend la phase facile ou difficile ; γ dit ce qui change **l'avantage de l'option 1**.

**La règle qui en découle**

```
π(x) = 1   si   γ₀ + γ·x > 0,   sinon 0
```

En clair : la fonction logistique est croissante. L'option 1 réussit donc plus souvent exactement quand γ₀ + γ·x est
positif. La règle est une frontière droite dans l'espace de ce que le détachement perçoit.

**« Propre » veut dire peu de coefficients**

```
(α, β, γ₀, γ) = argmin   − Σᵢ log P(Yᵢ | xᵢ, aᵢ)   +   λ · ( ‖β‖₁ + ‖γ‖₁ )
```

En clair : chaque coefficient coûte λ, et seuls restent ceux qui paient leur place. **Les γⱼ non nuls sont les causes
qui changent le bon choix.** C'est ce que le chercheur de causes devait trouver, mais sous une forme vérifiable.
λ est choisi par validation croisée, en laissant un monde de côté à chaque fois.

## 3. Juger l'Architecte sans se tromper

**Score de chaque épisode i pour chaque option a** (estimateur doublement robuste)

```
Γᵢ(a) = μ̂ₐ(xᵢ) + 1{aᵢ = a} / pₐ · ( Yᵢ − μ̂ₐ(xᵢ) )        avec pₐ = 1/2
```

En clair : on prend la prédiction du modèle, corrigée par l'erreur réellement observée quand cette option a été jouée.
Le score est sans biais si la pièce est honnête, même quand le modèle est faux. μ̂ est ajusté **sans le monde de
l'épisode i** (ajustement croisé par monde).

**Valeur d'une règle, et gain sur la meilleure option fixe**

```
V̂(π) = (1/n) · Σᵢ Γᵢ( π(xᵢ) )
G(π) = V̂(π) − max( V̂(0), V̂(1) )
```

En clair : G > 0 veut dire que décider selon la situation rapporte plus que jouer toujours la même option.
L'intervalle de confiance vient du rééchantillonnage des mondes, comme aujourd'hui.

## 4. L'Oracle : chercher la faille

**Le regret de la règle dans une situation θ**

```
ρ(θ) = max( V₀(θ), V₁(θ) ) − V_π(θ)
```

En clair : c'est ce que la règle perd, dans cette situation, par rapport à la meilleure option pour cette situation.
ρ peut être négatif quand la règle utilise mieux ce qu'elle perçoit que n'importe quelle option fixe.

**La propriété qui fait tout** (celle de PAIRED, Dennis et al., 2020)

- Situation impossible, où les deux options échouent : ρ = 0.
- Situation triviale, où les deux réussissent (le témoin de P1 et P2) : ρ = 0.

L'Oracle ne gagne rien à fabriquer des mondes injouables, ni à rejouer des mondes faciles. Il ne gagne que là où
**le choix compte et où la règle se trompe**.

**Estimation par case** (Θ découpé en cases k : type × tranche de distance × tranche de moment)

```
ρ̂ₖ = max( Γ̄ₖ(0), Γ̄ₖ(1) ) − Γ̄ₖ(π)
Uₖ = ρ̂ₖ + κ · σ̂ₖ                    tronqué à [0, 1]
```

En clair : le regret estimé, plus un bonus d'incertitude. Une case jamais visitée a un σ̂ grand, donc l'Oracle va voir.
Une case bien connue et sans regret s'éteint.

**Attention au maximum de moyennes bruitées.** Il est biaisé vers le haut, donc ρ̂ sert seulement à orienter l'Oracle.
Une faille n'est **déclarée** que sur des épisodes neufs :

```
âₖ = meilleure option de la case k, choisie sur les tours précédents
ρ̃ₖ = Γ̄ₖ^neuf(âₖ) − Γ̄ₖ^neuf(π)
faille déclarée si   ρ̃ₖ − z · σ̃ₖ > 0,    avec z = z_{1 − 0,05/K}  (K cases, correction de Bonferroni)
```

**Mise à jour de la répartition des situations** (poids exponentiels)

```
q_{t+1}(k) = (1 − η) · qₜ(k) · exp(ν · Uₖ) / Σⱼ qₜ(j) · exp(ν · Uⱼ)   +   η · q₀(k)
```

En clair : chaque case voit son poids multiplié selon sa faille présumée. Une part η, par exemple 20 %, reste tirée
uniformément dans Θ : l'Oracle ne perd jamais la vue d'ensemble.

**Limites de Θ**, écrites avant le premier tour : types de menace doctrinaux, distances plausibles, moments compris dans
la fenêtre de la phase. L'Oracle ne sort pas de Θ.

## 4 bis. Casser au maximum les plans de l'Architecte

*Ajouté le 17/09 à la demande de Younes : « l'Oracle doit casser au maximum les plans de l'Architecte, ça doit
pousser l'Architecte à se dépasser et trouver de nouvelles choses ».*

**Casser, c'est maximiser le regret, pas l'échec**

```
Oracle :   θ* = argmax_{θ ∈ Θ}  ρ_π(θ)          et non   argmax_{θ}  P(échec)
```

En clair : un Oracle qui gagne en rendant la mission impossible (tout échoue quelle que soit l'option) n'apprend rien
à l'Architecte. Dans ce monde-là, ρ = 0. L'Oracle n'est payé que quand **une autre option aurait réussi** et que la
règle ne l'a pas prise. C'est la seule manière de casser qui force l'Architecte à progresser.

**L'Oracle attaque en connaissant la règle** (boîte blanche). La frontière de l'Architecte, γ₀ + γ·x = 0, est
publique. L'Oracle regarde d'abord là où la règle bascule sous une petite perturbation de la situation :

```
sₖ = P( π(x') ≠ π(x) )   pour θ' voisin de θ dans la case k          (sensibilité de la règle)
Uₖ = ρ̂ₖ + κ · σ̂ₖ + κ_s · sₖ
```

- **Agressivité** : ν grand, pour que l'Oracle se concentre vite sur ce qui casse. La part uniforme η reste fixée
  (§ 6), elle garde la mesure honnête.
- **Pré-recherche** : le gymnase v0 prédit bien l'écart entre options. L'Oracle peut y chercher ses attaques sans
  dépenser d'épisodes, puis n'envoyer dans Arma que les meilleures. Arma confirme ou dément.

**Mesure du progrès : l'exploitabilité**

```
eₜ = maxₖ ρ̃ₖ(πₜ)        la pire faille confirmée de la règle au tour t
```

En clair : si l'Architecte se dépasse, la pire faille que l'Oracle arrive à confirmer baisse de tour en tour, alors
même que l'Oracle cherche de mieux en mieux. Si eₜ cesse de baisser alors que des failles restent, l'Architecte a
atteint la limite de sa forme ou de ses perceptions. Il doit monter d'un niveau (tableau ci-dessous).

**Non-régression : l'archive des failles.** Chaque faille confirmée entre dans une archive A. Une nouvelle règle
n'est acceptée que si elle ne rouvre pas les anciennes failles (mesure par ajustement croisé) :

```
accepter πₜ₊₁   seulement si   max_{k ∈ A} ρ̃ₖ(πₜ₊₁)  ≤  max_{k ∈ A} ρ̃ₖ(πₜ) + marge
```

Sans archive, les deux camps tournent en rond : l'Architecte oublie ce que l'Oracle lui a appris.

**Les trois niveaux pour se dépasser**

| niveau | quand l'Architecte y monte | ce qu'il change | critère d'acceptation |
|---|---|---|---|
| 1. coefficients | la faille se corrige en réajustant | γ | − log L + λ‖γ‖₁ minimal |
| 2. forme | la faille persiste après réajustement, et VI ≈ 0 (§ 4 ter) | un terme nouveau : produit, seuil, min… (agent-équation) | le terme paie sa place, voir ci-dessous |
| 3. perception ou option | VI élevée : la faille est invisible pour le détachement | une perception nouvelle dans la ligne de décision, ou une option nouvelle (« observer d'abord ») | VIⱼ plus grand que le coût de la perception |

**Niveau 2, la forme qui paie sa place** (longueur de description minimale)

```
f* = argmin_f   [ − log L_croisé(f)  +  λ · |f| ]          |f| = nombre de symboles de la formule
un terme nouveau est gardé si   log L_croisé(f') − log L_croisé(f)  >  λ · ( |f'| − |f| )
```

En clair : l'Architecte a le droit d'inventer un terme seulement si ce terme explique assez de failles, sur des
épisodes qu'il n'a pas vus, pour payer les symboles qu'il ajoute. C'est là que naissent les « nouvelles choses ».
Le banc `equation/` (dépôt 41f2ae6) teste justement quels algorithmes savent faire ce niveau sans inventer de fausses
formules.

## 4 ter. Voir ce que le détachement ne voit pas

**La valeur de l'information cachée**

```
VI(x) = E[ max_a μ_a(θ) | x ]  −  max_a E[ μ_a(θ) | x ]   ≥ 0
```

- Premier terme : on choisit en voyant la situation vraie θ, comme l'Oracle.
- Second terme : on choisit avec ce que perçoit le détachement, x.
- VI est toujours ≥ 0, parce que la moyenne des maximums est au moins le maximum des moyennes (inégalité de Jensen,
  le maximum est convexe).

**Ce que VI sépare**

- Regret élevé et VI ≈ 0 : l'information est visible, mais l'équation est mauvaise. C'est l'Architecte qui doit
  corriger (niveaux 1 et 2).
- VI élevée : aucune équation sur x ne peut gagner. L'Oracle a trouvé une variable cachée (niveau 3).

**Quelle variable cachée rendre visible**

```
VIⱼ = V̂( π_{x, θⱼ} ) − V̂( π_x )          règles apprises hors pli, valeurs par scores Γ (§ 3)
```

En clair : on compare une règle qui verrait aussi la composante θⱼ (type de menace, distance, position) à la règle
actuelle. La composante au plus grand VIⱼ est **ce que le détachement a le plus besoin de percevoir**. Elle devient une
perception nouvelle dans la ligne de décision (par exemple « patrouille repérée »), ou une option « observer d'abord ».
Chaque règle étant apprise imparfaitement, cette estimation est prudente : elle sous-estime plutôt VI.

**Premier usage possible, sans nouvel épisode.** Dans P1, P2 et P4, les perceptions au moment du choix sont presque
constantes, alors que le bras (menace ou témoin) change le résultat. Avec θ = bras, VI mesure ce que gagnerait un
détachement qui percevrait la menace. Une VI proche de 0 veut dire que voir la menace ne changerait pas le choix : c'est
ce qu'on attend pour P4, où le direct gagne partout.

## 5. Le duel, et quand il s'arrête

**Le jeu**

```
min_π   max_q   E_{θ∼q} [ ρ_π(θ) ]        sous la contrainte   q ≥ η · q₀
```

En clair : l'Architecte cherche la règle dont la pire faille est la plus petite. L'Oracle cherche la répartition de
situations qui la met le plus en défaut.

**Garantie connue.** Les poids exponentiels ont un regret moyen borné :

```
(1/T) · Regret_T  ≤  √( ln K / (2T) )  +  η        K cases, T tours, gains dans [0, 1], ν bien réglé
```

Le terme + η est le prix de la part uniforme : l'Oracle renonce volontairement à η de son attaque.

Si les deux camps ont un regret moyen qui tend vers 0, leurs stratégies moyennes tendent vers un équilibre du jeu
(Freund et Schapire, 1999). Notre Architecte se réajuste sur toutes les données avec une régularisation, ce qui
ressemble à « suivre le meneur régularisé ». Pour lui, la garantie n'est pas formelle : on surveille les courbes.

**Règle d'arrêt**, écrite avant

```
arrêt si   maxₖ ( ρ̃ₖ + z · σ̃ₖ ) < δ   deux tours de suite        (par exemple δ = 0,10)
```

En clair : il ne reste plus aucune case où la règle pourrait perdre plus de 10 points, vérifié sur épisodes neufs. Le
duel s'arrête aussi si le budget est épuisé.

**Test final**, sur des mondes jamais vus tirés selon q₀ :
- G(π) a une borne basse > 0 : **le choix dépend de la situation, la règle est apprise**, et γ dit dans quelles
  situations.
- G ≈ 0 et plus aucune faille : **le choix ne compte nulle part dans Θ**. C'est bien plus fort qu'« indifférent à un
  niveau de menace ».

## 6. Garder une mesure honnête malgré l'Oracle

L'Oracle tire plus souvent les situations difficiles, donc une moyenne brute serait faussée. On repondère vers la
répartition de référence q₀ :

```
V̂_{q₀}(π) = Σᵢ wᵢ · Γᵢ(π(xᵢ)) / Σᵢ wᵢ        wᵢ = q₀(θᵢ) / q̄(θᵢ)        q̄ = Σₜ nₜ · qₜ / Σₜ nₜ
```

En clair : chaque épisode pèse l'inverse de la fréquence à laquelle l'Oracle l'a demandé. Grâce à la part uniforme η :

```
qₜ ≥ η · q₀   pour tout t     ⇒     q̄ ≥ η · q₀     ⇒     wᵢ ≤ 1/η        (5 pour η = 0,2)
```

Les poids restent bornés, donc la variance ne peut pas exploser. C'est la raison d'être de η.

## 7. Combien d'épisodes

**Pour une case seule.** Voir un regret δ, sur une issue binaire autour de 50 %, avec un risque de 5 % et une puissance
de 80 % :

```
n par option ≈ ( z_{0,975} + z_{0,80} )² · 2 · p(1 − p) / δ²  =  3,9 / δ²
```

δ = 0,30 demande 44 épisodes par option ; δ = 0,20 en demande 98. Une case isolée coûte cher.

**C'est pourquoi l'Architecte a peu de paramètres** : il partage l'information entre les cases voisines. Règle de
prudence pour une logistique, au moins 10 issues rares par paramètre :

```
n ≥ 10 · d / min( p̄, 1 − p̄ )
```

Avec d = 16 paramètres (8 perceptions, pour β et pour γ) et p̄ = 0,4, il faut n ≥ 400 épisodes **au total**, pas
400 par case. Le débit réel (épisodes par heure sur 12 serveurs) sera mesuré au pilote.

## 8. Contrôles avant Arma (règle 16)

Le chercheur de causes v0 a échoué ses placebos. La boucle doit donc prouver qu'elle sait réussir et échouer **avant**
de coûter des épisodes Arma. On la teste dans un simulateur synthétique de quelques lignes, où la vérité est connue :

| contrôle | ce qu'on plante | attendu |
|---|---|---|
| positif | γ avec 2 coefficients non nuls | les 2 retrouvés dans au moins 18 répétitions sur 20, G > 0 |
| placebos | 3 perceptions sans effet | chacune sélectionnée au plus 1 fois sur 20 |
| nul | γ = 0 partout | aucune faille déclarée dans au moins 19 répétitions sur 20 |
| Oracle utile | frontière γ₀ + γ·x = 0 connue | q se concentre près de la frontière ; à budget égal, la règle est retrouvée avec moins d'épisodes qu'en tirage uniforme |
| injouable et trivial | cases où tout échoue, cases où tout réussit | leur poids redescend vers η · q₀ |

**Falsificateur de l'Oracle.** Si l'Oracle ne bat pas le tirage uniforme dans le simulateur, on le retire : un
plan uniforme sur Θ, analysé par l'Architecte, suffit.

## 9. Pièges connus d'avance

- **L'Oracle exploite l'instrument.** Il trouverait les situations où l'enregistreur refuse l'épisode (canari du monde
  9) ou bugue. Les épisodes refusés sont exclus, et le taux de refus est surveillé par case : au-delà de 20 %, la case
  est gelée et déclarée faute d'instrument, pas faille.
- **Malédiction du gagnant.** La case au plus grand ρ̂ l'est souvent par hasard. D'où ρ̃, mesuré sur épisodes neufs.
- **Fuite de vérité.** Si l'Architecte voit θ ou `verite_defenseurs`, sa règle est injouable. Un test dbt vérifie les
  colonnes interdites.
- **Charge machine.** Le taux dépend de la charge de la ferme (verdict `un-taux-porte-sa-charge-machine`). La part
  uniforme η de chaque tour sert de témoin de dérive d'un tour à l'autre.
- **Mondes mémorisés.** Il n'y a que 8 sites. L'ajustement croisé et le test final se font par monde, sinon la règle
  apprend les sites au lieu des situations.

## 10. Ce qu'il faudra construire (aucune ligne avant validation)

1. **Mission** : séparer, pour chaque menace, le type, la distance et le moment en leviers distincts (`menace_type`,
   `menace_dist`, `menace_t` par phase), au lieu du niveau 0-3 qui les couple. Écrire le θ réellement posé dans une
   ligne `CHACAL|E|situation_tiree`.
2. **Jobs** : un générateur qui tire θ selon qₜ, la pièce de l'option et les graines ; il écrit p et qₜ(θ) dans le job.
3. **dbt** : une table `duel_episodes` (θ, x, a, p, q, Y, accepté) et le test des colonnes interdites à l'Architecte.
4. **`architecte.py`** : logistique L1, ajustement croisé par monde, scores Γ, G et son intervalle.
5. **`oracle.py`** : cases, ρ̂, ρ̃, U, mise à jour exponentielle, tirage du tour suivant.
6. **La boucle** : un tour = poser ~96 épisodes, attendre, dbt, Architecte, Oracle, journal du tour.
7. **Les contrôles du § 8** dans le simulateur synthétique, avant tout épisode Arma.
8. **Pilote Arma** sur une phase courte.
9. Plus tard : le gymnase v0 prédit bien l'écart entre options (verdict `gymnase-de-decisions-predit-l-ecart-pas-le-niveau`).
   Il pourrait pré-classer les cases pour l'Oracle, sans dépenser d'épisodes.

## Décisions pour Younes

1. **Phase pilote** : P1 (épisodes de ~5 min, menace très lourde) ou P2 (patrouille qui roule contre poste fixe, et
   l'observable `vehicule_vu` déjà écrit) ?
2. **Limites de Θ** (types, distances, moments plausibles) : tu les fixes, ou je propose une table ?
3. **Seuils** : δ d'arrêt à 10 points ? part uniforme η à 20 % ? agressivité ν de l'Oracle ?
4. **P3, P4, P6** : les laisser finir et les lire (recommandé), leurs données pouvant amorcer l'Architecte.
