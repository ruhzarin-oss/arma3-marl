#!/usr/bin/env python3
"""Branche L AUTRE MOITIE (la loi de tir) dans assault_terrain.py.
Cinq ancres exactes, sauvegarde `.avanttir`, refus si une ancre a bouge.
Tout est sous le meme drapeau `canal_cwr` : eteint par defaut, `MONDE_ARMA` ne bouge pas."""
import sys, shutil
P = "/home/younes/arma3-marl/assault_terrain.py"
s = open(P, encoding="utf-8").read()
if "canal_mem_pas" in s:
    print("  DEJA BRANCHE — rien fait."); sys.exit(0)
if "self.canal = None" not in s:
    sys.exit("l equation 1 n est pas branchee — jouer patch_eq1.py d abord")

A = [
# ── 1. les deux durees, converties en pas, et le refus du doublon ───────────────
("""            if not self.cible_unique:
                raise ValueError("canal_cwr remplace la porte de designation de `cible_unique` : "
                                 "l activer sans cible_unique ne changerait rien (module inerte)")""",
 """            if not self.cible_unique:
                raise ValueError("canal_cwr remplace la porte de designation de `cible_unique` : "
                                 "l activer sans cible_unique ne changerait rien (module inerte)")
            # ─── L AUTRE MOITIE : LES DEUX HORLOGES DE LA LOI DE TIR ───
            # Arma compte en SECONDES, le gymnase en PAS : aucune duree ne se recopie.
            self.canal_mem_pas = _CANAL.en_pas(_CANAL.MEM_TIR_S, sec_par_pas)       # 10 s
            self.canal_verrou_pas = _CANAL.en_pas(_CANAL.FIRE_VALID_S, sec_par_pas)  # 15 s
            # `feu_sur_connu` etait une FRACTION libre a calibrer. La source dit que ce
            # n en est pas une : c est une FENETRE de 10 s. Deux mecanismes pour une seule
            # grandeur, c est le mode d echec de la calibration marginale.
            if self.feu_sur_connu > 0.0:
                raise ValueError(
                    "canal_cwr REMPLACE `feu_sur_connu` : la source en fait une fenetre de "
                    "%.0f s (%d pas), pas une fraction. Mettre feu_sur_connu=0.0."
                    % (_CANAL.MEM_TIR_S, self.canal_mem_pas))
            if self.feu_de_zone > 0.0:
                # `posError > 2*indirectHitRange` ecarte l arme : pour un FUSIL (rayon ~0)
                # une position connue a l oreille est INTIRABLE. Le feu de zone n existe
                # donc que pour une arme a rayon d effet — que le gymnase ne modelise pas.
                raise ValueError(
                    "canal_cwr : `feu_de_zone` n est licite que pour une arme A RAYON D EFFET "
                    "(la source ecarte l arme si posError > 2*indirectHitRange). Le gymnase "
                    "n en modelise aucune : mettre feu_de_zone=0.0")"""),

# ── 2. les tampons : derniere vue par attaquant, cible et verrou par defenseur ──
("""            # cliquet PAR ATTAQUANT : a-t-il deja ete vu ? monotone, comme l alerte de camp.
            self.a_connu = torch.zeros(N, A, device=d)""",
 """            # cliquet PAR ATTAQUANT : a-t-il deja ete vu ? monotone, comme l alerte de camp.
            self.a_connu = torch.zeros(N, A, device=d)
            # ─── LOI DE TIR : `lastSeen` (par ATTAQUANT, partage par le groupe defenseur,
            # comme le `Target` de RV1 qui est porte par l AIGroup) et le verrou de cible
            # (par DEFENSEUR). -1e9 = jamais vu, et ce n est pas 0 : au pas 0 un homme
            # jamais vu serait « vu a l instant ».
            self.a_dernier_vu = torch.full((N, A), -1e9, device=d)
            self.d_cible = torch.full((N, D), -1, dtype=torch.long, device=d)
            self.d_verrou = torch.zeros(N, D, dtype=torch.long, device=d)"""),

# ── 3. remise a zero ───────────────────────────────────────────────────────────
("""        if hasattr(self, 'a_connu'):
            self.a_connu[idx] = 0.0""",
 """        if hasattr(self, 'a_connu'):
            self.a_connu[idx] = 0.0
        if hasattr(self, 'a_dernier_vu'):
            self.a_dernier_vu[idx] = -1e9
            self.d_cible[idx] = -1
            self.d_verrou[idx] = 0"""),

# ── 4. la selection : fenetre de 10 s + verrou de 15 s ─────────────────────────
("""            if self.cible_unique:
                _porte = (self._canal_out["designe"] if self.canal is not None else (los > 0.5))
                _elig = (active > 0) & _porte & self._aalive()
                if self.courbe is None:                    # sans courbe, la portee est un mur
                    _elig = _elig & (dist < self.fire_range)
                _INF = torch.full_like(dist, float("inf"))
                _k = torch.where(_elig, dist, _INF).argmin(1, keepdim=True)
                _sel = torch.zeros_like(active).scatter_(1, _k, 1.0) * _elig.float()
                tir = active * _sel""",
 """            if self.cible_unique:
                _porte = (self._canal_out["designe"] if self.canal is not None else (los > 0.5))
                _elig = (active > 0) & _porte & self._aalive()
                if self.canal is not None:
                    # ─── LA FENETRE DE 10 s. `lastSeen` se met a jour sur la VUE
                    # GEOMETRIQUE du pas ; ensuite l homme reste tirable 10 s, puis plus.
                    # Ce n est pas le cliquet eternel de `a_connu` : la source coupe.
                    _frais = ((self.t.unsqueeze(1).float() - self.a_dernier_vu)
                              <= float(self.canal_mem_pas))
                    _visible_ok = self._canal_out["designe"] | (_frais & (self.a_dernier_vu > -1e8))
                    _elig = (active > 0) & _visible_ok & self._aalive()
                if self.courbe is None:                    # sans courbe, la portee est un mur
                    _elig = _elig & (dist < self.fire_range)
                _INF = torch.full_like(dist, float("inf"))
                _k = torch.where(_elig, dist, _INF).argmin(1, keepdim=True)
                if self.canal is not None:
                    # ─── LE VERROU DE 15 s (`FireValidTime`). Le defenseur RESTE sur sa
                    # cible tant qu elle vit et reste eligible ; il ne re-choisit pas le
                    # plus proche a chaque pas. C est ce verrou qui fait qu un flanqueur
                    # isole encaisse tout, au lieu d etre relache au pas suivant.
                    _anc = self.d_cible[:, di:di + 1]                      # (N,1)
                    _a_valide = (_anc >= 0)
                    _ok_anc = torch.zeros_like(_a_valide)
                    if bool(_a_valide.any()):
                        _idx = _anc.clamp(min=0)
                        _ok_anc = _a_valide & (self.d_verrou[:, di:di + 1] > 0) \\
                                  & torch.gather(_elig, 1, _idx)
                    _k = torch.where(_ok_anc, _anc, _k)
                    _neuf = _elig.any(1, keepdim=True) & ~_ok_anc
                    self.d_cible[:, di:di + 1] = torch.where(
                        _neuf, _k, torch.where(_ok_anc, _anc, torch.full_like(_anc, -1)))
                    self.d_verrou[:, di:di + 1] = torch.where(
                        _neuf, torch.full_like(_anc, self.canal_verrou_pas),
                        (self.d_verrou[:, di:di + 1] - 1).clamp(min=0))
                _sel = torch.zeros_like(active).scatter_(1, _k, 1.0) * _elig.float()
                tir = active * _sel"""),

# ── 5. les degats : le couvert AU CARRE + les deux portes ──────────────────────
("""                    _p = self._p_balle(dist) * self.tir_par_pas * self.degat_par_impact
                    dmg_a += _p * efrac * tir""",
 """                    if self.canal is not None:
                        # ⭐ LA LOI DE TIR. Avant : `_p * efrac` — le couvert LINEAIRE, et
                        # aucun plancher. La source : `hitProbab *= Square(visible)`, puis
                        # rien si `visible < 0.63`, puis rien si `hitProbab < 0.05`.
                        _pb = self._CANAL.tir(self._p_balle(dist), efrac)
                        _p = _pb * self.tir_par_pas * self.degat_par_impact
                        dmg_a += _p * tir
                    else:
                        _p = self._p_balle(dist) * self.tir_par_pas * self.degat_par_impact
                        dmg_a += _p * efrac * tir"""),

# ── 6. `lastSeen` se met a jour la ou la vue geometrique est deja relevee ──────
("""            self._vu_geo = torch.maximum(self._vu_geo, (los > 0.5).float() * _viv)""",
 """            self._vu_geo = torch.maximum(self._vu_geo, (los > 0.5).float() * _viv)
            if self.canal is not None:
                # `lastSeen` de RV1 : porte par le groupe, donc par ATTAQUANT et non par
                # couple (defenseur, attaquant). Mis a jour sur la vue geometrique du pas.
                _vu_ici = ((los > 0.5) & (_viv > 0))
                self.a_dernier_vu = torch.where(_vu_ici, self.t.unsqueeze(1).float(),
                                                self.a_dernier_vu)"""),
]

for i, (old, new) in enumerate(A, 1):
    n = s.count(old)
    if n != 1:
        sys.exit("ANCRE %d introuvable ou ambigue (%d occurrences) — RIEN N EST ECRIT.\n---\n%s" % (i, n, old[:220]))
    s = s.replace(old, new)

shutil.copy2(P, P + ".avanttir")
open(P, "w", encoding="utf-8").write(s)
print("  6 ancres appliquees. Sauvegarde : assault_terrain.py.avanttir")
