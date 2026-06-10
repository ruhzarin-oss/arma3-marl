# Bilan de la nuit — 10/06 (01:00 → 09:00)

## TL;DR
**La question pivot est tranchée, et la réponse est OUI** : la meilleure manœuvre **dépend** de la défense → l'officier‑sélecteur est justifié (modérément). **Mais** un coût pathologique imprévu (les ops M3‑vs‑défense‑réactive grindent 3–7 h chacune) a mangé toute la nuit sur cette seule confirmation : la matrice et les étapes suivantes n'ont **pas** tourné.

## Le résultat scientifique (Gate 0, confirmé n=32)
| | vs `skilled` (passif) | vs `skilled_react` (intelligent) |
|---|---|---|
| **M1 frontal** | 50 % | **34.4 %** (11/32) |
| **M3 enveloppement** | **62.5 %** | 21.9 % (7/32) |
| **champion** | **M3** | **M1** |

- **Le champion change avec la défense** → un sélecteur a un sens → **officier justifié.**
- **Effet différentiel robuste** : la défense réactive coûte **−40.6 pts à M3** vs **−15.6 pts à M1** (punit l'enveloppement 2.6× plus que le frontal). C'est la signature solide.
- **Magnitude modérée** : l'écart M1>M3 vs réactif = 12.5 pts (4 ops/32). Plus solide que le faux‑positif disperse (1 op), mais pas écrasant.
- **Ta thèse validée** : c'est l'**adaptation de l'ennemi** (pas la géométrie ni la difficulté) qui crée le besoin de choisir. La géométrie statique, même adversariale, n'avait rien donné ; un ennemi qui *réagit* casse la suprématie de l'enveloppement.

## L'incident (à corriger)
- Les ops **M3 vs réactif** durent en moyenne **3.5 h** (max **7.4 h**) contre ~11 min normalement : le standoff enveloppement‑vs‑réserve fait ramer le serveur (steps ~50 s au lieu de ~10 s).
- Conséquence : la confirmation n=32 a tourné **01:21 → 09:00** et a consommé la nuit entière. **Matrice / valeur‑de‑sélection / mesure de la 2ᵉ défense : non faites.**
- **Ma faute de process** : j'aurais dû borner le temps d'op (max_steps plus bas en réactif, ou abort rapide d'un enveloppement enlisé) AVANT de lancer, et le moniteur aurait dû couper le grind. Je l'ai laissé courir.

## Fait cette nuit
- ✅ `skilled_react` (défense coordonnée anti‑flanc) — bâtie, smoke OK, **confirmée n=32**.
- ✅ `skilled_react_depth` (défense anti‑frontale) — bâtie, câblée, import OK — **pas encore smokée/mesurée**.
- ✅ `--seed_base` (append‑only propre pour n=32) ajouté à run_maneuver.
- ✅ 3090 capée 315 W (règle posée), journal à jour, rien de cassé (16 serveurs up, GPU idle).

## Reco pour aujourd'hui (par ordre)
1. **Fixer le coût d'abord** : borner les ops réactives (ex. `max_steps` 250 + abort « enlisement » rapide) → une op réactive doit coûter ~10 min, pas 7 h. Sans ça, aucune matrice n'est faisable.
2. **Puis la matrice** M1/M2/M3/M5 × {passif, anti‑flanc, anti‑centre} en n=16 borné (~2 h) → prouver le pierre‑feuille‑ciseaux complet, pas juste une inversion.
3. **Le vrai prix** = ta « axe défense vs axe attaque » avec un **défenseur qui APPREND** (RL self‑play, GPU/archi). L'inversion confirmée le justifie maintenant : il existe des défenses qui battent l'enveloppement → un défenseur appris en trouvera d'autres, et la co‑évolution donnera la vraie matrice de jeu.

## Ammo (archi)
`eval_ammo` n'a toujours pas produit de sortie ; checkpoints `kothammo_rare_*` + `abond` présents. La 3090 est capée et idle. À l'archi de sortir le verdict ingéniosité.
