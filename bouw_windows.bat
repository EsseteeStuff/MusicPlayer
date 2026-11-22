@echo off
REM Maak een losse Windows-executable met het juiste icoon.
REM Resultaat: dist\Muziekspeler.exe
setlocal
cd /d "%~dp0"

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pyinstaller

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name Muziekspeler ^
    --icon icon.ico ^
    --add-data "icon.png;." ^
    --add-data "icon.ico;." ^
    muziekspeler.py

echo.
echo Klaar: dist\Muziekspeler.exe
endlocal
