#!/usr/bin/env python3
"""Installeer het desktopbestand waarmee Linux het app-icoon toont.

GNOME toont links in de titelbalk en in de dock het icoon uit het desktopbestand
dat bij de app_id hoort -- niet het icoon van setWindowIcon(). Dit script schrijft
dat bestand met de juiste, absolute paden naar ~/.local/share/applications.

Gebruik:
    python3 installeer_desktop.py                    # start via de bronlauncher
    python3 installeer_desktop.py --exe dist/Muziekspeler   # na een PyInstaller-build
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

BASIS = Path(__file__).resolve().parent
DOEL = Path.home() / ".local/share/applications/muziekspeler.desktop"

SJABLOON = """[Desktop Entry]
Type=Application
Version=1.0
Name=Muziekspeler
GenericName=Muziekspeler
Comment=Een Winamp-light in Python, in de stijl van Top30
Exec={programma}
TryExec={programma}
Icon={icoon}
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupWMClass=muziekspeler
StartupNotify=true
"""


def main() -> None:
    keuzes = argparse.ArgumentParser(description=__doc__)
    keuzes.add_argument("--exe", help="pad naar de PyInstaller-executable")
    argumenten = keuzes.parse_args()

    programma = (
        Path(argumenten.exe).resolve()
        if argumenten.exe
        else BASIS / "muziekspeler"
    )
    icoon = programma.parent / "icon.png" if argumenten.exe else BASIS / "icon.png"
    if not icoon.exists():
        icoon = BASIS / "icon.png"
    if not programma.exists():
        keuzes.error(f"programma niet gevonden: {programma}")
    if not icoon.exists():
        keuzes.error(f"icoon niet gevonden: {icoon}")

    DOEL.parent.mkdir(parents=True, exist_ok=True)
    DOEL.write_text(
        SJABLOON.format(programma=programma, icoon=icoon), encoding="utf-8"
    )
    DOEL.chmod(0o755)
    # Ook een kopie in de projectmap, zodat de bronmap altijd hetzelfde
    # bestand bevat als wat er nu geïnstalleerd staat.
    (BASIS / "muziekspeler.desktop").write_text(DOEL.read_text(encoding="utf-8"), encoding="utf-8")

    if shutil.which("update-desktop-database"):
        subprocess.run(
            ["update-desktop-database", str(DOEL.parent)],
            check=False,
            capture_output=True,
        )
    print(f"Geïnstalleerd: {DOEL}")
    print(f"  Exec: {programma}")
    print(f"  Icon: {icoon}")


if __name__ == "__main__":
    main()
