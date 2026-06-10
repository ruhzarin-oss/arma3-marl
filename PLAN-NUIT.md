# PROGRAMME DE NUIT — 10/06 ~00:50 → ~08:50 (bâtisseur-Linux, autonome)

## Cadre & discipline (gravé, non négociable)
- **Répartition matériel** : MOI = 16 serveurs Arma (CPU). ARCHI = 3090 (ammo). Le **journal `MEMOIRE-COMMUNE.md`** = cerveau commun (append-only, jamais réécrire → pas de collision SSH).
- **Tout run** : détaché (`setsid`), log dur dans `logs_train/`, jsonl **append-only**, **n≥16**.
- **Pré-enregistrer les prédictions AVANT chaque table** (track-record Tetlock, sans spin).
- **Confirmer par split-half tout résultat surprenant** avant de le graver (leçon disperse : un écart < ~20 pts à n=16 peut être du bruit).
- **Off-ramp à chaque gate** : si le résultat tue l'hypothèse → STOP la ligne, ne pas brûler le compute, basculer sur solidification/rapport honnête.
- **Pas de build spéculatif lourd sans gate franchi.** En cas d'ambiguïté de gate : je m'arrête, je laisse le résultat + la question pour Younes, je ne devine pas.

---

## GATE 0 — confirmer l'inversion (EN COURS, fin ~01:18)
`react_confirm` n=16 (M1+M3 vs skilled_react, seeds 8-15, append, split-half).
- **Critère ✅** : M3 reste ≪ M1 sur seeds 8-15 ET M3 n=16 ≤ 25 % < M1 n=16.
- **✅ → Étape 1.  ❌ (M3 remonte) → OFF-RAMP A** : l'inversion n=8 était du bruit → rapport négatif + solidification, on rejoint l'archi sur l'ammo.

## ÉTAPE 1 — 2ᵉ défense intelligente : anti-frontal (~01:20-01:50)
Construire `skilled_react_depth` : la réserve se masse au **CENTRE/profondeur** quand le contact est frontal → doit **punir M1**, laisser le flanc libre à **M3**.
- Build SQF (miroir de REACTIVE_DEF_SQF) + smoke 1 op (zéro erreur SQF + op résout).
- **Pré-pred** : vs depth, M1 chute (< 35 %), M3 tient/monte (> 50 %). Si M1 NE chute PAS → la défense anti-frontal ne mord pas, je le note et je passe (pas de 2e axe propre).

## ÉTAPE 2 — LA MATRICE attaque × défense (~01:50-04:00) — le vrai « 2 axes »
- **Attaques** : M1, M2, M3, M5.  **Défenses** : `skilled` (passive), `skilled_react` (anti-flanc), `skilled_react_depth` (anti-centre).
- Mesurer les **cellules manquantes** n=16 (16 serveurs, 1 vague/cellule ~13 min). Réutiliser les cellules connues (skilled×{M1,M2,M3,M5} = 50/31/62.5/25 ; react×{M1,M3} = 50/0).
- À mesurer : react×{M2,M5}, depth×{M1,M2,M3,M5}.
- **Pré-pred matrice (gravée)** : passive→M3 meilleur ; anti-flanc→M1 meilleur ; anti-centre→M3 (ou M2) meilleur.
- **Question décisive** : y a-t-il **AUCUNE ligne d'attaque dominante** (la meilleure attaque CHANGE selon la défense) ?

## GATE 1 — la matrice montre-t-elle du pierre-feuille-ciseaux ? (~04:00)
- **✅** best-attaque change selon défense → Étape 3.
- **❌** une attaque domine partout (même contre les 2 défenses intelligentes) → l'inversion react était isolée → journal nuancé + **OFF-RAMP B** (officier faiblement justifié, on s'arrête là).

## ÉTAPE 3 — quantifier la VALEUR de la sélection (~04:00-05:00)
- `value_of_selection` = moyenne(meilleure-attaque-PAR-défense) − moyenne(meilleure-attaque-FIXE-globale).
- **> ~15-20 pts** → un officier qui CHOISIT bat n'importe quelle manœuvre fixe → **justification chiffrée du LLM-officier ET du défenseur appris.**
- Scaffold (PAS d'entraînement) : `officer_selector_stub` qui lit la défense → sort l'attaque optimale selon la matrice ; mesurer son score vs M3-fixe vs M1-fixe.

## ÉTAPE 4 — robustesse + hygiène (~05:00-06:00)
- Re-confirmer à **n=32** toute cellule pivot dont l'écart au 2ᵉ < 20 pts.
- Vérifier les confounds (pris vs mil, QRF-spawn) sur les cellules clés.
- Commits propres + tag (sans push).

## ÉTAPE 5 — spec du défenseur APPRIS (handoff archi) + rapport (~06:00-08:30)
- Écrire dans le journal la **spec de l'axe-défense RL** pour l'archi (sa 3090) : état→posture défensive, reward = nier la colline / maximiser les pertes attaquant, co-évolution self-play vs le répertoire d'attaque. C'est SA brique (GPU), je la prépare, je ne l'entraîne pas.
- Rédiger `REPORT_nuit.md` + entrée journal finale + (si temps) PDF eisvogel soigné.

## Garde-fous opérationnels
- Crash flotte → reboot 16 serveurs + reprise APPEND-only.
- Je touche **zéro** fichier ammo/GPU de l'archi. Coordination uniquement par le journal.
- Rapport prêt au réveil (~08:50) : matrice complète, valeur de sélection, verdict officier, spec défenseur appris.
