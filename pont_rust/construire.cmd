@echo off
rem Compile le pont du monde ( extension Arma monde_x64.dll ) avec MSVC. Lance par WMI, sans aucune redirection interne
rem ( memoire build-windows-par-ssh-pieges ) ; la sortie est redirigee a l invocation.
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d C:\hmt\pont_rust
"%USERPROFILE%\.cargo\bin\cargo.exe" build --release
if errorlevel 1 goto echec
copy /Y target\release\monde.dll "C:\Program Files (x86)\Steam\steamapps\common\Arma 3\monde_x64.dll"
echo ===== EXITCODE 0
goto fin
:echec
echo ===== EXITCODE 1
:fin
