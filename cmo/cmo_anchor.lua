-- cmo_anchor.lua — cote CMO (VM Windows), a charger comme action d'un evenement RECURRENT (~1/s sim).
-- Role : resoudre en BATCH des combats scriptes et exporter l'ISSUE (survivants). Machine a etats idle->running->done.
-- Prerequis : Game -> Options -> Lua security DESACTIVEE (sinon io.open bloque).
--   ANCHOR_DIR = dossier PARTAGE vu cote Windows (ex Z:\cmo_bridge\) = le bridge_dir cote Linux.
-- Battement (hb.json) reecrit CHAQUE tick -> l'hote detecte le gel. Ecritures ATOMIQUES (tmp->rename).
-- NB: la CONSTRUCTION d'unites (ScenEdit_AddUnit) et le comptage survivants sont a VALIDER contre CMO reel
--     (noms de classes/DB, guids) au premier round-trip ; la MECANIQUE du pont, elle, est prouvee a blanc.
if ANCHOR_DIR == nil then ANCHOR_DIR = [[Z:\cmo_bridge\]] end
if HMT_k     == nil then HMT_k = 0 end          -- dernier job resolu
if HMT_phase == nil then HMT_phase = "idle" end
if HMT_wall  == nil then HMT_wall = 0 end       -- compteur de ticks (battement)
if HMT_job   == nil then HMT_job = nil end

local BLUE_CLASS = "FA-18E"       -- a caler sur la DB CMO du scenario d'ancrage
local RED_CLASS  = "Su-35S"
local RESOLVE_CAP = 3600          -- s de sim max par combat avant resolution forcee

local function atomic_write(name, s)
  local f = io.open(ANCHOR_DIR .. name .. ".tmp", "w"); if f == nil then return end
  f:write(s); f:close()
  os.remove(ANCHOR_DIR .. name); os.rename(ANCHOR_DIR .. name .. ".tmp", ANCHOR_DIR .. name)
end

local function heartbeat()
  HMT_wall = HMT_wall + 1
  atomic_write("hb.json", string.format('{"t":%s,"wall":%d,"k":%d,"phase":"%s"}',
               tostring(ScenEdit_CurrentTime()), HMT_wall, HMT_k, HMT_phase))
end

local function read_job(k)
  local f = io.open(ANCHOR_DIR .. "job_" .. tostring(k) .. ".json", "r")
  if f == nil then return nil end
  local s = f:read("*a"); f:close()
  local nb = tonumber(s:match('"nb":%s*(%d+)')); local nr = tonumber(s:match('"nr":%s*(%d+)'))
  local aw = tonumber(s:match('"aw":%s*(%d+)')); local sd = tonumber(s:match('"seed":%s*(%d+)'))
  if nb == nil then return nil end
  return {k = k, nb = nb, nr = nr, aw = aw, seed = sd}
end

local function count_side(sd)                      -- survivants avions du camp (a valider vs CMO reel)
  local ok, side = pcall(function() return VP_GetSide({side = sd}) end)
  if not ok or side == nil or side.units == nil then return 0 end
  local n = 0
  for i = 1, #side.units do
    local u = ScenEdit_GetUnit({guid = side.units[i].guid})
    if u ~= nil and (u.type == "Aircraft" or u.type == "Air") and (u.damage or 0) < 100 then n = n + 1 end
  end
  return n
end

local function build_battle(job)
  -- table rase des avions puis pose nb bleus + nr rouges (+ AWACS si aw=1). ScenEdit_AddUnit a valider.
  pcall(function()
    for _, sd in ipairs({"BLUE", "RED"}) do
      local ok, side = pcall(function() return VP_GetSide({side = sd}) end)
      if ok and side ~= nil and side.units ~= nil then
        for i = #side.units, 1, -1 do pcall(function() ScenEdit_DeleteUnit({guid = side.units[i].guid}) end) end
      end
    end
    for i = 1, job.nb do
      ScenEdit_AddUnit({type = "Air", name = "RAF_" .. i, side = "BLUE", dbid = 0,
                        loadoutid = 0, unitclass = BLUE_CLASS, latitude = 40.0, longitude = 10.0 + i * 0.05,
                        altitude = 9000, heading = 90})
    end
    for i = 1, job.nr do
      ScenEdit_AddUnit({type = "Air", name = "SU_" .. i, side = "RED", dbid = 0,
                        loadoutid = 0, unitclass = RED_CLASS, latitude = 40.0, longitude = 11.5 + i * 0.05,
                        altitude = 9000, heading = 270})
    end
    if job.aw == 1 then
      ScenEdit_AddUnit({type = "Air", name = "E3F", side = "BLUE", dbid = 0, loadoutid = 0,
                        unitclass = "E-3F", latitude = 39.7, longitude = 9.6, altitude = 9000, heading = 90})
    end
  end)
  HMT_start_t = ScenEdit_CurrentTime()
end

local function resolved(job)
  local b = count_side("BLUE"); local r = count_side("RED")
  local elapsed = ScenEdit_CurrentTime() - (HMT_start_t or ScenEdit_CurrentTime())
  -- resolu si un camp est vide OU cap de temps atteint
  if b == 0 or r == 0 or elapsed >= RESOLVE_CAP then return true, b, r end
  return false, b, r
end

-- ===== machine a etats =====
heartbeat()
if HMT_phase == "idle" then
  local job = read_job(HMT_k + 1)
  if job ~= nil then
    HMT_job = job; build_battle(job); HMT_phase = "running"
  end
elseif HMT_phase == "running" then
  local done, b, r = resolved(HMT_job)
  if done then
    local aw = HMT_job.aw
    local blue0 = HMT_job.nb + aw     -- AWACS compte dans l'effectif bleu de depart
    atomic_write("result_" .. tostring(HMT_job.k) .. ".json", string.format(
      '{"k":%d,"nb":%d,"nr":%d,"aw":%d,"seed":%d,"blue0":%d,"red0":%d,"blue_surv":%d,"red_surv":%d,"status":"ok"}',
      HMT_job.k, HMT_job.nb, HMT_job.nr, aw, HMT_job.seed or 0, blue0, HMT_job.nr, b, r))
    HMT_k = HMT_job.k; HMT_phase = "idle"; HMT_job = nil
  end
end
