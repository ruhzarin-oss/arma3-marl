# REGISTRE DES VERSIONS — harnais de mesure « École de guerre »
But : tracer, version par version, **les problèmes qui se sont posés, ceux qu'on a résolus, et ce que ça invalide**.
Règle : les chiffres de deux versions de harnais ne se comparent JAMAIS directement — seulement structure à structure
(classements, familles). Détail chronologique complet : MEMOIRE-COMMUNE.md. Trace technique : git (tags par version).

---

## Harnais v1 — wargame opérationnel (05-06/06, baseline P-v3b)
**Contenu** : partition scriptée 4 escouades, garnison 12 + 2 patrouilles + QRF, spawns historiques, acc 4, headless.
**Résultats clés** : P-v3b 72 % militaire (n=24+) ; paliers 1-2 (QRF mécanisée = change le MODE d'échec, pas le taux ; H1/H2).
**Problèmes posés → résolus ICI** : bug métrique (ennemi_brisé créditait une QRF jamais spawnée) → garnison prise obligatoire + QRF comptée si spawnée ; exploit d'esquive par l'anneau 60-120 m (sim) → spawn sur garr_down (sim SEULEMENT — pas reporté dans Arma, voir v2).
**Données** : wargame_v2_*.jsonl, logs_train/arm1-3.

## Table v2 — première table 7 manœuvres (06-07/06 nuit)
**Contenu** : répertoire doctrinal M1-M7 (maneuvers.py), 7×16 ops, 16 serveurs, QRF accrochée à l'ENTRÉE EN CONSOLIDATION.
**Résultats clés** : M2 62.5 > M1 56.2 = M5 56.2 > M6 50 > M3 31 > M4 25 = M7 25. **Loi : pression simultanée ≥2 axes
(A 56 % poolé) bat la fragmentation (B 27 %), z≈3.3.** Track-record préds : 1/6 (biais = surestimer la doctrine d'école).
**Problèmes DÉCOUVERTS (par le canal visuel, 07/06)** :
1. ⚠️ QRF ESQUIVABLE : les chemins de contingence sautent CONSOLIDATION → succès sans affronter la contre-attaque
   (disséqué sur AZALAI-01 ; QRF affrontée 50-81 % selon manœuvre → scores famille A flattés).
2. ⚠️ SPAWNS DANS L'EAU : les 4 spawns (y=15560-15740) sont EN MER → ~150-200 m de nage non modélisée en début
   de CHAQUE op (armes inutilisables, lenteur, exposition). Uniforme → comparaison interne valide, absolu biaisé.
3. ⚠️ LZ OCÉANIQUE (15180,15620) : exfil à la nage (marginal, verdict déjà joué).
**Résolution** : AUCUNE dans v2 (figée pour traçabilité) → tout corrigé d'un bloc en v3.
**Données** : table_maneuvers.jsonl (112 ops, noms de baptême ajoutés en cours de route), backup .bak-0607.

## Pont éditeur v1 → v2 (07/06, canal visuel — hors mesure)
**Problèmes posés → résolus** : gel d'index preprocessFile en solo → DLL hmt_ext (acquis C.4) ; resync v1 par sentinelle
cmd_1 → resets en plein vol (3 ops tuées) → protocole v2 sans état caché (numérotation continue max-disque+1, rattrapage
par sondage, écriture atomique tmp+rename) ; fichier vide = indistinguable d'absent (obs RPT en retard → step sans ordres)
→ noop-guard ; pause Arma à la perte de focus → -noPause (hmt-arma.sh) + timeout 600 s.
**Apport à la mesure** : c'est ce canal qui a DÉCOUVERT les 3 artefacts de v2 (une op regardée > 112 ops aveugles).

## Table v3 — harnais purgé (07/06 après-midi, OP-1 « SOCLE »)  [EN COURS]
**Changements (un bloc, pré-enregistrés AVANT mesure)** :
1. QRF déclenchée par CHUTE DE GARNISON, vérifiée chaque step (clé plan qrf_on_garrison) — l'esquive est morte.
2. Géo sèche mesurée par sonde surfaceIsWater : 4 spawns (y≥15820), LZ (15180,15840), POSTE_RES (15060,15800).
3. Wrapper _with_qrf_trigger sur les 7 manœuvres ; smoke validé (QRF_TRIGGER au step de la chute, QRF affrontée).
**Prédictions pré-enregistrées** : M1 50-70 · M2 45-60 · M3 25-45 · M4 20-40 · M5 35-55 · M6 35-55 · M7 15-35 ;
familles A-B ≥15 pts = loi confirmée · 5-15 affaiblie · <5/inversion = artefact ; QRF affrontée ~100 % attendue.
**Problème DÉJÀ posé par v3 (gravé après M1 seul)** : M1 = 93.8 % (préd réfutée vers le HAUT) — les spawns secs
compriment l'approche à ~170 m, l'écran de patrouilles ne mord plus → RÈGLE D'EFFET PLAFOND pré-enregistrée
(A ET B >85 % = NON-CONCLUANT ; départage secondaire : pertes, % QRF détruite, durée).
**Données** : table_maneuvers_v3.jsonl.

## v4 — (conditionnel, non ouvert)
Si plafond v3 confirmé : durcir le harnais SANS retour à la nage — défense renforcée (profils pro/hardcore portés
en mesure, cf. OP-3 « MIROIR ») et/ou théâtre plus profond (approche longue sur TERRE). Décision après verdict v3.
