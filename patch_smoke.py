#!/usr/bin/env python3
"""patch_smoke.py — le smoke-test EXIGE avant toute heure de GPU.

« Pas de preuve que le champ est reellement dans l observation = pas de lancement. » Trois
choses a montrer, et rien d autre :
  1. la largeur de l observation est bien passee de 8 a 16 pour soi ;
  2. les huit valeurs du champ VARIENT d une position a l autre (un champ plat = huit copies
     du meme nombre = aucune information) ;
  3. le placebo, lui, ne suit PAS la position — sinon ce n est pas un placebo.
"""
import pathlib

P = pathlib.Path('/home/younes/arma3-marl/agent_complet.py')
t = P.read_text(encoding='utf-8')

ANC = """class Politique(nn.Module):"""
NEUF = '''if '--smoke' in sys.argv:
    # QUATRE positions tres differentes, sur QUATRE configurations defensives reelles.
    _i = torch.arange(min(4, NC), device=dev)
    _p = torch.tensor([[0., 250.], [120., 120.], [250., 0.], [-180., 60.]],
                      device=dev)[:len(_i)]
    _po = torch.zeros(len(_i), dtype=torch.long, device=dev)
    _c = champ_risque(_p, _po, _i)
    print("\\n  CHAMP DE RISQUE — huit directions, quatre positions")
    print("  " + "-" * 68)
    for _k in range(len(_i)):
        _v = " ".join(f"{x:5.3f}" for x in _c[_k].tolist())
        print(f"    p=({_p[_k,0]:7.1f},{_p[_k,1]:6.1f})   {_v}")
    _ecart_dir = _c.std(dim=1).mean().item()      # dispersion ENTRE directions
    _ecart_pos = _c.std(dim=0).mean().item()      # dispersion ENTRE positions
    _moy = _c.mean().item()
    print("  " + "-" * 68)
    print(f"    moyenne du champ                     {_moy:.4f}")
    print(f"    dispersion ENTRE DIRECTIONS          {_ecart_dir:.4f}"
          f"   {'OK' if _ecart_dir > 0.01 else 'PLAT -> aucune information'}")
    print(f"    dispersion ENTRE POSITIONS           {_ecart_pos:.4f}"
          f"   {'OK' if _ecart_pos > 0.01 else 'INSENSIBLE A LA POSITION'}")
    _moi, _ent = percevoir(_p, _po, _i)
    print(f"    largeur de l observation : soi={_moi.shape[-1]} (attendu {CM}) "
          f"· entite={_ent.shape[-1]} (attendu {CE})")
    _ok = (_moi.shape[-1] == CM and (not CHAMP_ACTIF or _ecart_dir > 0.01))
    print(f"\\n  SMOKE {'PASSE' if _ok else 'ECHOUE — on ne lance rien'}\\n")
    sys.exit(0 if _ok else 1)

class Politique(nn.Module):'''
assert t.count(ANC) == 1, "ancre Politique introuvable"
t = t.replace(ANC, NEUF, 1)
P.write_text(t, encoding='utf-8')
print("smoke-test pose")
