# Rapport session autonome — 09/06 (mandat « lance toutes les étapes », 8h)

## TL;DR (le verdict)
Au niveau OPÉRATIONNEL (« gagner une bataille »), la trajectoire s'est conclue **proprement et tôt** :
1. **Le problème 83→0 est résolu** par l'école-de-guerre : on choisit une manœuvre du répertoire
   M1-M7 (Arma-exécutable par construction), au lieu de laisser un RL inventer une fiction de sim.
2. **M3 (enveloppement simple) est robustement la MEILLEURE manœuvre** sur tout l'espace de défense
   testé → **la PORTE est FERMÉE** (pas de signal de sélection) → **pas d'officier-sélecteur justifié**.
   (La thèse « officier » se dissout une 2e fois au contact de la mesure — comme le runaway KOTH.)
3. **M3-fixe ÉCRASE le scripté** : M3 vs `normal` = **100 % (16/16, mesuré cette nuit)** vs partition
   scriptée 72 % → +28 pts. Enveloppe complète : normal 100 / skilled 62.5 / skilled_hunt 50 / pro 31.2 /
   skilled_qrf 25 → M3 dégrade gracieusement (jamais 0, même vs pro où la v4 moyennait ~6 %).

→ **« Gagner des batailles en Arma » au niveau opérationnel = RÉSOLU par M3-fixe.** Pas besoin de
RL→LLM→RL-LLM ici (étapes 3-4 non déclenchées, conformément à la porte).

## Étape 1 — table précise vs `skilled` (n=16, 112 ops) ✅
Classement : **M3 62.5** > M1 50 > M6 43.8 > M4 37.5 = M7 37.5 > M2 31.2 > M5 25.0. Écart 37.5 pts.
⚠️ n=8 mentait (M2 « 62 % » @n8 → 31 % @n16) ; la loi des familles v2 NE tient PAS ici.

## Étape 2 — multi-situations (la PORTE) ✅ → FERMÉE
M1-M7 × n=16 sur skilled / skilled_hunt / skilled_qrf. **Gagnant = M3 sur les TROIS** (62.5 / 50.0 / 25.0).
Trois caractères de défense (garnison-skill / chasse-soutenue / QRF-massive) → même gagnant → pas de
problème de sélection.

## Étape 3 (officier) / 4 (RL-LLM) — NON déclenchées (porte fermée, conforme au plan).

## Enveloppe M3 (confirmée, n=16) ✅ : normal 100 / skilled 62.5 / skilled_hunt 50 / pro 31.2 / skilled_qrf 25.
M3 vs normal = 100 % > scripté 72 % (+28 pts). Dégradation gracieuse — robuste.

## CAVEAT HONNÊTE (la limite du verdict)
Les 3 situations étaient des variantes de la MÊME garnison (skill+géométrie identiques), variant la
chasse/QRF — donc difficulté/tempo, pas la STRUCTURE tactique. Un signal de sélection pourrait émerger
avec des défenses de GÉOMÉTRIE différente (garnison concentrée vs dispersée, points faibles distincts),
que les knobs actuels (mult/skill/hunt/qrf) ne produisent pas. → **Prochaine vraie question** : enrichir
l'espace de défense (géométrie) avant de reconclure « jamais de sélecteur ». C'est un build, pas un knob.

## Discipline / artefacts
n≥16 obligatoire (n=3-8 très bruyant, plusieurs fausses alertes corrigées). Scripts : run_table_skilled.sh,
run_table_multi.sh, run_m3_curve.sh, enemy_profiles (skilled/skilled_hunt/skilled_qrf/mid_*, knobs hunt/qrf),
run_maneuver (--base, --enemy). Données : table_skilled.jsonl, table_multi.jsonl, m3_curve.jsonl.
