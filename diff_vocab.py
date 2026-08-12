import re, glob, pathlib
CMDS = """commandSuppressiveFire doSuppressiveFire suppressFor getSuppression setSuppression
checkVisibility lineIntersectsSurfaces lineIntersects terrainIntersect terrainIntersectASL
eyePos aimPos eyeDirection weaponDirection aimedAtTarget
knowsAbout reveal forgetTarget targetKnowledge targetsQuery nearTargets
findCover findNearestEnemy nearestObjects nearestTerrainObjects boundingBoxReal sizeOf
setUnitPos setBehaviour setCombatMode setSpeedMode setFormation setFormDir
doMove doFollow doStop doWatch doTarget doFire commandMove commandStop commandWatch
commandTarget commandFire moveTo forceSpeed limitSpeed setDestination addWaypoint
setWaypointType disableAI enableAI setSkill skillFinal unitReady canFire canMove
currentCommand lifeState setUnconscious setVehicleAmmo setUnitLoadout getUnitLoadout
setAmmo someAmmo allowFleeing setUnitTrait nearRoads isOnRoad selectBestPlaces
BIS_fnc_findOverwatch BIS_fnc_nearestPosition""".split()
def lu(fs):
    t = ""
    for f in fs:
        try: t += pathlib.Path(f).read_text(encoding="utf-8", errors="ignore") + "\n"
        except: pass
    t = re.sub(r"//.*", "", t)
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)
leur = lu(glob.glob("/home/younes/arma3-marl/refs/antistasi/A3A/addons/**/*.sqf", recursive=True))
notre = lu(glob.glob("/mnt/data/harmattan-sandbox/arma3server/mpmissions/*/*.sqf"))
print("  %-28s%6s%6s" % ("commande", "eux", "nous"))
print("  " + "-" * 46)
manq = []
for c in CMDS:
    a = len(re.findall(r"\b" + re.escape(c) + r"\b", leur))
    b = len(re.findall(r"\b" + re.escape(c) + r"\b", notre))
    if a or b:
        print("  %-28s%6d%6d%s" % (c, a, b, "   <-- JAMAIS CHEZ NOUS" if (a and not b) else ""))
        if a and not b: manq.append((c, a))
print("\n  %d commandes qu ils emploient et nous jamais :" % len(manq))
for c, a in sorted(manq, key=lambda x: -x[1]): print("     %4d  %s" % (a, c))
