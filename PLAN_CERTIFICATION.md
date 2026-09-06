# PLAN DE CERTIFICATION DU GYMNASE — état au 07/09/2026

Plan arrêté par Fable le 07/09. **Ordre non négociable :**
`ancre de niveau` → `invariants de mécanisme` → `paires` → `paires tenues à l'écart`.
Aucun étage ne se lit avant que le précédent tienne. **7 nuits, 9 au pire, < 24 h GPU.**
« En dessous de 7, ce n'est pas un certificat, c'est une revendication. »

---

## ✅ FAIT — mesuré sur Arma, critères écrits avant, contrôles positifs joués avant

- [x] **Courbe de toucher remesurée à `HitPart`** — un impact par PROJECTILE, source appariée,
      tireur ET cible invulnérables. Instrument **reproductible** : 100 m debout
      0,402 [0,371;0,435] n=902 puis 0,383 [0,335;0,434] n=368. 18 conditions, ~17 000 balles.
- [x] **`p_touche` croît avec le rang du coup** — 0,354 [0,328;0,381] aux coups 1-10 contre
      0,407 [0,394;0,419] aux 31-80, IC disjoints, hausse persistante DANS les mêmes duels.
- [x] **`degat_par_impact` re-dérivé sur l'acte de mort** — médiane 4,0 impacts, n=83 → **0,175**
      (l'ancien 0,233 = 0,7/3,00 venait du capteur qui sur-comptait).
- [x] **Loi auditive VALIDÉE avec sa forme** — `audSide(d) = min(2177/d² ; 1,35)`, jamais 1,5,
      nulle au-delà de 100 m ; 1/d² prédit 1,78, mesuré 1,79.
- [x] **Porte `MinVisibleFire = 0,63` FALSIFIÉE** (37,1 % contre 10 % pré-inscrits) → retirée.
- [x] **`visible²` RÉFUTÉ** — exposant mesuré **0,72** [0,39 ; 0,97].
- [x] **4 valeurs `configFile` lues** — rayon 1,688 m · sensitivity 6,0 · sensitivityEar 0,125 ·
      audible 0,05 · `indirectHitRange` 0,0.
- [x] **Signe « flanc +17,3 » DÉGELÉ** — reclassé « dépendant de la létalité ».
- [x] **Infrastructure** — sentinelle de pont · harnais de banc (contrôle positif en bloc 0,
      bronze par épisode, survie à la mort du pont) · déploiement du SQF depuis git.
- [x] **Bras à trois voies sur Arma** (8c4, 220 m, 300 s) — A 0,357 [0,163;0,612] · B 0,214 · C 0,214.
- [~] **Nuit B contre C, 252 épisodes** — B 42/126=0,333 · C 41/125=0,328, écart −0,005
      IC95 [−0,122;+0,111]. **EXPLORATOIRE, pas verdict** : mon contrôle a échoué (104/251 = 41,4 %).

---

## 🔜 À FAIRE — dans l'ordre

### Nuit 1 — l'ancre et B/C manipulé  *(1 nuit Arma)*
- [ ] **Remplacer le contrôle « morts des deux côtés »** (c'était un RÉSULTAT, pas un contrôle) par :
      - [ ] **engagement** : chaque camp a tiré dans ≥ 95 % des épisodes ;
      - [ ] **manipulation** : azimut de chaque attaquant / axe défendu au premier coup reçu —
            **≥ 60° dans ≥ 80 % des C**, **≤ 20° dans ≥ 80 % des B**.
- [ ] Si C n'est pas livré → réparer la livraison en SQF (20 épisodes) **ou retirer la paire**.
      **Ne jamais conclure « le flanc ne fait rien ».**
- [ ] **Ancre = B**, pas A (A a 45 points d'IC à n=14). Contrôle : **IC ≤ ±0,08** et
      **première moitié = seconde moitié** (le déclin inexpliqué devient un contrôle).
- [ ] Figer **capteur et SQF par hash git** avant la première nuit.

### En parallèle sur GPU — la détection  *(0 nuit, heures GPU)*
- [ ] **Allumer `canal_cwr` EN BLOC** — une loi, une bascule, rien d'autre ne bouge.
      *(La détection d'abord : elle a une loi Arma certifiée avec sa forme. Le couvert n'a qu'une enveloppe.)*
- [ ] **Contrôle (i)** : le multiplicateur « être vu » du gymnase entre dans l'IC du **+75 %**,
      même dispositif B et même estimateur que les 563 k obs.
- [ ] **Contrôle (ii)** : B au gymnase entre dans l'IC de l'ancre.
- [ ] ⚠️ **Niveau dedans avec multiplicateur dehors = COMPENSATION → refus.** (Piège de `26/07 · 0,233`.)
- [ ] **Invariant gratuit** : rapport pertes att/déf de B au gymnase dans l'IC d'Arma (1,79 / 1,04),
      sans avoir été recopié.

### Le couvert — SEULEMENT si (ii) échoue avec (i) passé  *(1 nuit Arma + GPU)*
- [ ] Étendre `HitPart` à 4-6 conditions de couvert (mur bas, couché derrière buisson, 100/200 m).
- [ ] Le gymnase prend **la courbe mesurée, jamais un facteur**.

### Nuits 2-4 — l'étoile autour de B  *(3 nuits, 2 instances, 2 X par nuit)*
- [ ] Chaque paire = **B contre X**, ABBA par nuit, sites épinglés (jamais `nearRoads` sans ordre stable).
- [ ] **Ancre en NIVEAU, paires en AMPLITUDE** : chaque paire exige un écart Arma qui **exclut 0**,
      sinon elle ne certifie rien et **est remplacée**.
- [ ] Le gymnase doit reproduire **le signe ET l'écart** dans l'IC95 de l'écart Arma.
- [ ] **Marge d'équivalence pré-inscrite** : δ = 0,10 en niveau, 0,15 en écart — sinon huit tests
      à 95 % refusent un gymnase parfait **une fois sur trois**.
- [ ] Les paires ne règlent JAMAIS le gymnase : seuls l'ancre et les lois micro le règlent.

### Le gel, puis les tenues à l'écart  *(2 nuits)*
- [ ] **GELER le gymnase par hash.**
- [ ] Jouer les **2 dernières paires** sur Arma **après** le gel. Lues avant → **certificat nul**.
- [ ] +1 à +2 nuits pour remplacer les paires à effet Arma nul.

---

## ⛔ ABANDONNÉ — ne pas y revenir
- les six appariements courbe × dégât — *« le niveau ne viendra pas d'une forme »* ;
- le contrôle « morts des deux côtés » ;
- **le +17,3 du gymnase** — mesuré à la mauvaise létalité, nul et non avenu, à remesurer après ;
- **le signe comme critère** ;
- `cible_unique=True` — remplacé par l'empilement du canal ;
- toute paire à effet Arma nul.

## 🚫 HORS PÉRIMÈTRE tant que l'ancre ne tient pas
pente (Arma sépare 1,47×) · 2,5D (`los_boites` accordé 5/5, non branché) · son · fumée · blessé ·
munition. *« Chaque paramètre ajouté avant que l'ancre tienne est un compensateur de plus. »*

## 📌 PÉRIMÈTRE R, borné
sites plats (pente ≤ 5 % sur l'axe d'approche) · terrain ouvert · 4c4 ou 8c4 · 150-250 m · 300 s ·
corps obéissant. **ÉQ. 1 reste suspendue** jusqu'aux contrôles (i) et (ii).
