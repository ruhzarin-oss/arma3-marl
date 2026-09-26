# lancer_guerre.ps1 — demarre le serveur Arma de la guerre des iles par WMI (Win32_Process.Create).
# Copie de labo/lancer_labo.ps1 (ses deux lecons : WMI et pas Start-Process, HMT_BRIDGE_WIN dans l environnement
# DU serveur), avec la carte en parametre : la guerre se joue sur Malden. Sa configuration est server_guerre.cfg : le
# server.cfg de hmtech10 est celui de l inventaire de Malden ( 24/09 ), on n y touche pas. Sans mods par defaut, comme
# l inventaire ( prouve le 24/09 ) : Warlords est du jeu de base, et C:\hmt_mods n existe pas.
param([int]$Instance = 10, [string]$Monde = 'Malden', [string]$Mods = '')
$ErrorActionPreference = 'Stop'
$arma   = 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3'
$exe    = Join-Path $arma 'arma3server_x64.exe'
$profil = "C:\Users\Younes\hmtech$Instance"
$pont   = "C:\hmt_bridge\i$Instance"
$port   = 2402 + 10 * $Instance
$ligne  = "`"$exe`" -config=$profil\server_guerre.cfg -profiles=$profil -name=hmtech$Instance -port=$port " +
          "-world=$Monde -noSound -autoInit"
if ($Mods -ne '') { $ligne += " `"-mod=$Mods`"" }
$vars = @(Get-ChildItem Env: | Where-Object { $_.Name -ne 'HMT_BRIDGE_WIN' } |
          ForEach-Object { "$($_.Name)=$($_.Value)" })
$vars += "HMT_BRIDGE_WIN=$pont"
$demarrage = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly `
             -Property @{ EnvironmentVariables = [string[]]$vars }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $ligne; CurrentDirectory = $arma; ProcessStartupInformation = $demarrage }
if ($r.ReturnValue -ne 0) { Write-Output "ECHEC WMI $($r.ReturnValue)"; exit 1 }
Write-Output "PID $($r.ProcessId)"
