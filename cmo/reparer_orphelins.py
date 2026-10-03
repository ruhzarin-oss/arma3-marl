#!/usr/bin/env python3
"""reparer_orphelins — après un complément interrompu ( 03/10 : prix manquant pendant le complément, état non sauvé ),
retire de CMO les SEULES unités HMT posées depuis le dernier theatre.json ( les unités non HMT de nos camps, créées par
CMO lui-même : groupes, équipages éjectés, restent ), pour que la reprise les repose proprement sans doublon. Refuse au-delà de MAX unités. Lua brut par_humain.

    .venv312/bin/python cmo/reparer_orphelins.py <dossier de la guerre> [--retirer]"""
import json, os, sys
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import cmo_labo as CL                                     # noqa: E402
from theatres import baltique_reel as T                   # noqa: E402

MAX = 200


def main(dossier, retirer=False):
    e = json.load(open(os.path.join(dossier, "theatre.json")))
    connus = {int(k) for k in e["avions"]} | {int(k) for k in e["sol"]} | {int(k) for k in e["elements"]}
    connus |= {int(b["groupe"]) for b in e["bases"].values() if b.get("groupe")}
    with CL.Labo(camps=T.CAMPS, installations=T.FICHIERS) as l:
        r = l.lua("for k, _ in pairs(HMT_recenser()) do R('N', {k}) end "
                  "local n = 0 for _, nom in ipairs(HMT_CAMPS) do local ok, s = pcall(VP_GetSide, {side = nom}) "
                  "for _, x in ipairs((ok and s and s.units) or {}) do if not string.match(x.name or '', '^HMT%-%d+$') "
                  "and ScenEdit_GetUnit({guid = x.guid}) ~= nil then n = n + 1 end end end R('NON_HMT', {n})", par_humain=True, patience=120)
        dans_cmo = {int(x["nombres"][0]) for x in r["lignes"] if x["cle"] == "N"}
        non_hmt = next(int(x["nombres"][0]) for x in r["lignes"] if x["cle"] == "NON_HMT")
        orphelins = sorted(dans_cmo - connus)
        print(f"{len(dans_cmo)} unités HMT dans CMO, {len(connus)} dans l'état ; orphelins {len(orphelins)} : {orphelins[:40]} ; non HMT {non_hmt}")
        if not retirer:
            return
        if len(orphelins) + non_hmt > MAX:
            print("REFUS : trop d'unités à retirer, rien n'est fait")
            return
        n = 0
        for i in range(0, len(orphelins), 50):
            corps = " ".join(f"do local e = HMT_recenser()[{k}] if e then pcall(ScenEdit_DeleteUnit, {{guid = e.guid}}) R('X', {{{k}}}) end end"
                             for k in orphelins[i:i + 50])
            n += sum(1 for x in l.lua(corps, par_humain=True, patience=120)["lignes"] if x["cle"] == "X")
        l.lua("HMT_unites = nil", par_humain=True)          # le registre sera refait à la prochaine ouverture
        print(f"retirés : {n} orphelins HMT ( les unités non HMT, créées par CMO lui-même, restent )")


if __name__ == "__main__":
    main(sys.argv[1], "--retirer" in sys.argv)
