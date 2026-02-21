@echo off
cd /d "%~dp0"
chcp 65001 >nul
echo ===================================================
echo   LinMHelper - 安裝與環境設定 (新電腦專用)
echo ===================================================
echo.

echo [1/3] 檢查 Python 是否已安裝並加入環境變數...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 GOTO NO_PYTHON

echo [2/3] 建立虛擬環境 (.venv)...
python -m venv .venv
IF %ERRORLEVEL% NEQ 0 GOTO VENV_ERROR

echo [3/3] 安裝必要套件與依賴...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 GOTO PIP_ERROR

echo.
echo ===================================================
echo   安裝設定完成！
echo   日後只要點擊執行 【Start.bat】 即可開啟程式。
echo ===================================================
pause
exit /b


:NO_PYTHON
echo [錯誤] 找不到 Python，或者尚未加入 PATH 環境變數。
echo 請前往 https://www.python.org/ 下載 Python 3.8 以上版本，
echo 安裝時請務必勾選 "Add Python to PATH" (或 "Add python.exe to PATH")。
echo.
pause
exit /b

:VENV_ERROR
echo [錯誤] 建立虛擬環境失敗。
pause
exit /b

:PIP_ERROR
echo [錯誤] 安裝套件時發生錯誤，請檢查網路或套件名稱。
pause
exit /b
