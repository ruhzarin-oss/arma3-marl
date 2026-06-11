-- cmo_ping.lua — TEST ATOMIQUE du Gate 0 CMO : le Lua de CMO peut-il ECRIRE un fichier (io.open) ?
-- C'est LE point critique du pont (tout le reste en decoule). A coller dans la console Lua de CMO
-- (Editor -> Lua Script Console), ou comme action d'un event. Mapping Proton : Z:\ = / cote Linux.
local ok, err = pcall(function()
  local t = ScenEdit_CurrentTime()                 -- temps de simulation (preuve que l'API repond)
  local f = io.open("Z:\\tmp\\cmo_bridge\\ping.txt", "w")
  f:write("HMT_CMO_PING ok time=" .. tostring(t) .. "\n")
  f:close()
end)
if not ok then
  local f = io.open("Z:\\tmp\\cmo_bridge\\ping.txt", "w")
  if f then f:write("HMT_CMO_PING err=" .. tostring(err) .. "\n"); f:close() end
  ScenEdit_SpecialMessage("Blue", "PING ECHEC: " .. tostring(err))
else
  ScenEdit_SpecialMessage("Blue", "PING OK -> /tmp/cmo_bridge/ping.txt ecrit")
end
