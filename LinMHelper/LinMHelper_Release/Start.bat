@echo off
cd /d "%~dp0"
chcp 65001 >nul
echo 正在啟動 LinM Helper...

IF NOT EXIST ".venv\Scripts\activate.bat" GOTO NO_ENV

call .venv\Scripts\activate.bat
start pythonw main.py
exit /b

:NO_ENV
echo [錯誤] 找不到虛擬環境 .venv，請先執行 Setup.bat 進行安裝。
echo 按任意鍵結束...
pause >nul
exit /b
