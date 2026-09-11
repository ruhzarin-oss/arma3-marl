# lancer_labo.ps1 — démarre le serveur Arma du LABO par WMI (Win32_Process.Create). Appelé par
# lancer_labo.sh, qui le copie dans C:\hmt\labo\ : PowerShell n'exécute pas un script sur \\wsl$.
#
# ⚠️ PAS Start-Process : lancé depuis ssh, le processus reste enfant de la session et meurt avec
# elle. WMI le fait naître sous WmiPrvSE, hors de l'arbre ssh (mesuré le 04/09/2026).
# ⚠️ HMT_BRIDGE_WIN doit être dans l'environnement DU SERVEUR : c'est la DLL hmt_ext qui le lit.
# EnvironmentVariables REMPLACE tout l'environnement : on passe donc l'environnement courant
# complet, plus cette variable.
param([int]$Instance = 9, [string]$Mods = '!Workshop\@CBA_A3;C:\hmt_mods\@LAMBS_Danger')
$ErrorActionPreference = 'Stop'
$arma   = 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3'
$exe    = Join-Path $arma 'arma3server_x64.exe'
$profil = "C:\Users\Younes\hmtech$Instance"
$pont   = "C:\hmt_bridge\i$Instance"
$port   = 2402 + 10 * $Instance
$ligne  = "`"$exe`" -config=$profil\server.cfg -profiles=$profil -name=hmtech$Instance -port=$port " +
          "-world=Altis -noSound -autoInit `"-mod=$Mods`""
$vars = @(Get-ChildItem Env: | Where-Object { $_.Name -ne 'HMT_BRIDGE_WIN' } |
          ForEach-Object { "$($_.Name)=$($_.Value)" })
$vars += "HMT_BRIDGE_WIN=$pont"
$demarrage = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly `
             -Property @{ EnvironmentVariables = [string[]]$vars }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $ligne; CurrentDirectory = $arma; ProcessStartupInformation = $demarrage }
if ($r.ReturnValue -ne 0) { Write-Output "ECHEC WMI $($r.ReturnValue)"; exit 1 }
Write-Output "PID $($r.ProcessId)"
