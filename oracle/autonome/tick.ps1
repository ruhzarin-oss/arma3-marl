# Tache Windows HMT_ORACLE : un tour de l Oracle autonome toutes les 5 minutes. Le tour tourne dans WSL ; s il demande de
# nourrir la ferme ( « NOURRIR n » ), c est ICI qu on declenche HMT_RUN - un processus WSL detache ne peut pas
# appeler un .exe Windows ( memoire du 17/09 ).
$log = 'C:\hmt\logs\oracle.log'
New-Item -ItemType Directory -Force -Path 'C:\hmt\logs' | Out-Null
$out = & wsl.exe -u younes -- bash /mnt/data/hmt/depot/oracle/autonome/tick.sh 2>&1
$t = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
($out | ForEach-Object { "$t $_" }) | Out-File -FilePath $log -Append -Encoding utf8
$m = [regex]::Match(($out -join "`n"), 'NOURRIR (\d+)')
if ($m.Success) { for ($i = 0; $i -lt [int]$m.Groups[1].Value; $i++) { schtasks /run /tn HMT_RUN | Out-Null; Start-Sleep -Seconds 2 } }
