#!/usr/bin/env bash
# Maak een losse Linux-executable; het icoon wordt ook in de GUI gebruikt.
# Resultaat: dist/Muziekspeler
set -e
cd "$(dirname "$0")"

.venv/bin/python -m pip install --upgrade pyinstaller
.venv/bin/python -m PyInstaller --noconfirm --clean --onefile --windowed \
    --name Muziekspeler \
    --icon icon.ico \
    --add-data "icon.png:." \
    --add-data "icon.ico:." \
    muziekspeler.py

# Iconen naast de executable leggen en het desktopbestand daarop laten wijzen,
# zodat GNOME ook voor de losse build het juiste icoon toont.
cp icon.png icon.ico dist/
.venv/bin/python installeer_desktop.py --exe dist/Muziekspeler

echo "Klaar: dist/Muziekspeler"
