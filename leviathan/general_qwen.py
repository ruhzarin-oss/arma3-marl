#!/usr/bin/env python3
"""general_qwen.py - le GENERAL de leviathan001. Qwen (inference Ollama) lit la SITUATION
du pays par secteur (via le pont FOB) et emet des ORDRES abstraits (TENIR/MASSER/REPLIER).
Sort general_orders.json -> lu par fob_driver. Pas d'entrainement : raisonnement zero-shot."""
import json, re, os, time, argparse, urllib.request

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
BRIDGE = MIS + "/hmt_bridge"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
ORDERS = "/home/younes/arma3-marl/leviathan/general_orders.json"
OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"

SECTORS = [("Mike26", 4279, 3856), ("AirBase", 2050, 5700), ("Maxwell", 3253, 2984), ("Kamino", 6544, 4863),
           ("Rogain", 4886, 5948), ("AgiaMarina", 2915, 6165), ("Tempest", 1942, 3557), ("OldOutpost", 4319, 4398),
           ("LZBaldy", 4604, 5284), ("MilRange", 3338, 5744), ("AgiosIoannis", 3027, 2184), ("Tsoukalia", 4206, 2715),
           ("Girna", 1935, 2723), ("KaminoFR", 6402, 5427), ("LZConnor", 2979, 1860), ("AgiosCephas", 2719, 1712),
           ("Strogos", 2024, 1790), ("Keiros", 6157, 4349), ("Limeri", 5440, 3687), ("Nisi", 1784, 4134),
           ("Kyfi", 1790, 3512), ("MarinaBay", 2648, 5990), ("Tsoukala", 4241, 2498), ("KaminoCoast", 5691, 6124), ("GirnaBay", 1845, 2656)]

SYS = ("Tu es le GENERAL qui commande l'armee d'un pays en paix mais sous menace possible. "
       "Pour CHAQUE secteur tenu tu donnes un ordre : TENIR (defense normale), MASSER (concentrer du renfort vers une menace proche), "
       "REPLIER (si intenable). En paix sans ennemi : TENIR partout. Si un secteur a un ENNEMI proche, fais MASSER les secteurs VOISINS dessus. "
       "Indique aussi un FOCUS : le NOM du secteur menace sur lequel concentrer les renforts (celui qui a un ENNEMI), ou null s'il n'y a aucune menace. "
       'Sois sobre. Reponds en JSON STRICT : {"ordres":{"<secteur>":"TENIR|MASSER|REPLIER"}, "focus":"<nom du secteur menace ou null>", "intention":"<1 phrase>"}.')

WORLD_F = "/home/younes/arma3-marl/leviathan/world_state.json"


def secs_arr():
    return "[" + ",".join("[%d,%d]" % (x, y) for _, x, y in SECTORS) + "]"


SIT_SQF = ('private _secs = ' + secs_arr() + ';\n'
           'private _out = "";\n'
           '{ private _s = _x;\n'
           '  private _own = {alive _x && side _x==east && (_x distance2D _s)<200} count allUnits;\n'
           '  private _en = allUnits select {alive _x && side _x!=east && side _x!=civilian && (east knowsAbout _x>1) && (_x distance2D _s)<450};\n'
           '  private _ed = if (count _en>0) then { round (_s distance2D (_en select 0)) } else { -1 };\n'
           '  _out = _out + format ["%1,%2;", _own, _ed];\n'
           '} forEach _secs;\n'
           'diag_log format ["HARMATTAN_SIT alert=%1 | %2", HMT_ALERT, _out];\n')


def next_n():
    ns = [int(re.match(r"cmd_(\d+)\.sqf", f).group(1)) for f in os.listdir(BRIDGE) if re.match(r"cmd_(\d+)\.sqf", f)]
    return (max(ns) + 1) if ns else 1


def query(sqf, marker, settle=2.5):
    n = next_n()
    p = "%s/cmd_%d.sqf" % (BRIDGE, n)
    with open(p + ".tmp", "w") as f:
        f.write(sqf)
    os.replace(p + ".tmp", p)
    time.sleep(settle)
    ls = [l for l in open(LOG, errors="ignore").read().splitlines() if marker in l]
    return ls[-1] if ls else None


def read_situation():
    # 1) si le DRIVER expose l'etat (frais < 30s) -> on le lit (le driver reste seul maitre du pont)
    try:
        d = json.load(open(WORLD_F))
        if time.time() - d.get("ts", 0) < 30:
            rows = [(r[0], int(r[1]), int(r[2])) for r in d["rows"]]
            alert = "1" if any(r[2] >= 0 for r in rows) else "0"
            return alert, rows
    except Exception:
        pass
    # 2) sinon (mode standalone) -> requete directe du pont
    line = query(SIT_SQF, "HARMATTAN_SIT")
    if not line:
        return None, None
    alert = re.search(r"alert=(\S+)", line).group(1)
    payload = line.split("|", 1)[1].strip().strip('"')
    cells = [c for c in payload.split(";") if "," in c]
    rows = []
    for (name, _, _), c in zip(SECTORS, cells):
        own, ed = c.split(",")[:2]
        rows.append((name, int(own), int(ed)))
    return alert, rows


def situation_text(alert, rows):
    lines = ["Alerte pays: %s" % alert]
    for name, own, ed in rows:
        menace = ("ENNEMI a %dm" % ed) if ed >= 0 else "calme"
        lines.append("  - %-13s : %3d hommes | %s" % (name, own, menace))
    return "\n".join(lines)


def ask_general(sit):
    body = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.2},
                       "messages": [{"role": "system", "content": SYS},
                                    {"role": "user", "content": "Situation du pays par secteur :\n" + sit + "\n\nTes ordres ?"}]}).encode()
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    return json.loads(json.load(urllib.request.urlopen(req, timeout=180))["message"]["content"])


def cycle():
    alert, rows = read_situation()
    if rows is None:
        print("[general] pas de situation (pont ?)")
        return
    sit = situation_text(alert, rows)
    print("=" * 60)
    print("SITUATION lue par le general :")
    print(sit)
    ans = ask_general(sit)
    json.dump({"ts": time.time(), "alert": alert, **ans}, open(ORDERS, "w"), ensure_ascii=False)
    print("-" * 60)
    print("ORDRES du GENERAL (Qwen) :")
    print(json.dumps(ans, ensure_ascii=False, indent=2))
    print("-> ecrit dans", ORDERS)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--period", type=float, default=12)
    a = ap.parse_args()
    if a.loop:
        while True:
            try:
                cycle()
            except Exception as e:
                print("[general] err:", e)
            time.sleep(a.period)
    else:
        cycle()
