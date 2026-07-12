# PROTOCOL — A/B : upgrade sandbox 3D (LOS 2.5D + postures)

**Pré-enregistré le 2026-07-09, AVANT tout run.** Ce fichier fige la question, les
conditions, les métriques et le seuil de succès — pour éviter le p-hacking. Ne pas
modifier après avoir lancé (créer une v2 si besoin).

Commits de l'upgrade testé : `2a2a290` (LOS 2.5D) · `53026e4` (postures) ·
`4b3fd1d` (fix solidh) · `103c086` (fix obs_dim) · `1c3dfa3` (smoke-train).

---

## 1. Question de recherche & hypothèse

**H1 (principale).** Une politique entraînée avec géométrie **2.5D + postures**
survit mieux — et s'expose moins — sur des cartes urbaines 3D **tenues hors
entraînement**, qu'une politique entraînée sur géométrie **plate** (posture-aveugle),
**sans dégrader la mission** (neutralisation des défenseurs).

Prédiction directionnelle : `survie(B) > survie(A)` ET `exposition(B) < exposition(A)`,
avec `dkilled(B) >= dkilled(A)` (garde-fou anti-turtle : B ne doit pas juste se cacher).

---

## 2. Les deux bras (une seule variable change)

| Bras | Entraînement | Sémantique |
|---|---|---|
| **A — « avant » (baseline)** | géométrie **plate** : LOS binaire (tout bâtiment bloque), `postures=False` | l'état d'avant l'upgrade |
| **B — « après »** | **2.5D** (vraie `solidh`) + `postures=True` | l'upgrade complet |

- Bras A réalisé soit par un replica où `solidh` = constante haute (999 m → tout
  bâtiment bloque = ancienne sémantique binaire), soit par un flag `flat_los`.
- **Tout le reste identique** : même `curriculum_replica.py`, mêmes paliers, même
  budget (générations/PBT/K), mêmes cartes d'entraînement, mêmes graines.

> Limite assumée (§7) : l'A/B à 2 bras dit *si* l'upgrade aide, pas *quelle part*
> vient de la LOS vs des postures. Un 3ᵉ bras (2.5D **sans** postures) l'isolera plus tard.

---

## 3. Cartes — séparation entraînement / test (obligatoire)

- **Entraînement (4)** : `denver` `chicago` `paris` `madrid` — générées par `make_cities.sh`.
- **Test (3, DISJOINTES)** : `newyork` `london` `lille` — jamais vues à l'entraînement.
- **Test RELIEF (3, terrain vallonné, `--dem`)** : `athens` (Acropole +78 m) · `delphi` (Parnasse +264 m) · `santorini` (caldeira +218 m) — relief SRTM réel dans `elev` → teste le défilement de TERRAIN (crêtes) en plus du couvert bâti.
- La géométrie de test est **3D réelle** (verticalité active) pour **les deux bras**.
- Détail d'interface à l'éval : A tourne `postures=False` (subit la 3D, ne peut pas
  se baisser) ; B tourne `postures=True`. **Même terrain, B a la capacité en plus.**

---

## 4. Métriques (figées)

**Primaire :** taux de **survie** en fin d'épisode = `1 − losses` (moyenne sur les
cartes de test).

**Garde-fou (anti-turtle) :** `dkilled` (fraction de défenseurs neutralisés) — B ne
compte comme un succès que si `dkilled(B) >= dkilled(A)` (dans l'IC).

**Secondaires / mécanisme :**
- **temps d'exposition** = fraction de pas où l'agent vivant est en LOS d'un défenseur
  vivant à portée (à instrumenter dans l'éval, via `_losc`).
- **usage des postures** = fraction de pas accroupi/couché (depuis `env.posture`).
- **objectif** = taux de `neutralized` (tous défenseurs neutralisés).

**Qualitatif (jugement à l'œil) :** rejouer B sur **Arma** et filmer — le **défilement**
et le **couvert par posture** doivent se **voir**. C'est le juge final du réalisme.

---

## 5. Rigueur statistique

- **≥ 5 graines par bras** (viser 8–10). Graines figées, listées dans le rapport.
- Rapport : **moyenne ± IC bootstrap** par métrique, par bras.
- Test : IC **non chevauchants** sur la primaire, ou Mann-Whitney `p < 0.05`.
- Éval : **greedy** (argmax), mêmes cartes de test, `auto_reset=False`, N épisodes fixés.

---

## 6. Critère de succès (pré-enregistré)

**H1 est confirmée si, sur les cartes de test :**
1. `survie(B) − survie(A) >= +10 points` avec IC non chevauchants (ou MW p<0.05), **ET**
2. `dkilled(B) >= dkilled(A)` (dans l'IC — pas de sacrifice de mission), **ET**
3. `exposition(B) < exposition(A)`.

Si (1) tient mais pas (2) → B **turtle** (se cache au prix de la mission) = résultat
à documenter, pas un succès de H1.
Si aucun écart → l'upgrade 3D n'aide pas la performance (mais peut aider le réalisme
à l'œil) = résultat honnête à publier tel quel.

---

## 7. Ce que l'expérience N'établit PAS (honnêteté)

- Ne sépare pas l'effet **LOS-verticale** de l'effet **postures** → 3ᵉ bras ultérieur.
- Un seul générateur de cartes (OSM) = un domaine ; la généralisation à d'autres
  villes/pays est une question distincte.
- Environnement libre (sandbox) : **Arma reste une validation qualitative**, hors de
  la chaîne de preuve (fermé, non reproductible, EULA).

---

## 8. Procédure d'exécution (rappel)

1. Geler ce fichier (commit) **avant** de lancer.
2. Générer les cartes train + test (disjointes).
3. Entraîner A et B (mêmes graines, même budget).
4. Évaluer A et B sur les cartes de **test**, collecter les métriques (≥5 graines).
5. Rapporter moyenne ± IC + verdict vs §6.
6. Filmer B sur Arma (juge à l'œil).
