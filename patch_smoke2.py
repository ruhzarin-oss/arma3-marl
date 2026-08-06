#!/usr/bin/env python3
"""patch_smoke2.py — ORDRE 8c : le smoke doit passer A TOUTES LES DISTANCES du trajet.

« Le seuil reste 0,010, inchange, et le critere redepose exige la dispersion au-dessus de
 0,010 A TOUTES LES DISTANCES du trajet, pas seulement en moyenne. Ta table dit que ca passe ;
 le smoke doit le confirmer sur la machine, pas sur la table. »

Et cinq graines au lieu de trois : « 2 sur 3 » s ouvrait tout seul une fois sur cinq.
"""
import pathlib, re

P = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = P.read_text(encoding='utf-8')

# --- le smoke, refait : toutes les distances, seuil intact
i = t.index("if '--smoke' in sys.argv:")
j = t.index("class Politique(nn.Module):")
NEUF = '''if '--smoke' in sys.argv:
    # LE SEUIL NE BOUGE PAS : 0,010 de dispersion entre les huit directions. Ce qui change,
    # c est l exigence — il doit etre franchi A CHAQUE DISTANCE du trajet, pas en moyenne.
    # Un champ qui ne parle qu au but est un champ qui parle trop tard.
    _SEUIL = 0.010
    _B = 512
    _idx = torch.randint(0, NC, (_B,), device=dev)
    _po = torch.zeros(_B, dtype=torch.long, device=dev)
    print(f"\\n  SMOKE — champ de risque, portee {PORTEE_CHAMP:.0f} m"
          f"{' (PLACEBO : bruit)' if CHAMP_PLACEBO else ''}")
    print("  " + "-" * 68)
    _tout = True
    for _d in (40, 60, 90, 120, 160, 200, 250):
        _a = torch.rand(_B, device=dev) * 2 * math.pi
        _p = torch.stack([torch.sin(_a), torch.cos(_a)], -1) * _d
        _c = champ_risque(_p, _po, _idx)
        _disp = _c.std(dim=1).mean().item()
        _ok = _disp > _SEUIL
        _tout &= _ok
        print(f"    a {_d:3d} m de l objectif   dispersion {_disp:.4f}   "
              f"{'OK' if _ok else 'MORD — le champ est plat ici'}")
    _moi, _ent = percevoir(_p, _po, _idx)
    _larg = (_moi.shape[-1] == CM and _ent.shape[-1] == CE)
    print("  " + "-" * 68)
    print(f"    largeur de l observation : soi={_moi.shape[-1]} (attendu {CM})"
          f" · entite={_ent.shape[-1]} (attendu {CE})   {'OK' if _larg else 'ECHEC'}")
    print(f"\\n  SMOKE {'PASSE — lancement autorise' if (_tout and _larg) else 'MORD — on ne lance rien'}\\n")
    sys.exit(0 if (_tout and _larg) else 1)

'''
t = t[:i] + NEUF + t[j:]

# --- cinq graines, succes a 4 sur 5 (addendum du 06/08 sur la taille de la porte)
A = "GRAINES = (1,) if COURT else (1, 2, 3)"
N = ("# CINQ graines, pas trois. « 2 sur 3 » s ouvrait tout seul une fois sur cinq : ce n etait\n"
     "# pas une porte. A 4 sur 5, le hasard ne passe que 3 fois sur 100.\n"
     "GRAINES = (1,) if COURT else (1, 2, 3, 4, 5)")
assert t.count(A) == 1, "ancre GRAINES introuvable"
t = t.replace(A, N, 1)

P.write_text(t, encoding='utf-8')
print("smoke a toutes les distances + 5 graines")
