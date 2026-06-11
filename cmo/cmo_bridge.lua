-- cmo_bridge.lua — actuateur PONT cote CMO (a charger comme action d un evenement RECURRENT, ~1/s sim).
-- Prerequis : Game -> Options -> Lua security DESACTIVEE (sinon io.open est bloque).
-- HMT_DIR = dossier PARTAGE, vu cote Windows (ex Z:\hmt_bridge\), = /mnt/.../hmt_bridge cote Linux.
-- OUT : ecrit state.json (unites + temps + n=dernier ordre execute), ecriture atomique (tmp->rename).
-- IN  : lit cmd_<n+1>.lua, l execute (load), incremente HMT_n.
if HMT_DIR == nil then HMT_DIR = [[Z:\hmt_bridge\]] end
if HMT_n   == nil then HMT_n = 0 end
if HMT_SIDES == nil then HMT_SIDES = {"BLUE", "RED"} end

local function jstr(s) return (tostring(s):gsub("\\", "\\\\"):gsub("\"", "\\\"")) end

local function dump_state()
  local f = io.open(HMT_DIR .. "state.tmp", "w")
  if f == nil then return end
  f:write("{\"t\":" .. tostring(ScenEdit_CurrentTime()) .. ",\"n\":" .. tostring(HMT_n) .. ",\"units\":[")
  local first = true
  for _, sd in ipairs(HMT_SIDES) do
    -- enumeration des unites du camp (a VALIDER contre CMO reel : VP_GetSide().units / ScenEdit_GetUnit)
    local ok, side = pcall(function() return VP_GetSide({side = sd}) end)
    if ok and side ~= nil and side.units ~= nil then
      for i = 1, #side.units do
        local u = ScenEdit_GetUnit({guid = side.units[i].guid})
        if u ~= nil then
          if not first then f:write(",") end
          first = false
          f:write(string.format(
            "{\"side\":\"%s\",\"name\":\"%s\",\"lon\":%s,\"lat\":%s,\"hdg\":%s,\"spd\":%s,\"alt\":%s,\"dmg\":%s}",
            jstr(sd), jstr(u.name), tostring(u.longitude or 0), tostring(u.latitude or 0),
            tostring(u.heading or 0), tostring(u.speed or 0), tostring(u.altitude or 0), tostring(u.damage or 0)))
        end
      end
    end
  end
  f:write("]}")
  f:close()
  os.remove(HMT_DIR .. "state.json")
  os.rename(HMT_DIR .. "state.tmp", HMT_DIR .. "state.json")
end

local function poll_cmd()
  local nx = HMT_n + 1
  local f = io.open(HMT_DIR .. "cmd_" .. tostring(nx) .. ".lua", "r")
  if f ~= nil then
    local code = f:read("*a")
    f:close()
    pcall(function() load(code)() end)
    HMT_n = nx
  end
end

dump_state()
poll_cmd()
