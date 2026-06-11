-- cmo_bridge.lua — PONT CMO <-> Python (jumeau du pont fichier Arma). A poser comme action d'un
-- EVENT RECURRENT (trigger "Regular Time", ~1 s de jeu) dans un scenario. Mapping Proton Z:\ = /.
--   OUT : dump l'etat (unites des sides Blue/Red : lat/lon/cap/vitesse/alt/vivant) -> state.txt
--   IN  : lit cmd.lua (genere par Python), l'execute via load(), puis l'archive (n croissant)
local DIR = "Z:\\tmp\\cmo_bridge\\"

local function dump_state()
  local f = io.open(DIR .. "state.txt", "w")
  if not f then return end
  f:write("T " .. tostring(ScenEdit_CurrentTime()) .. "\n")
  for _, sidename in ipairs({"Blue", "Red"}) do
    local ok, side = pcall(VP_GetSide, {name = sidename})
    if ok and side and side.units then
      for _, ud in ipairs(side.units) do
        local ok2, u = pcall(ScenEdit_GetUnit, {guid = ud.guid})
        if ok2 and u then
          f:write(string.format("U %s|%s|%s|%.5f|%.5f|%.1f|%.1f|%.1f\n",
            sidename, tostring(u.name), tostring(u.guid),
            u.latitude or 0, u.longitude or 0, u.heading or 0, u.speed or 0, u.altitude or 0))
        end
      end
    end
  end
  f:close()
end

local function exec_cmd()
  local cf = io.open(DIR .. "cmd.lua", "r")
  if not cf then return end
  local code = cf:read("*a"); cf:close()
  os.remove(DIR .. "cmd.lua")
  if code and #code > 2 then
    local chunk, e = load(code)
    if chunk then pcall(chunk) end
    local af = io.open(DIR .. "ack.txt", "w")
    if af then af:write("ACK " .. tostring(ScenEdit_CurrentTime()) .. "\n"); af:close() end
  end
end

exec_cmd()
dump_state()
