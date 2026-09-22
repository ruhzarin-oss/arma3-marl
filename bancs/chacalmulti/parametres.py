"""Ecrit server_multi.cfg : la classe Params entiere, reecrite a chaque episode.

Usage : parametres.py <server.cfg source> <server_multi.cfg> <job.json> <episode>
Les parametres communs ont les noms et les valeurs par defaut du lanceur du banc seul ( bancs/chacaloracle/lancer.sh ) ;
chaque cellule en surcharge quelques-uns. Refuse un job dont une cellule demande un parametre non surchargeable.
"""
import json, re, sys

src, dst, jobf, ep = sys.argv[1:5]
j = json.load(open(jobf))
# nom du job -> ( parametre de mission, defaut ) : la table du lanceur du banc seul, dans son ordre
COMMUNS = [("palier", "PALIER", 0), ("depart", "DEPART", 1), ("immortel", "IMMORTEL", 0), ("jour", "JOUR", 0),
           ("echelle", "ECHELLE", 100), ("dtcs", "DTCS", 100), ("placeur", "PLACEUR", 0), ("banc_appui", "BANC_APPUI", 0),
           ("ablation", "ABLATION", 0), ("socle", "SOCLE", 0), ("azimut", "AZIMUT", 0), ("geometrie", "GEOMETRIE", 0),
           ("obs", "OBS", 1), ("azimut_val", "AZIMUT_VAL", 0), ("exfil", "EXFIL", 0), ("tactique", "TACTIQUE", 0),
           ("oracle", "ORACLE", 0), ("mg_assaut", "MG_ASSAUT", 0), ("delai_porteur", "DELAI_PORTEUR", 45),
           ("appui_fixe", "APPUI_FIXE", 0), ("feu_avant", "FEU_AVANT", 0), ("appui_feu", "APPUI_FEU", 0),
           ("effectif", "EFFECTIF", 10), ("accessible", "ACCESSIBLE", 0), ("tenir", "TENIR", 0), ("hmg", "HMG", -1),
           ("assaut_x", "ASSAUT_X", 100), ("arret", "ARRET", 6), ("partage", "PARTAGE", 0), ("qrf_n", "QRF_N", -1),
           ("qrf_delai", "QRF_DELAI", -1), ("qrf_dist", "QRF_DIST", -1), ("acc", "ACC", 1), ("situation", "SITUATION", 0),
           ("menace_p1", "MENACE_P1", 0), ("menace_p2", "MENACE_P2", 0), ("menace_p3", "MENACE_P3", 0),
           ("menace_p4", "MENACE_P4", 0), ("menace_p5", "MENACE_P5", 0), ("menace_p6", "MENACE_P6", 0),
           ("p1_attente", "P1_ATTENTE", 0), ("traversee", "TRAVERSEE", 0), ("obs_duree", "OBS_DUREE", 0),
           ("itineraire", "ITINERAIRE", 0), ("avant", "AVANT", 260), ("oracle_cmd", "ORACLE_CMD", 0),
           ("oracle_b", "ORACLE_B", 6), ("oracle_nu", "ORACLE_NU", 15), ("oracle_eps", "ORACLE_EPS", 15),
           ("oracle_delta", "ORACLE_DELTA", 60), ("oracle_ctrl", "ORACLE_CTRL", 0), ("portee_son", "PORTEE_SON", 600),
           ("sonde_perception", "SONDE_PERCEPTION", 0), ("balayage", "BALAYAGE", 0), ("observation", "OBSERVATION", 0),
           ("controle_perception", "CONTROLE_PERCEPTION", 0), ("sonde", "SONDE", 0), ("attente_test", "ATTENTE_TEST", 0),
           ("controle_dist", "CONTROLE_DIST", 150), ("delai_mode", "DELAI_MODE", 0), ("f_len", "F_LEN", 0)]
PAR_CELLULE = ["GRAINE", "GRAINE_HAUT", "SITUATION", "MENACE_P2", "TRAVERSEE", "PALIER", "EFFECTIF", "AVANT",
               "OBSERVATION", "QRF_N", "QRF_DELAI", "HMG", "PORTEE_SON", "BALAYAGE", "ORACLE_CMD", "ORACLE_CTRL", "ORACLE_B",
               "ORACLE_NU", "ORACLE_EPS", "ORACLE_DELTA", "SITE_X", "SITE_Y"]
KMAX = 8

P = {}
bras = j.get("bras", "PLAN")
if bras not in ("PLAN", "NUL"): sys.exit(f"job invalide : bras {bras}")
P["CHACAL_BRAS"] = 0 if bras == "PLAN" else 1
P["CHACAL_GRAINE"] = 0; P["CHACAL_GRAINE_HAUT"] = 0
for cle, nom, d in COMMUNS: P["CHACAL_" + nom] = int(j.get(cle, d))
for k in range(32): P[f"CHACAL_F{k}"] = int(j.get(f"f{k}", 0))
cellules = j["episodes"][str(ep)]
if not (1 <= len(cellules) <= KMAX): sys.exit(f"episode {ep} : {len(cellules)} cellules, 1 a {KMAX} permises")
P["MULTI_K"] = len(cellules)
P["MULTI_TMAX"] = int(j.get("multi_tmax", 1200))
P["MULTI_SONDE"] = int(j.get("multi_sonde", 1))
P["MULTI_ESPACEMENT"] = int(j.get("multi_espacement", 3000))
P["MULTI_ESPACEMENT_MIN"] = int(j.get("multi_espacement_min", 2000))
for k in range(1, KMAX + 1):
    for x in PAR_CELLULE: P[f"MULTI_C{k}_{x}"] = -999999
for k, c in enumerate(cellules, start=1):
    if "graine" not in c: sys.exit(f"cellule {k} sans graine")
    for cle, v in c.items():
        if cle in ("note", "role", "attendu", "origine", "version"): continue
        if cle.upper() not in PAR_CELLULE: sys.exit(f"cellule {k} : {cle} n est pas surchargeable par cellule")
        P[f"MULTI_C{k}_{cle.upper()}"] = int(v)
    P[f"MULTI_C{k}_GRAINE_HAUT"] = 0     # la graine de la cellule est ecrite ENTIERE dans GRAINE

cfg = open(src, encoding="utf-8", errors="strict").read()
cfg, n = re.subn(r'template = "[A-Za-z0-9_]+\.Altis";', 'template = "CHACALMULTI.Altis";', cfg)
if n != 1: sys.exit(f"server.cfg : {n} lignes template, 1 attendue")
m = re.search(r"class Params \{.*?\n(\s*)\};", cfg, re.S)
if not m: sys.exit("server.cfg sans class Params")
ind = m.group(1) + "    "
corps = "class Params {\n" + "".join(f"{ind}{k} = {v};\n" for k, v in P.items()) + m.group(1) + "};"
cfg = cfg[:m.start()] + corps + cfg[m.end():]
open(dst, "w", encoding="utf-8").write(cfg)
print(f"{len(P)} parametres ecrits dans {dst}")
print("communs : " + " ".join(f"{k[7:]}={v}" for k, v in P.items() if k.startswith("CHACAL_") and not re.match(r"CHACAL_F\d", k)))
for k, c in enumerate(cellules, start=1):
    print(f"cellule {k} : " + " ".join(f"{x}={P[f'MULTI_C{k}_{x}']}" for x in PAR_CELLULE if P[f"MULTI_C{k}_{x}"] != -999999))
