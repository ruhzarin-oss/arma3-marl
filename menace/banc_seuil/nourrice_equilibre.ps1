$ProgressPreference='SilentlyContinue'
foreach ($i in 1..10) {
  & 'C:\Program Files\WSL\wsl.exe' -u younes -- python3 /mnt/c/hmt/tmp/reaffecter.py | Out-Null
  foreach ($k in 1..2) { schtasks /run /tn HMT_RUN | Out-Null; Start-Sleep -Seconds 26 }
}
"serveurs : " + @(Get-Process arma3server_x64 -ErrorAction SilentlyContinue).Count
