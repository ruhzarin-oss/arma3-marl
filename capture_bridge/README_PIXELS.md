# Pixel + état — pont de capture (mis en place le 31/08/2026)

Contexte : Fable a rendu un NO-GO argumenté le 25/08 sur les pixels dans Arma
(voir mémoire `pixels-arma-verdict-fable-nogo`). Younes a tranché le 31/08 :
on le fait quand même. Ce dossier construit la machinerie ; **rien ici n'est
un verdict** — au sens du `CLAUDE.md` du projet, une machinerie qui tourne
n'est pas un progrès tant qu'elle n'a pas produit une mesure sur le vrai Arma.

## Ce qui est fait (auto-testé hors-ligne, PAS mesuré sur Arma vivant)
- `fusion_net.py` — `NetFusion` : encodeur image (CNN léger, ~embed 32) fusionné
  en fin de vecteur d'état (20 dims + flag `has_pixel`), mêmes têtes pi/v que
  `Net` existant. `has_pixel=0` neutralise bien l'embedding (testé).
- `capture_receiver.py` — serveur TCP côté WSL, garde le DERNIER cadre (pas de
  file), expose `get_latest(max_age_s)`. Round-trip testé en local (127.0.0.1).
- `capture_bridge.py` — **doit tourner côté Windows natif**, pas WSL : c'est le
  seul endroit où le rendu GPU d'Arma existe. Capture DXGI (`dxcam`) de la
  fenêtre client + état clavier/souris par polling (`pywin32`), envoie vers
  `capture_receiver.py`. Non testé (pas de fenêtre Arma rendue disponible
  pendant cette session).
- `freshness_bench.sqf` + `freshness_detect.py` — l'instrument que Fable a
  explicitement demandé AVANT de faire confiance à un cadre capturé : un
  panneau blanc bascule à un instant serveur connu, on mesure quand ça
  apparaît réellement dans le flux capturé. Logique de détection auto-testée
  avec un retard injecté connu (180 ms retrouvé à <40 ms près) et un contrôle
  négatif (aucun flash → banc jugé EN PANNE, pas un faux verdict).

## Ce qui N'EST PAS fait
- **Aucune mesure de fraîcheur réelle.** Le critère de Fable (p95 ≤ 500 ms,
  20/20 flashes détectés) n'a pas été évalué sur le vrai pont. Tant que ce
  n'est pas fait, `has_pixel` ne devrait pas être fait confiance en
  entraînement — le risque nommé par Fable (le client rend une réplique en
  retard réseau, l'IA décide sur l'état serveur) n'est toujours qu'un risque.
- **Pas de branchement live** dans `harmattan_actuator_native.sqf` ni dans
  `arma_couture.py` (parse_obs reste 20-dim, pas de canal image). Volontaire :
  ça touche un pont utilisé par des serveurs en cours (`hmtbanc`, `hmtech0-2`
  tournaient au moment de cette session) — le branchement doit être fait à
  froid, pas à chaud sur une expérience en cours.
- **Pas d'actor-critic asymétrique** (Dactyl : critique sur état privilégié
  seul, acteur sur pixels+état). `NetFusion` est symétrique pour l'instant —
  c'est un axe documenté, pas construit, cf. `fusion_net.py`.
- **`capture_bridge.py` jamais lancé contre un vrai client Arma.** Dépendances
  (`dxcam`, `pywin32`) pas encore installées côté Windows natif.

## Prochaine étape concrète, dans l'ordre
1. Installer `dxcam pywin32 numpy` dans un venv Windows natif dédié (PAS
   l'env `se1` de SolarEndure — projet différent).
2. Lancer un client Arma RENDU (Preview/host, pas un dédié `hmtbanc` — ceux-là
   n'ont pas de fenêtre) et vérifier que `capture_bridge.py` trouve la fenêtre
   et envoie des cadres à `capture_receiver.py` (compter `n_recv` qui avance).
3. Charger `freshness_bench.sqf` sur ce client SEUL (pas sur un serveur en
   production), mesurer médiane/p95 avec `freshness_detect.py` branché en
   direct — c'est la première vraie mesure de cette histoire.
4. Seulement si le p95 passe : brancher `has_pixel`/l'image dans
   `arma_couture.py` et `harmattan_actuator_native.sqf`, sur une copie de
   mission dédiée, pas sur `BancLive.Stratis` tel quel.

## Réseau
WSL (ce host, au 31/08) : `172.31.53.160`. NAT WSL2 standard : Windows → WSL
sur cette IP fonctionne directement. Cette IP est dynamique (change au
redémarrage) — vérifier avec `ip addr show eth0` dans WSL avant de lancer
`capture_bridge.py --host <ip>`.
