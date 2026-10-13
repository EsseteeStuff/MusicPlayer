#!/usr/bin/env python3
# Copyright (C) 2026 EsseteeStuff
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Muziekspeler in de stijl van de Top30-app, een "Winamp-light".

    .venv/bin/python muziekspeler.py

Opent een map met muziek (of sleep bestanden in het venster) en speelt ze
af. De vormgeving past bij Top30, met meerdere thema's (donker, licht,
middernacht, bos, sepia, neon), een afspeellijst, voortgangsbalk, volume,
willekeurig en herhalen. Extra's: een equalizer ("mengpaneel") met presets,
een visualizer (oscilloscoop) en meertaligheid (Nederlands, Engels, Duits en
Frans; de systeemtaal kiest de starttaal, in de kopbalk is te wisselen).

Sneltoetsen:
    Spatie          afspelen / pauzeren
    Ctrl+O          een map kiezen
    Ctrl+Links      vorige nummer
    Ctrl+Rechts     volgende nummer
    Ctrl+H          herhalen (uit → één → alle)
    Ctrl+M          dempen
"""
from __future__ import annotations

import array
import math
import random
import sys
from pathlib import Path

from PySide6.QtCore import (
    QEventLoop, QIODevice, QLocale, QObject, QSettings, Qt, QThread, QTimer,
    QUrl, Signal,
)
from PySide6.QtGui import (
    QColor, QFontDatabase, QKeySequence, QPainter, QPen, QShortcut,
)
from PySide6.QtMultimedia import (
    QAudioDecoder, QAudioFormat, QAudioOutput, QAudioSink, QMediaPlayer,
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QSlider,
    QVBoxLayout, QWidget,
)

# --------------------------------------------------------------------------
# Talen: een dunne vertaallaag. De Nederlandse tekst is de sleutel; ontbreekt
# een vertaling, dan valt de app terug op het Nederlands. De systeemtaal kiest
# de starttaal; in de kopbalk staat een keuzemenu om te wisselen.
# --------------------------------------------------------------------------

TAAL_NAMEN = {
    "nl": "Nederlands",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
}

VERTALINGEN: dict[str, dict[str, str]] = {
    "nl": {},
    "en": {
        "Muziekspeler": "Music Player",
        "Een Winamp-light in Python, in de Top30-stijl":
            "A Winamp-light in Python, in the Top30 style",
        "Thema": "Theme",
        "Taal": "Language",
        "Donker": "Dark",
        "Licht": "Light",
        "Middernacht": "Midnight",
        "Bos": "Forest",
        "AFSPELLIJST": "PLAYLIST",
        "Map kiezen…": "Choose folder…",
        "Bestanden…": "Files…",
        "Wis": "Clear",
        "SPELER": "PLAYER",
        "— kies een nummer —": "— choose a track —",
        "⏮ Vorige": "⏮ Previous",
        "Afspelen": "Play",
        "Pauze": "Pause",
        "Volgende ⏭": "Next ⏭",
        "Stoppen": "Stop",
        "Willekeurig": "Shuffle",
        "Herhalen: uit": "Repeat: off",
        "Herhalen: één": "Repeat: one",
        "Herhalen: alle": "Repeat: all",
        "Dempen": "Mute",
        "EQ aan": "EQ on",
        "Standaard": "Default",
        "Preset": "Preset",
        "Kies een vooraf ingestelde tooncurve": "Choose a preset tone curve",
        "Eigen": "Custom",
        "Vlak": "Flat",
        "Meer bas": "More bass",
        "Minder bas": "Less bass",
        "Stem": "Vocal",
        "Elektronisch": "Electronic",
        "Klassiek": "Classical",
        "Spraak": "Speech",
        "{etiket} Hz (dubbelklik = 0)": "{etiket} Hz (double-click = 0)",
        "Preamp (dubbelklik = 0)": "Preamp (double-click = 0)",
        "Pre": "Pre",
        "— gestopt —": "— stopped —",
        "— geen golfvorm —": "— no waveform —",
        "Kan dit nummer niet afspelen:\n{boodschap}":
            "Can't play this track:\n{boodschap}",
        "EQ wacht op een nummer.": "EQ is waiting for a track.",
        "EQ verwerkt nummer…": "EQ is processing the track…",
        "EQ actief ({rate} kHz)": "EQ active ({rate} kHz)",
        "EQ kan dit nummer niet verwerken.":
            "EQ can't process this track.",
        "Kies een map met muziek": "Choose a music folder",
        "Kies muziekbestanden": "Choose music files",
        "Muziek ({soorten})": "Music ({soorten})",
    },
    "de": {
        "Muziekspeler": "Musikspieler",
        "Een Winamp-light in Python, in de Top30-stijl":
            "Ein Winamp-Light in Python, im Top30-Stil",
        "Thema": "Design",
        "Taal": "Sprache",
        "Donker": "Dunkel",
        "Licht": "Hell",
        "Middernacht": "Mitternacht",
        "Bos": "Wald",
        "AFSPELLIJST": "WIEDERGABELISTE",
        "Map kiezen…": "Ordner wählen…",
        "Bestanden…": "Dateien…",
        "Wis": "Leeren",
        "SPELER": "PLAYER",
        "— kies een nummer —": "— Titel wählen —",
        "⏮ Vorige": "⏮ Zurück",
        "Afspelen": "Wiedergabe",
        "Pauze": "Pause",
        "Volgende ⏭": "Weiter ⏭",
        "Stoppen": "Stopp",
        "Willekeurig": "Zufällig",
        "Herhalen: uit": "Wiederholen: aus",
        "Herhalen: één": "Wiederholen: eins",
        "Herhalen: alle": "Wiederholen: alle",
        "Dempen": "Stumm",
        "EQ aan": "EQ ein",
        "Standaard": "Standard",
        "Preset": "Voreinstellung",
        "Kies een vooraf ingestelde tooncurve": "Eine Klangkurve wählen",
        "Eigen": "Eigene",
        "Vlak": "Flach",
        "Meer bas": "Mehr Bass",
        "Minder bas": "Weniger Bass",
        "Stem": "Stimme",
        "Elektronisch": "Elektronisch",
        "Klassiek": "Klassisch",
        "Spraak": "Sprache",
        "{etiket} Hz (dubbelklik = 0)": "{etiket} Hz (Doppelklick = 0)",
        "Preamp (dubbelklik = 0)": "Vorverstärker (Doppelklick = 0)",
        "Visualizer": "Visualisierer",
        "— gestopt —": "— gestoppt —",
        "— geen golfvorm —": "— keine Wellenform —",
        "Kan dit nummer niet afspelen:\n{boodschap}":
            "Dieser Titel lässt sich nicht abspielen:\n{boodschap}",
        "EQ wacht op een nummer.": "EQ wartet auf einen Titel.",
        "EQ verwerkt nummer…": "EQ verarbeitet Titel…",
        "EQ actief ({rate} kHz)": "EQ aktiv ({rate} kHz)",
        "EQ kan dit nummer niet verwerken.":
            "EQ kann diesen Titel nicht verarbeiten.",
        "Kies een map met muziek": "Musikordner wählen",
        "Kies muziekbestanden": "Musikdateien wählen",
        "Muziek ({soorten})": "Musik ({soorten})",
    },
    "fr": {
        "Muziekspeler": "Lecteur de musique",
        "Een Winamp-light in Python, in de Top30-stijl":
            "Un Winamp-light en Python, dans le style Top30",
        "Thema": "Thème",
        "Taal": "Langue",
        "Donker": "Sombre",
        "Licht": "Clair",
        "Middernacht": "Minuit",
        "Bos": "Forêt",
        "Sepia": "Sépia",
        "Neon": "Néon",
        "AFSPELLIJST": "LISTE DE LECTURE",
        "Map kiezen…": "Choisir un dossier…",
        "Bestanden…": "Fichiers…",
        "Wis": "Vider",
        "SPELER": "LECTEUR",
        "— kies een nummer —": "— choisir un titre —",
        "⏮ Vorige": "⏮ Précédent",
        "Afspelen": "Lecture",
        "Pauze": "Pause",
        "Volgende ⏭": "Suivant ⏭",
        "Stoppen": "Arrêter",
        "Willekeurig": "Aléatoire",
        "Herhalen: uit": "Répéter : non",
        "Herhalen: één": "Répéter : un",
        "Herhalen: alle": "Répéter : tous",
        "Dempen": "Muet",
        "Equalizer": "Égaliseur",
        "EQ aan": "EQ activé",
        "Standaard": "Par défaut",
        "Preset": "Préréglage",
        "Kies een vooraf ingestelde tooncurve":
            "Choisir une courbe préréglée",
        "Eigen": "Personnalisé",
        "Vlak": "Plat",
        "Meer bas": "Plus de basses",
        "Minder bas": "Moins de basses",
        "Stem": "Voix",
        "Elektronisch": "Électronique",
        "Klassiek": "Classique",
        "Spraak": "Parole",
        "{etiket} Hz (dubbelklik = 0)": "{etiket} Hz (double-clic = 0)",
        "Preamp (dubbelklik = 0)": "Préampli (double-clic = 0)",
        "Pre": "Pré",
        "Visualizer": "Visualiseur",
        "— gestopt —": "— arrêté —",
        "— geen golfvorm —": "— aucune forme d'onde —",
        "Kan dit nummer niet afspelen:\n{boodschap}":
            "Impossible de lire ce titre :\n{boodschap}",
        "EQ wacht op een nummer.": "L'égaliseur attend un titre.",
        "EQ verwerkt nummer…": "L'égaliseur traite le titre…",
        "EQ actief ({rate} kHz)": "Égaliseur actif ({rate} kHz)",
        "EQ kan dit nummer niet verwerken.":
            "L'égaliseur ne peut pas traiter ce titre.",
        "Kies een map met muziek": "Choisir un dossier de musique",
        "Kies muziekbestanden": "Choisir des fichiers musicaux",
        "Muziek ({soorten})": "Musique ({soorten})",
    },
}

TAAL = "nl"


def zet_taal(code: object) -> None:
    """De taal kiezen; onbekend valt terug op Nederlands."""
    global TAAL
    TAAL = code if code in VERTALINGEN else "nl"


def t(tekst: str) -> str:
    """De vertaling van `tekst` in de huidige taal (anders de tekst zelf)."""
    return VERTALINGEN.get(TAAL, {}).get(tekst, tekst)


def systeemtaal() -> str:
    """De taal van het systeem, als we die ondersteunen, anders Nederlands."""
    van_q = QLocale.system().name()          # bijvoorbeeld "nl_BE"
    code = van_q.split("_")[0].lower()
    return code if code in VERTALINGEN else "nl"


# --------------------------------------------------------------------------
# Stijl (uit de Top30-app gekopieerd; de speler is verder los van de repo)
# --------------------------------------------------------------------------
DONKER = {
    "achtergrond": "#0f1116",
    "paneel": "#161a23",
    "paneel_licht": "#1d222d",
    "rand": "#262c3a",
    "tekst": "#e8ecf4",
    "tekst_zwak": "#98a1b3",
    "accent": "#5b8cff",
    "accent_hover": "#7aa2ff",
    "accent_tekst": "#0b1020",
    "ok": "#3ecf8e",
    "fout": "#ff6b6b",
    "waarschuwing": "#f2b544",
}

LICHT = {
    "achtergrond": "#f2f4f8",
    "paneel": "#ffffff",
    "paneel_licht": "#f7f9fc",
    "rand": "#d8dee9",
    "tekst": "#131722",
    "tekst_zwak": "#5c6675",
    "accent": "#3b6ef5",
    "accent_hover": "#2c58d8",
    "accent_tekst": "#ffffff",
    "ok": "#128a5b",
    "fout": "#c62b2b",
    "waarschuwing": "#a86a00",
}

MIDDERNACHT = {
    "achtergrond": "#0a1020",
    "paneel": "#111a30",
    "paneel_licht": "#17223d",
    "rand": "#22304f",
    "tekst": "#e6ecff",
    "tekst_zwak": "#8fa0c4",
    "accent": "#37c8ff",
    "accent_hover": "#5ed4ff",
    "accent_tekst": "#04121f",
    "ok": "#3ecf8e",
    "fout": "#ff6b6b",
    "waarschuwing": "#f2b544",
}

BOS = {
    "achtergrond": "#0c1310",
    "paneel": "#12201a",
    "paneel_licht": "#182a22",
    "rand": "#234034",
    "tekst": "#e4f2e9",
    "tekst_zwak": "#93b3a2",
    "accent": "#4dbf7a",
    "accent_hover": "#6ed094",
    "accent_tekst": "#06170e",
    "ok": "#8fe3b0",
    "fout": "#ff7a6b",
    "waarschuwing": "#e8c05a",
}

SEPIA = {
    "achtergrond": "#f4ecdc",
    "paneel": "#fffaf0",
    "paneel_licht": "#f8f0e0",
    "rand": "#ddceb4",
    "tekst": "#3a2f22",
    "tekst_zwak": "#7d6b52",
    "accent": "#b06a2c",
    "accent_hover": "#8f5620",
    "accent_tekst": "#fffaf0",
    "ok": "#2f7d4f",
    "fout": "#b23b2e",
    "waarschuwing": "#9a6a12",
}

NEON = {
    "achtergrond": "#0d0716",
    "paneel": "#160d24",
    "paneel_licht": "#1e1233",
    "rand": "#34204f",
    "tekst": "#f0e6ff",
    "tekst_zwak": "#b09ad0",
    "accent": "#c04dff",
    "accent_hover": "#d177ff",
    "accent_tekst": "#12031f",
    "ok": "#46e0b0",
    "fout": "#ff5f8a",
    "waarschuwing": "#ffcf5a",
}

# De thema's in de volgorde van het keuzemenu.
KLEUREN = {
    "donker": DONKER,
    "licht": LICHT,
    "middernacht": MIDDERNACHT,
    "bos": BOS,
    "sepia": SEPIA,
    "neon": NEON,
}

THEMA_NAMEN = {
    "donker": "Donker",
    "licht": "Licht",
    "middernacht": "Middernacht",
    "bos": "Bos",
    "sepia": "Sepia",
    "neon": "Neon",
}



def _als_getal(waarde: object) -> int:
    """Een getal uit de instellingen, of 0 als het er geen is.

    De settings.json is met de hand te wijzigen, dus hier kan van alles in
    staan: een getal, een tekst, `null`, of helemaal niets. Vandaar de
    omzettiging in plaats van `int(...)` dat om een exception zou vragen.
    """
    try:
        getal = int(waarde)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return getal if getal > 0 else 0


def _als_int(waarde: object, standaard: int = 0) -> int:
    """Een (ook negatief) getal uit de instellingen, of `standaard`."""
    try:
        return int(waarde)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return standaard


def stijlblad(kleuren: dict) -> str:
    """Bouw het stylesheet op uit het kleurenpalet."""
    return f"""
    QWidget {{
        background: {kleuren['achtergrond']};
        color: {kleuren['tekst']};
        font-size: 10pt;
    }}
    QMainWindow, QDialog {{ background: {kleuren['achtergrond']}; }}

    /* ---------- kopbalk ---------- */
    #kop {{
        background: {kleuren['paneel']};
        border-bottom: 1px solid {kleuren['rand']};
    }}
    #kop_titel {{ font-size: 15pt; font-weight: 600; background: transparent; }}
    #kop_sub {{ color: {kleuren['tekst_zwak']}; font-size: 9pt; background: transparent; }}

    /* ---------- kaarten ---------- */
    #rij {{ background: transparent; border: none; }}
    #kaart {{
        background: {kleuren['paneel']};
        border: 1px solid {kleuren['rand']};
        border-radius: 10px;
    }}
    #kaart_titel {{
        font-size: 9pt; font-weight: 600; color: {kleuren['tekst_zwak']};
        background: transparent; padding: 2px 0;
    }}

    /* ---------- invoer ---------- */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background: {kleuren['paneel_licht']};
        border: 1px solid {kleuren['rand']};
        border-radius: 7px;
        padding: 7px 10px;
        color: {kleuren['tekst']};
        selection-background-color: {kleuren['accent']};
        selection-color: {kleuren['accent_tekst']};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid {kleuren['accent']};
    }}
    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        color: {kleuren['tekst_zwak']};
    }}
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background: {kleuren['rand']}; border: none; width: 16px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background: {kleuren['accent']};
    }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
    QComboBox QAbstractItemView {{
        background: {kleuren['paneel']};
        border: 1px solid {kleuren['rand']};
        selection-background-color: {kleuren['accent']};
        outline: none; padding: 4px;
    }}

    /* ---------- knoppen ---------- */
    QPushButton {{
        background: {kleuren['paneel_licht']};
        border: 1px solid {kleuren['rand']};
        border-radius: 7px;
        padding: 8px 14px;
        color: {kleuren['tekst']};
    }}
    QPushButton:hover {{
        border-color: {kleuren['accent']};
        background: {kleuren['paneel']};
    }}
    QPushButton:pressed {{ background: {kleuren['rand']}; }}
    QPushButton:disabled {{ color: {kleuren['tekst_zwak']}; border-color: {kleuren['rand']}; }}
    QPushButton#hoofd_knop {{
        background: {kleuren['accent']};
        color: {kleuren['accent_tekst']};
        border: none;
        font-weight: 600;
        padding: 10px 22px;
        font-size: 10.5pt;
    }}
    QPushButton#hoofd_knop:hover {{ background: {kleuren['accent_hover']}; }}
    QPushButton#hoofd_knop:disabled {{ background: {kleuren['rand']}; color: {kleuren['tekst_zwak']}; }}
    QPushButton#stop_knop {{
        background: transparent;
        border: 1px solid {kleuren['fout']};
        color: {kleuren['fout']};
        font-weight: 600;
        padding: 10px 18px;
    }}
    QPushButton#stop_knop:hover {{ background: {kleuren['fout']}; color: #ffffff; }}
    QPushButton#stop_knop:disabled {{ border-color: {kleuren['rand']}; color: {kleuren['tekst_zwak']}; }}

    /* ---------- keuzes ---------- */
    QRadioButton, QCheckBox {{ background: transparent; spacing: 8px; padding: 2px; }}
    QRadioButton::indicator, QCheckBox::indicator {{
        width: 17px; height: 17px;
        border: 1px solid {kleuren['rand']};
        background: {kleuren['paneel_licht']};
    }}
    QRadioButton::indicator {{ border-radius: 9px; }}
    QCheckBox::indicator {{ border-radius: 5px; }}
    QRadioButton::indicator:hover, QCheckBox::indicator:hover {{ border-color: {kleuren['accent']}; }}
    QRadioButton::indicator:checked {{
        background: {kleuren['accent']};
        border: 3px solid {kleuren['paneel_licht']};
    }}
    QCheckBox::indicator:checked {{ background: {kleuren['accent']}; border-color: {kleuren['accent']}; }}
    QRadioButton:disabled, QCheckBox:disabled {{ color: {kleuren['tekst_zwak']}; }}

    /* ---------- voortgang ---------- */
    QProgressBar {{
        background: {kleuren['paneel_licht']};
        border: none; border-radius: 6px;
        height: 12px; text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: {kleuren['accent']};
        border-radius: 6px;
    }}

    /* ---------- console ---------- */
    #console {{
        background: {kleuren['paneel']};
        border: 1px solid {kleuren['rand']};
        border-radius: 10px;
        font-family: "{QFontDatabase.systemFont(QFontDatabase.FixedFont).family()}";
        font-size: 9pt;
    }}

    /* ---------- groepen ---------- */
    QGroupBox {{
        border: 1px solid {kleuren['rand']};
        border-radius: 10px;
        margin-top: 14px;
        background: transparent;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px; padding: 0 6px;
        color: {kleuren['tekst_zwak']};
    }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {kleuren['rand']}; border-radius: 5px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {kleuren['tekst_zwak']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    QToolTip {{
        background: {kleuren['paneel']};
        color: {kleuren['tekst']};
        border: 1px solid {kleuren['accent']};
        padding: 4px;
    }}
    """


# --------------------------------------------------------------------------


APP_TITEL = "Muziekspeler"

# Bestandstypen die de afspeellijst herkent. QtMultimedia speelt op
# macOS/Windows/Linux alles af wat het systeem aankan; hier worden alleen
# de gangbare muziekbestanden opgeraapt.
MEDIA_EXTENSIES = {
    ".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".opus", ".wma",
}

# "uit" → de afspeellijst stopt na het laatste nummer; "een" → herhaal
# hetzelfde nummer; "alle" → de hele lijst opnieuw.
HERHALEN_MODES = ["uit", "een", "alle"]


# --------------------------------------------------------------------------
# Tijd- en naamhulpen (los gehouden van het venster, zodat de zelftest ze
# snel kan draaien)
# --------------------------------------------------------------------------

def formaat_tijd(ms: int) -> str:
    """Milliseconden als m:ss, of u:mm:ss vanaf een uur."""
    totaal_s = max(0, round(ms / 1000))
    uren, rest = divmod(totaal_s, 3600)
    minuten, seconden = divmod(rest, 60)
    if uren:
        return f"{uren}:{minuten:02d}:{seconden:02d}"
    return f"{minuten}:{seconden:02d}"


def toon_naam(pad: Path) -> str:
    """Een leesbare naam: artiest - titel uit de tags, anders de bestandsnaam.

    Bij de Top30-bestanden staat er een nummer voor ("0017-ABBA - …"); dat
    wordt er voor de weergave afgehaald.
    """
    try:
        import mutagen
        bestand = mutagen.File(str(pad), easy=True)
    except Exception:
        bestand = None
    if bestand is not None:
        artiest = str(bestand.get("artist", [""])[0]).strip() if bestand.get("artist") else ""
        titel = str(bestand.get("title", [""])[0]).strip() if bestand.get("title") else ""
        if artiest and titel:
            return f"{artiest} - {titel}"
        if artiest or titel:
            return artiest or titel
    import re
    return re.sub(r"^\d+[\s_-]+", "", pad.stem)


def zoek_muziek(map_pad: Path, extensies: set[str] | None = None) -> list[Path]:
    """Alle muziekbestanden onder map_pad, op naam gesorteerd.

    Verborgen mappen (namen die met een punt beginnen) worden overgeslagen.
    """
    kegels = set(extensies or MEDIA_EXTENSIES)
    gevonden: list[Path] = []
    for pad in sorted(map_pad.rglob("*")):
        if pad.is_file() and pad.suffix.lower() in kegels:
            if any(deel.startswith(".") for deel in pad.parts[len(map_pad.parts):]):
                continue  # verborgen map overgeslagen
            gevonden.append(pad)
    return gevonden


def _extra_stijl(kleuren: dict) -> str:
    """De stijl voor de speler-onderdelen, bovenop het Top30-palet."""
    mono = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
    return f"""
    /* ---------- muziekspeler ---------- */
    #playlist {{
        background: {kleuren['paneel_licht']};
        border: 1px solid {kleuren['rand']};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    #playlist::item {{ padding: 4px 8px; border-radius: 5px; }}
    #playlist::item:hover {{ background: {kleuren['paneel']}; }}
    #playlist::item:selected {{
        background: {kleuren['accent']};
        color: {kleuren['accent_tekst']};
    }}
    #playlist::item:selected:hover {{ background: {kleuren['accent_hover']}; }}
    #nu_naam {{
        font-size: 12.5pt; font-weight: 600; background: transparent;
        border-bottom: 1px solid {kleuren['rand']}; padding-bottom: 8px;
    }}
    #tijd {{
        font-family: "{mono}"; font-size: 9pt; color: {kleuren['tekst_zwak']};
        background: transparent;
    }}
    QSlider::groove:horizontal {{
        background: {kleuren['paneel_licht']}; height: 6px; border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{ background: {kleuren['accent']}; border-radius: 3px; }}
    QSlider::handle:horizontal {{
        background: {kleuren['tekst']}; width: 14px; height: 14px;
        margin: -5px 0; border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{ background: {kleuren['accent']}; }}
    QSlider::handle:horizontal:pressed {{ background: {kleuren['accent_hover']}; }}
    QPushButton:checked {{
        background: {kleuren['accent']}; color: {kleuren['accent_tekst']};
        border-color: {kleuren['accent']};
    }}
    """


def speler_stijlblad(kleuren: dict) -> str:
    """Het volledige stylesheet: Top30-basis plus de speler-regels."""
    return stijlblad(kleuren) + _extra_stijl(kleuren)


# --------------------------------------------------------------------------
# Mengpaneel: een grafische equalizer in Winamp-stijl (10 banden + preamp).
#
# QMediaPlayer biedt in Qt6 geen DSP-haken tussen audio-uitgang en
# geluidskaart. Een ingeschakelde EQ speelt daarom een eigen, volledig
# gedeocodeerde en gefilterde geluidsstroom via QAudioSink; de QMediaPlayer
# blijft intussen de "gids" (klok, einde van het nummer, zoekbalk) - als de
# EQ aanstaat wordt zijn eigen geluid op volume 0 gezet.
# --------------------------------------------------------------------------

# De tien banden van de klassieke Winamp-equalizer: (frequentie, etiket).
EQUALIZER_BANDEN = [
    (60, "60"), (170, "170"), (310, "310"), (600, "600"),
    (1000, "1k"), (3000, "3k"), (6000, "6k"),
    (12000, "12k"), (14000, "14k"), (16000, "16k"),
]

EQ_BEREIK = 12        # elke fader loopt van -12 tot +12 dB
BIQUAD_Q = 1.1        # kwaliteitsfactor: brede, zachte bellen

# Voorgedefinieerde tooncurven (dB per band, in de volgorde van EQUALIZER_BANDEN).
# Het eerste item ("Eigen") betekent: geen preset, de handmatige stand.
EQ_PRESETS = [
    ("Eigen", None),
    ("Vlak", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ("Meer bas", [6, 5, 3, 1, 0, 0, 0, 0, 0, 0]),
    ("Minder bas", [-6, -5, -3, -1, 0, 0, 0, 0, 0, 0]),
    ("Stem", [-3, -2, 0, 2, 4, 4, 3, 1, 0, -1]),
    ("Pop", [-1, 0, 2, 4, 4, 2, 0, -1, -1, -1]),
    ("Rock", [5, 3, 1, -1, -1, 0, 1, 3, 4, 4]),
    ("Elektronisch", [5, 4, 2, 0, -1, 0, 1, 3, 5, 6]),
    ("Klassiek", [4, 3, 2, 1, 0, 0, -1, -1, -2, -2]),
    ("Spraak", [-6, -4, -1, 2, 4, 4, 2, 0, -1, -2]),
]


def peaking_coefficienten(versterking_db: float, frequentie: float,
                          monsterfrequentie: float) -> tuple[float, ...]:
    """Genormaliseerde biquad-coëfficiënten voor één peaking-EQ-band."""
    a = 10.0 ** (versterking_db / 40.0)
    w0 = math.tau * frequentie / monsterfrequentie
    alfa = math.sin(w0) / (2.0 * BIQUAD_Q)
    cosw = math.cos(w0)
    noemer = 1.0 + alfa / a
    return ((1.0 + alfa * a) / noemer, -2.0 * cosw / noemer,
            (1.0 - alfa * a) / noemer, -2.0 * cosw / noemer,
            (1.0 - alfa / a) / noemer)


def _filter16(waarde: float) -> int:
    """Een biquad-resultaat terugbrengen in het 16-bit bereik."""
    return max(-32768, min(32767, int(waarde)))


def _schaal16(waarde, soort, _kanalen: int) -> int:
    """Eén monster van het bronformaat naar 16-bit omzetten."""
    w = waarde
    if soort == QAudioFormat.SampleFormat.Float:
        w = max(-1.0, min(1.0, w)) * 32767
    elif soort == QAudioFormat.SampleFormat.Int32:
        w = w >> 16
    elif soort == QAudioFormat.SampleFormat.UInt8:
        w = (w - 128) * 256
    return _filter16(w)


def _pas_biquad(staat: list[float], kf: tuple[float, ...], x: float) -> float:
    """Eén TDF2-biquadstap voor één kanaal; houdt zijn eigen toestand bij."""
    b0, b1, b2, a1, a2 = kf
    x1, x2, y1, y2 = staat
    y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
    staat[1], staat[0], staat[3], staat[2] = x1, x, y1, y
    return y


def _ruw_stuk(blokken: list[bytes], start: int, frames: int) -> bytes:
    """`frames` 16-bit stereomonsters opvragen vanaf framenummer `start`.

    De gedecodeerde muziek ligt als losse blokken in het geheugen; dit
    schuift de blokken aan elkaar tot het gevraagde stukje (kan korter zijn
    dan gevraagd, aan het eind van het nummer).
    """
    uit = bytearray()
    rest = frames * 4
    verschuiving = start * 4
    for blok in blokken:
        if rest <= 0:
            break
        if verschuiving >= len(blok):
            verschuiving -= len(blok)
            continue
        hunk = blok[verschuiving:verschuiving + rest]
        uit += hunk
        rest -= len(hunk)
        verschuiving = 0
    return bytes(uit)


class EqFader(QSlider):
    """Verticale EQ-fader; een dubbelklik zet hem terug op 0 dB."""

    def __init__(self, ouder: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Vertical, ouder)
        self.setRange(-EQ_BEREIK, EQ_BEREIK)
        self.setFixedHeight(150)

    def mouseDoubleClickEvent(self, gebeurtenis) -> None:  # noqa: N802
        self.setValue(0)
        gebeurtenis.accept()



class Equalizerkanaal(QIODevice):
    """De geluidskaart trekt hier gefilterde monsters uit (pull-model).

    QAudioSink kan in Qt6 geen kladjes aannemen via `write`; het apparaat
    vraagt zelf om data. Deze device geeft op `readData` het volgende
    gestemde stukje terug dat de Equalizer ter plekke door de filters haalt.
    """

    def __init__(self, gelijkmaker: "Equalizer", ouder=None) -> None:
        super().__init__(ouder)
        self._gelijkmaker = gelijkmaker
        self.open(QIODevice.OpenModeFlag.ReadOnly)

    def bytesAvailable(self) -> int:  # noqa: N802
        return self._gelijkmaker.overblijvende_bytes()

    def readData(self, maxlen: int) -> bytes:  # noqa: N802
        return self._gelijkmaker.lees(maxlen)


class Decodeerder(QThread):
    """Decodeert één bron volledig tot 16-bit stereomonsters, op de
    achtergrond. De ruwe buffer wordt daarna in het geheugen bewaard."""

    gereed = Signal()

    def __init__(self, bron: str) -> None:
        super().__init__()
        self._bron = bron
        self._blokken: list[bytes] = []
        self._rate = 0

    @property
    def bron(self) -> str:
        return self._bron

    @property
    def blokken(self) -> list[bytes]:
        return self._blokken

    @property
    def rate(self) -> int:
        return self._rate

    def run(self) -> None:
        loop = QEventLoop()
        decoder = QAudioDecoder()
        decoder.setSource(QUrl(self._bron))
        decoder.finished.connect(loop.quit)
        decoder.bufferReady.connect(lambda: self._vang(decoder))
        decoder.start()
        QTimer.singleShot(120000, loop.quit)  # noodrem voor kapotte bronnen
        loop.exec()
        if self._rate and self._blokken:
            self.gereed.emit()

    def _vang(self, decoder: QAudioDecoder) -> None:
        buffer = decoder.read()
        if buffer.isValid():
            formaat = buffer.format()
            if self._rate == 0:
                self._rate = formaat.sampleRate()
            gegevens = bytes(buffer.data())
            if gegevens:
                self._blokken.append(
                    self._stereo16(gegevens, formaat.channelCount(),
                                   formaat.sampleFormat()))

    @staticmethod
    def _stereo16(gegevens: bytes, kanalen: int, soort) -> bytes:
        """Ruwe audiobytes omzetten naar 16-bit stereo (mono wordt gedubbeld)."""
        if soort == QAudioFormat.SampleFormat.Int16 and kanalen == 2:
            return gegevens
        if soort == QAudioFormat.SampleFormat.Float:
            waarden = array.array("f", gegevens)
        elif soort == QAudioFormat.SampleFormat.Int32:
            waarden = array.array("i", gegevens)
        elif soort == QAudioFormat.SampleFormat.UInt8:
            waarden = array.array("B", gegevens)
        else:
            waarden = array.array("h", gegevens)
        uit = array.array("h")
        stap = max(1, kanalen)
        einde = len(waarden) - (len(waarden) % stap)
        for i in range(0, einde, stap):
            links = waarden[i]
            rechts = waarden[i + 1] if kanalen >= 2 else links
            uit.append(_schaal16(links, soort, kanalen))
            uit.append(_schaal16(rechts, soort, kanalen))
        return uit.tobytes()


class Equalizer(QObject):
    """De geluidsweg van het mengpaneel: decodeert, filtert en speelt.

    Het nummer wordt één keer volledig gedecodeerd en als ruwe 16-bit
    stereobuffer bewaard. Bij het afspelen haalt de geluidskaart er zelf
    monsters uit; elke fader-beweging werkt direct op de nog komende
    monsters, want de filters zitten in de leesstroom zelf.
    """

    klaar = Signal()   # de ruwe buffer staat klaar; afspelen kan beginnen

    def __init__(self, ouder=None) -> None:
        super().__init__(ouder)
        self._ruw: list[bytes] = []
        self._monsters = 0
        self._index = 0
        self._rate = 44100
        self._draad: Decodeerder | None = None
        self._ladders: list[Decodeerder] = []
        self._gevraagd: str | None = None
        self._klaar_vlag = False
        self._actief = False
        self._pauze = False
        self._sink: QAudioSink | None = None
        self._kanaal: Equalizerkanaal | None = None
        self._sink_rate = 0
        self._teller = QTimer(self)
        self._teller.setInterval(10)
        self._teller.timeout.connect(self._pompen)
        self._volume = 1.0
        self._gedempt = False
        self._versterkingen = [0.0] * len(EQUALIZER_BANDEN)
        self._preamp = 0.0
        self._coeffs: list[tuple[float, ...]] = []
        self._staten: list[list[list[float]]] = []

    # ------------------------------------------------------------ toestand

    @property
    def bezig(self) -> bool:
        return self._draad is not None and self._draad.isRunning()

    @property
    def gereed(self) -> bool:
        return self._klaar_vlag

    @property
    def rate(self) -> int:
        return self._rate

    def vrijmaken(self) -> None:
        """Ruwe data loslaten (bij een nieuw nummer of uitschakelen)."""
        self._actief = False
        self._klaar_vlag = False
        self._ruw = []
        self._monsters = 0
        self._index = 0

    def sluit(self) -> None:
        """Bij het sluiten van het venster: wacht netjes op de decodeerdraden."""
        self._actief = False
        for draad in [self._draad, *self._ladders]:
            if draad is not None and draad.isRunning():
                draad.wait(3000)

    # --------------------------------------------------------------- beheer

    def vraag_aan(self, bron: str) -> None:
        """Op de achtergrond laten decoderen; een oudere taak wordt genegeerd."""
        self.vrijmaken()
        self._gevraagd = bron
        oude = self._draad
        if oude is not None and oude.isRunning():
            oude.finished.connect(lambda d=oude: self._ruim_oude_op(d))
            self._ladders.append(oude)
        draad = Decodeerder(bron)
        draad.gereed.connect(self._bij_draad_gereed)
        self._draad = draad
        draad.start()

    def _ruim_oude_op(self, draad: "Decodeerder") -> None:
        try:
            self._ladders.remove(draad)
        except ValueError:
            pass

    def _bij_draad_gereed(self) -> None:
        draad = self.sender()
        if draad is not self._draad or draad.bron != self._gevraagd:
            return  # verouderde taak van een vorig nummer
        self._ruw = draad.blokken
        self._rate = draad.rate
        self._monsters = sum(len(b) for b in self._ruw) // 4
        self._index = 0
        self._draad = None
        self._klaar_vlag = self._monsters > 0
        if self._klaar_vlag:
            self._herbereken()   # de filters met de echte monsterfrequentie
        self.klaar.emit()

    def zet_banden(self, versterkingen: list[float]) -> None:
        if len(versterkingen) != len(EQUALIZER_BANDEN):
            return
        self._versterkingen = list(versterkingen)
        self._herbereken()

    def zet_preamp(self, db: float) -> None:
        self._preamp = float(db)

    def zet_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        if self._sink is not None:
            self._sink.setVolume(0.0 if self._gedempt else self._volume)

    def zet_dempen(self, aan: bool) -> None:
        self._gedempt = aan
        if self._sink is not None:
            self._sink.setVolume(0.0 if aan else self._volume)

    # -------------------------------------------------------------- afspelen

    def begin(self, ms: int) -> bool:
        if not self._klaar_vlag:
            return False
        if self._sink is not None and self._sink_rate != self._rate:
            self._sink.stop()
            self._sink = None
            self._kanaal = None
        if self._sink is None:
            formaat = QAudioFormat()
            formaat.setSampleRate(self._rate)
            formaat.setChannelCount(2)
            formaat.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            self._sink = QAudioSink(formaat)
            self._sink_rate = self._rate
            self._kanaal = Equalizerkanaal(self, self)
            self._sink.start(self._kanaal)
            self._sink.setVolume(0.0 if self._gedempt else self._volume)
        self._index = max(0, min(self._monsters,
                                 int(ms / 1000.0 * self._rate)))
        self._pauze = False
        self._actief = True
        self._herbereken()   # toestanden opnieuw
        if not self._teller.isActive():
            self._teller.start()
        return True

    def pauze(self) -> None:
        self._pauze = True

    def hervat(self) -> None:
        self._pauze = False

    def stop(self) -> None:
        self._actief = False
        self._pauze = False

    def zoek(self, ms: int) -> None:
        self._index = max(0, min(self._monsters,
                                 int(ms / 1000.0 * self._rate)))
        self._herbereken()

    # --------------------------------------------------------------- kanaal

    def overblijvende_bytes(self) -> int:
        if not self._actief:
            return 0
        return max(0, (self._monsters - self._index) * 4)

    def _pompen(self) -> None:
        if self._actief and self._kanaal is not None:
            self._kanaal.readyRead.emit()

    def lees(self, maxlen: int) -> bytes:
        if self._pauze or not self._actief or self._index >= self._monsters:
            return b""
        frames = min(maxlen // 4, self._monsters - self._index)
        if frames <= 0:
            return b""
        ruw = self._lees_ruw(self._index, frames)
        zelfde = len(ruw) // 4
        self._index += zelfde
        if zelfde == 0:
            return b""
        if not self._coeffs and self._preamp == 0.0:
            return ruw
        return self._filter(ruw, zelfde)

    def _lees_ruw(self, start: int, frames: int) -> bytes:
        return _ruw_stuk(self._ruw, start, frames)

    def _filter(self, ruw: bytes, frames: int) -> bytes:
        waarden = array.array("h", ruw)
        uit = array.array("h")
        factor = 10.0 ** (self._preamp / 20.0)
        for i in range(frames):
            links = waarden[2 * i] * factor
            rechts = waarden[2 * i + 1] * factor
            for kf, staten in zip(self._coeffs, self._staten):
                links = _pas_biquad(staten[0], kf, links)
                rechts = _pas_biquad(staten[1], kf, rechts)
            uit.append(_filter16(links))
            uit.append(_filter16(rechts))
        return uit.tobytes()

    def _herbereken(self) -> None:
        zelf = []
        staten = []
        for nummer, (bandfreq, _etiket) in enumerate(EQUALIZER_BANDEN):
            versterking = self._versterkingen[nummer]
            if abs(versterking) < 0.3:
                continue  # een vlakke band kost niets
            zelf.append(peaking_coefficienten(versterking, bandfreq, self._rate))
            staten.append([[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]])
        self._coeffs = zelf
        self._staten = staten


# --------------------------------------------------------------------------
# Visualizer: een oscilloscoop ("scope") in Winamp-stijl. Het huidige nummer
# wordt op de achtergrond gedecodeerd; het venster tekent de golfvorm rond
# de plek waar de speler nu is. Alleen actief als het paneel open is.
# --------------------------------------------------------------------------

class Visualisator(QWidget):
    """Tekent de golfvorm van het nummer rond de huidige afspeelpositie."""

    VENSTER = 2048   # aantal monsters dat in beeld komt

    def __init__(self, ouder: QWidget | None = None) -> None:
        super().__init__(ouder)
        self.setFixedHeight(96)
        self.setMinimumWidth(320)
        self._ruw: list[bytes] = []
        self._monsters = 0
        self._rate = 44100
        self._url: str | None = None
        self._draad: Decodeerder | None = None
        self._ladders: list[Decodeerder] = []
        self._positie_ms = 0
        self._actief = False
        self._kleuren = DONKER
        self._teller = QTimer(self)
        self._teller.setInterval(33)   # ±30 beelden per seconde
        self._teller.timeout.connect(self.update)

    # --------------------------------------------------------------- beheer

    def zet_kleuren(self, kleuren: dict) -> None:
        self._kleuren = kleuren
        self.update()

    def start(self) -> None:
        self._actief = True
        if not self._teller.isActive():
            self._teller.start()
        if self._monsters == 0 and self._url:
            self.vraag_data()

    def stop(self) -> None:
        self._actief = False
        self._teller.stop()

    def stel_positie(self, ms: int) -> None:
        self._positie_ms = ms

    def stel_bron(self, url: str | None) -> None:
        """Bij een nieuw nummer: oude data loslaten en opnieuw decoderen."""
        if url == self._url and self._monsters:
            return
        self._url = url
        self._ruw = []
        self._monsters = 0
        self._positie_ms = 0
        if url and self._actief:
            self.vraag_data()
        self.update()

    def vraag_data(self) -> None:
        if not self._url:
            return
        oude = self._draad
        if oude is not None and oude.isRunning():
            oude.finished.connect(lambda d=oude: self._ruim_oude_op(d))
            self._ladders.append(oude)
        draad = Decodeerder(self._url)
        draad.gereed.connect(self._bij_gereed)
        self._draad = draad
        draad.start()

    def _ruim_oude_op(self, draad: "Decodeerder") -> None:
        try:
            self._ladders.remove(draad)
        except ValueError:
            pass

    def _bij_gereed(self) -> None:
        draad = self.sender()
        if draad is not self._draad or draad.bron != self._url:
            return  # verouderde taak
        self._ruw = draad.blokken
        self._rate = draad.rate
        self._monsters = sum(len(b) for b in self._ruw) // 4
        self._draad = None
        self.update()

    def sluit(self) -> None:
        self._actief = False
        for draad in [self._draad, *self._ladders]:
            if draad is not None and draad.isRunning():
                draad.wait(3000)

    # ---------------------------------------------------------------- tekenen

    def paintEvent(self, gebeurtenis) -> None:  # noqa: N802
        teken = QPainter(self)
        k = self._kleuren
        teken.fillRect(self.rect(), QColor(k["paneel_licht"]))
        teken.setPen(QPen(QColor(k["rand"]), 1))
        teken.drawRect(self.rect().adjusted(0, 0, -1, -1))
        midden = self.height() // 2

        if self._monsters == 0:
            teken.setPen(QPen(QColor(k["tekst_zwak"]), 1))
            teken.drawLine(6, midden, self.width() - 6, midden)
            teken.drawText(10, midden - 8, t("— geen golfvorm —"))
            return

        breedte = self.width()
        start = max(0, min(self._monsters - 1,
                           int(self._positie_ms / 1000.0 * self._rate)))
        ruw = _ruw_stuk(self._ruw, start, self.VENSTER)
        waarden = array.array("h", ruw)
        aantal = len(waarden) // 2
        if aantal < 2:
            return

        stap = max(1, aantal // max(1, breedte))
        teken.setPen(QPen(QColor(k["accent"]), 2))
        schaal = self.height() * 0.45
        vorige_x = 0
        vorige_y = midden - int(waarden[0] / 32768.0 * schaal)
        for x in range(1, breedte):
            i = min(aantal - 1, x * stap)
            y = midden - int(waarden[2 * i] / 32768.0 * schaal)
            teken.drawLine(vorige_x, vorige_y, x, y)
            vorige_x, vorige_y = x, y


# --------------------------------------------------------------------------
# De afspeellijst, met het accepteren van gesleepte bestanden en mappen
# --------------------------------------------------------------------------

class Afspeellijst(QListWidget):
    bestanden = Signal(list)  # lijst van paden (str), uit slepen of dialoog

    def __init__(self, ouder: QWidget | None = None) -> None:
        super().__init__(ouder)
        self.setObjectName("playlist")
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)

    def dragEnterEvent(self, gebeurtenis) -> None:
        if gebeurtenis.mimeData().hasUrls():
            gebeurtenis.acceptProposedAction()

    def dragMoveEvent(self, gebeurtenis) -> None:
        if gebeurtenis.mimeData().hasUrls():
            gebeurtenis.acceptProposedAction()

    def dropEvent(self, gebeurtenis) -> None:
        paden: list[str] = []
        for url in gebeurtenis.mimeData().urls():
            if url.isLocalFile():
                paden.append(url.toLocalFile())
        if paden:
            self.bestanden.emit(paden)
        gebeurtenis.acceptProposedAction()


# --------------------------------------------------------------------------
# Het venster
# --------------------------------------------------------------------------

class Muziekvenster(QMainWindow):
    def __init__(self, thema: str = "donker") -> None:
        super().__init__()
        self.setWindowTitle(t(APP_TITEL))
        self.setMinimumSize(900, 520)
        self.resize(1040, 640)

        # Geluid: de speler speelt via de systeem-uitgang.
        self.speler = QMediaPlayer(self)
        self.uitvoer = QAudioOutput(self)
        self.uitvoer.setVolume(0.8)
        self.speler.setAudioOutput(self.uitvoer)

        self.thema_naam = thema if thema in KLEUREN else "donker"
        self.kleuren = KLEUREN[self.thema_naam]

        self.huidige_index = -1
        self.herhaal_mode = 0      # stand "uit"
        self.willekeurig = False
        self._sleept = False       # de gebruiker sleept de voortgangsbalk
        self._onthouden = True     # de zelftest zet dit uit via _onthoud()
        self._laadt_instellingen = False

        # Mengpaneel: de equalizer speelt een eigen gefilterde geluidsstroom.
        self.eq = Equalizer(self)
        self.eq.klaar.connect(self._eq_bij_gereed)
        self.eq_actief = False     # of de gebruiker de EQ wil
        self.eq_speelt = False     # of de EQ nu daadwerkelijk de klank doet
        self._eq_preset_bezig = False
        self._nu_staat = "kies"       # "kies" / "gestopt" / "naam" / "fout"
        self._nu_extra = ""
        self._eq_status_sleutel: tuple[str, dict] | None = None

        # Visualizer: een oscilloscoop over de gedecodeerde golfvorm.
        self.viz = Visualisator(self)

        self._bouw_venster()
        self._koppel_geluid()
        self._laad_instellingen()
        self._geef_stijl()

    # ------------------------------------------------------------ opbouw

    def _bouw_venster(self) -> None:
        centraal = QWidget()
        kolom = QVBoxLayout(centraal)
        kolom.setContentsMargins(0, 0, 0, 0)
        kolom.setSpacing(0)

        # Kopbalk, net als in Top30.
        kop = QFrame()
        kop.setObjectName("kop")
        kopbalk = QHBoxLayout(kop)
        kopbalk.setContentsMargins(16, 10, 16, 10)
        kop_titel = QLabel(t(APP_TITEL))
        kop_titel.setObjectName("kop_titel")
        self.kop_titel = kop_titel
        kop_sub = QLabel(t("Een Winamp-light in Python, in de Top30-stijl"))
        kop_sub.setObjectName("kop_sub")
        self.kop_sub = kop_sub
        kop_tekst = QVBoxLayout()
        kop_tekst.setSpacing(0)
        kop_tekst.addWidget(kop_titel)
        kop_tekst.addWidget(kop_sub)
        kopbalk.addLayout(kop_tekst)
        kopbalk.addStretch(1)
        self.kies_taal = QComboBox()
        self.kies_taal.setToolTip(t("Taal"))
        for code, naam in TAAL_NAMEN.items():
            self.kies_taal.addItem(naam, code)
        self.kies_taal.currentIndexChanged.connect(self._wissel_taal)
        kopbalk.addWidget(self.kies_taal)
        self.kies_thema = QComboBox()
        self.kies_thema.setToolTip(t("Thema"))
        for naam in KLEUREN:
            self.kies_thema.addItem(t(THEMA_NAMEN[naam]), naam)
        self.kies_thema.currentIndexChanged.connect(self._wissel_thema)
        kopbalk.addWidget(self.kies_thema)
        kolom.addWidget(kop)

        # Twee kaarten: links de afspeellijst, rechts de bediening.
        inhoud = QHBoxLayout()
        inhoud.setContentsMargins(16, 14, 16, 14)
        inhoud.setSpacing(14)

        links = QFrame()
        links.setObjectName("kaart")
        links_rij = QVBoxLayout(links)
        links_rij.setContentsMargins(14, 12, 14, 14)
        links_titel = QLabel(t("AFSPELLIJST"))
        links_titel.setObjectName("kaart_titel")
        self.links_titel = links_titel
        links_rij.addWidget(links_titel)

        self.playlist = Afspeellijst()
        self.playlist.itemDoubleClicked.connect(
            lambda item: self.speel(self.playlist.row(item)))
        # Zowel "Map kiezen", "Bestanden…" als het slepen van bestanden/mappen
        # komt via dit signaal binnen.
        self.playlist.bestanden.connect(self.voeg_bestanden_toe)
        links_rij.addWidget(self.playlist, 1)

        rij_knop = QHBoxLayout()
        self.knop_map = QPushButton(t("Map kiezen…"))
        self.knop_map.clicked.connect(self._kies_map)
        self.knop_bestanden = QPushButton(t("Bestanden…"))
        self.knop_bestanden.clicked.connect(self._kies_bestanden)
        self.knop_wis = QPushButton(t("Wis"))
        self.knop_wis.clicked.connect(self._wis_lijst)
        rij_knop.addWidget(self.knop_map)
        rij_knop.addWidget(self.knop_bestanden)
        rij_knop.addStretch(1)
        rij_knop.addWidget(self.knop_wis)
        links_rij.addLayout(rij_knop)

        inhoud.addWidget(links, 3)

        rechts = QFrame()
        rechts.setObjectName("kaart")
        rechts_rij = QVBoxLayout(rechts)
        rechts_rij.setContentsMargins(14, 12, 14, 14)
        speler_titel = QLabel(t("SPELER"))
        speler_titel.setObjectName("kaart_titel")
        self.speler_titel = speler_titel
        rechts_rij.addWidget(speler_titel)

        self.nu_naam = QLabel(t("— kies een nummer —"))
        self.nu_naam.setObjectName("nu_naam")
        self.nu_naam.setWordWrap(True)
        self.nu_naam.setMinimumHeight(46)
        rechts_rij.addWidget(self.nu_naam)

        # Voortgang: positie, balk en totale duur.
        voortgang = QHBoxLayout()
        voortgang.setSpacing(8)
        self.tijd_huidig = QLabel("0:00")
        self.tijd_huidig.setObjectName("tijd")
        self.tijd_totaal = QLabel("0:00")
        self.tijd_totaal.setObjectName("tijd")
        self.tijd_totaal.setAlignment(Qt.AlignRight)
        self.schuif_voortgang = QSlider(Qt.Horizontal)
        self.schuif_voortgang.sliderMoved.connect(self._mors_balk)
        self.schuif_voortgang.sliderPressed.connect(
            lambda: setattr(self, "_sleept", True))
        self.schuif_voortgang.sliderReleased.connect(self._los_balk)
        voortgang.addWidget(self.tijd_huidig)
        voortgang.addWidget(self.schuif_voortgang, 1)
        voortgang.addWidget(self.tijd_totaal)
        rechts_rij.addLayout(voortgang)

        # Openen-van: vorige, speel/pauze, volgende, stoppen.
        open = QHBoxLayout()
        open.setSpacing(8)
        self.knop_vorige = QPushButton(t("⏮ Vorige"))
        self.knop_vorige.clicked.connect(self.vorige)
        self.knop_afspelen = QPushButton(t("Afspelen"))
        self.knop_afspelen.setObjectName("hoofd_knop")
        self.knop_afspelen.clicked.connect(self.afspelen_of_pauzeren)
        self.knop_volgende = QPushButton(t("Volgende ⏭"))
        self.knop_volgende.clicked.connect(self.volgende)
        self.knop_stop = QPushButton(t("Stoppen"))
        self.knop_stop.setObjectName("stop_knop")
        self.knop_stop.clicked.connect(self.stoppen)
        open.addWidget(self.knop_vorige)
        open.addWidget(self.knop_afspelen, 1)
        open.addWidget(self.knop_volgende)
        open.addWidget(self.knop_stop)
        rechts_rij.addLayout(open)

        # Opties en volume.
        opties = QHBoxLayout()
        opties.setSpacing(8)
        self.knop_willekeurig = QPushButton(t("Willekeurig"))
        self.knop_willekeurig.setCheckable(True)
        self.knop_willekeurig.toggled.connect(
            lambda aan: setattr(self, "willekeurig", aan))
        self.knop_herhalen = QPushButton()
        self.knop_herhalen.setCheckable(True)
        self.knop_herhalen.clicked.connect(self._wissel_herhalen)
        opties.addWidget(self.knop_willekeurig)
        opties.addWidget(self.knop_herhalen)
        opties.addStretch(1)
        self.knop_dempen = QPushButton(t("Dempen"))
        self.knop_dempen.setCheckable(True)
        self.knop_dempen.toggled.connect(self._zet_dempen)
        self.schuif_volume = QSlider(Qt.Horizontal)
        self.schuif_volume.setRange(0, 100)
        self.schuif_volume.setValue(80)
        self.schuif_volume.setFixedWidth(170)
        self.schuif_volume.valueChanged.connect(self._zet_volume)
        self.volume_tekst = QLabel("80%")
        self.volume_tekst.setObjectName("tijd")
        opties.addWidget(self.knop_dempen)
        opties.addWidget(self.schuif_volume)
        opties.addWidget(self.volume_tekst)
        rechts_rij.addLayout(opties)

        self._bouw_eq_paneel(rechts_rij)
        self._bouw_viz_paneel(rechts_rij)

        rechts_rij.addStretch(1)

        inhoud.addWidget(rechts, 4)
        kolom.addLayout(inhoud, 1)
        self.setCentralWidget(centraal)

        # Sneltoetsen.
        QShortcut(QKeySequence("Space"), self, self.afspelen_of_pauzeren)
        QShortcut(QKeySequence("Ctrl+O"), self, self._kies_map)
        QShortcut(QKeySequence("Ctrl+Left"), self, self.vorige)
        QShortcut(QKeySequence("Ctrl+Right"), self, self.volgende)
        QShortcut(QKeySequence("Ctrl+H"), self, lambda: self._wissel_herhalen())
        QShortcut(QKeySequence("Ctrl+M"), self, self.knop_dempen.click)

    def _koppel_geluid(self) -> None:
        self.speler.positionChanged.connect(self._bij_voortgang)
        self.speler.durationChanged.connect(self._bij_duur)
        self.speler.playbackStateChanged.connect(self._bij_toestand)
        self.speler.mediaStatusChanged.connect(self._bij_status)
        self.speler.errorOccurred.connect(self._bij_fout)

    # --------------------------------------------------------- instellingen

    def _laad_instellingen(self) -> None:
        self._laadt_instellingen = True
        opslag = QSettings("Muziekspeler", APP_TITEL)
        self.schuif_volume.setValue(int(opslag.value("volume", 80)))
        self.knop_willekeurig.setChecked(opslag.value("willekeurig", False) in
                                         (True, "true", "1"))
        self.herhaal_mode = 0
        self.knop_herhalen.setChecked(False)
        self._zet_herhalen_tekst()
        banden = opslag.value("eq_banden", [0] * len(EQUALIZER_BANDEN))
        if not isinstance(banden, list):
            banden = [0] * len(EQUALIZER_BANDEN)
        for i, fader in enumerate(self.eq_faders):
            waarde = _als_int(banden[i]) if i < len(banden) else 0
            fader.setValue(max(-EQ_BEREIK, min(EQ_BEREIK, waarde)))
        self.eq_preamp.setValue(
            max(-EQ_BEREIK, min(EQ_BEREIK, _als_int(opslag.value("eq_preamp", 0)))))
        self.eq_aan_k.setChecked(
            opslag.value("eq_aan", False) in (True, "true", "1"))
        self.kies_preset.setCurrentIndex(0)   # de banden komen uit de opslag
        for i in range(self.kies_taal.count()):
            if self.kies_taal.itemData(i) == TAAL:
                self.kies_taal.setCurrentIndex(i)
                break
        for i in range(self.kies_thema.count()):
            if self.kies_thema.itemData(i) == self.thema_naam:
                self.kies_thema.setCurrentIndex(i)
                break
        self.viz_open_k.setChecked(
            opslag.value("viz_open", False) in (True, "true", "1"))
        self._laadt_instellingen = False

    def _onthoud(self) -> None:
        if not self._onthouden or self._laadt_instellingen:
            return
        opslag = QSettings("Muziekspeler", APP_TITEL)
        opslag.setValue("thema", self.thema_naam)
        opslag.setValue("taal", TAAL)
        opslag.setValue("volume", self.schuif_volume.value())
        opslag.setValue("willekeurig", self.willekeurig)
        opslag.setValue("eq_banden", [f.value() for f in self.eq_faders])
        opslag.setValue("eq_preamp", self.eq_preamp.value())
        opslag.setValue("eq_aan", self.eq_aan_k.isChecked())
        opslag.setValue("viz_open", self.viz_open_k.isChecked())

    def closeEvent(self, gebeurtenis) -> None:  # noqa: N802 (Qt-naam)
        self._onthoud()
        self.eq.stop()
        self.eq.sluit()
        self.viz.sluit()
        super().closeEvent(gebeurtenis)

    # --------------------------------------------------------------- stijl

    def _geef_stijl(self) -> None:
        self.setStyleSheet(speler_stijlblad(self.kleuren))
        self.viz.zet_kleuren(self.kleuren)

    def _wissel_thema(self, index: int) -> None:
        if index < 0:
            return
        naam = self.kies_thema.itemData(index)
        if naam not in KLEUREN:
            return
        self.thema_naam = naam
        self.kleuren = KLEUREN[naam]
        self._geef_stijl()
        self._onthoud()

    # ------------------------------------------------------------------ taal

    def _wissel_taal(self, index: int) -> None:
        if index < 0:
            return
        code = self.kies_taal.itemData(index)
        zet_taal(code)
        self._hertaal()
        self._onthoud()

    def _hertaal(self) -> None:
        """Alle teksten opnieuw zetten in de gekozen taal."""
        self.setWindowTitle(t(APP_TITEL))
        self.kop_titel.setText(t(APP_TITEL))
        self.kop_sub.setText(t("Een Winamp-light in Python, in de Top30-stijl"))
        self.kies_taal.setToolTip(t("Taal"))
        self.kies_thema.setToolTip(t("Thema"))
        for i in range(self.kies_thema.count()):
            self.kies_thema.setItemText(i, t(THEMA_NAMEN[self.kies_thema.itemData(i)]))
        self.links_titel.setText(t("AFSPELLIJST"))
        self.speler_titel.setText(t("SPELER"))
        self.knop_map.setText(t("Map kiezen…"))
        self.knop_bestanden.setText(t("Bestanden…"))
        self.knop_wis.setText(t("Wis"))
        self.knop_vorige.setText(t("⏮ Vorige"))
        self.knop_volgende.setText(t("Volgende ⏭"))
        self.knop_stop.setText(t("Stoppen"))
        self.knop_willekeurig.setText(t("Willekeurig"))
        self.knop_dempen.setText(t("Dempen"))
        self.knop_eq.setText(t("Equalizer"))
        self.eq_aan_k.setText(t("EQ aan"))
        self.preset_label.setText(t("Preset"))
        self.kies_preset.setToolTip(t("Kies een vooraf ingestelde tooncurve"))
        for i, (naam, _waarden) in enumerate(EQ_PRESETS):
            self.kies_preset.setItemText(i, t(naam))
        for fader, (_freq, etiket) in zip(self.eq_faders, EQUALIZER_BANDEN):
            fader.setToolTip(t("{etiket} Hz (dubbelklik = 0)").format(etiket=etiket))
        self.eq_preamp.setToolTip(t("Preamp (dubbelklik = 0)"))
        self.pre_naam.setText(t("Pre"))
        self.viz_open_k.setText(t("Visualizer"))
        self._zet_herhalen_tekst()
        speelt = (self.speler.playbackState()
                  == QMediaPlayer.PlaybackState.PlayingState)
        self.knop_afspelen.setText(t("Pauze") if speelt else t("Afspelen"))
        self._teken_nu()
        self._teken_eq_status()

    # ------------------------------------------------------------ statusregels

    def _stel_nu_kies(self) -> None:
        self._nu_staat, self._nu_extra = "kies", ""
        self._teken_nu()

    def _stel_nu_gestopt(self) -> None:
        self._nu_staat, self._nu_extra = "gestopt", ""
        self._teken_nu()

    def _stel_nu_naam(self, naam: str) -> None:
        self._nu_staat, self._nu_extra = "naam", naam
        self._teken_nu()

    def _stel_nu_fout(self, bericht: str) -> None:
        self._nu_staat, self._nu_extra = "fout", bericht
        self._teken_nu()

    def _teken_nu(self) -> None:
        if self._nu_staat == "naam":
            self.nu_naam.setText(self._nu_extra)
        elif self._nu_staat == "gestopt":
            self.nu_naam.setText(t("— gestopt —"))
        elif self._nu_staat == "fout":
            self.nu_naam.setText(
                t("Kan dit nummer niet afspelen:\n{boodschap}")
                .format(boodschap=self._nu_extra))
        else:
            self.nu_naam.setText(t("— kies een nummer —"))

    def _stel_eq_status(self, sleutel: str | None = None, **velden) -> None:
        self._eq_status_sleutel = None if sleutel is None else (sleutel, velden)
        self._teken_eq_status()

    def _teken_eq_status(self) -> None:
        if self._eq_status_sleutel is None:
            self.eq_status.setText("")
            return
        sleutel, velden = self._eq_status_sleutel
        self.eq_status.setText(t(sleutel).format(**velden))

    # ---------------------------------------------------------- afspeellijst

    def aantal(self) -> int:
        return self.playlist.count()

    def _pad_van(self, rij: int) -> str | None:
        item = self.playlist.item(rij)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def voeg_bestanden_toe(self, paden: list[str]) -> int:
        """Bestanden of mappen toevoegen; geeft het aantal nieuwe nummers terug."""
        was_leeg = self.aantal() == 0
        nieuw = 0
        bestaande = {
            self._pad_van(i) for i in range(self.aantal())
        }
        for ruw in paden:
            pad = Path(ruw)
            if pad.is_dir():
                kandidaten = zoek_muziek(pad)
            elif pad.is_file() and pad.suffix.lower() in MEDIA_EXTENSIES:
                kandidaten = [pad]
            else:
                continue
            for bestand in kandidaten:
                sleutel = str(bestand)
                if sleutel in bestaande:
                    continue
                item = QListWidgetItem(
                    f"{self.aantal() + 1}. {toon_naam(bestand)}")
                item.setData(Qt.UserRole, sleutel)
                self.playlist.addItem(item)
                bestaande.add(sleutel)
                nieuw += 1
        van_start_af = (
            self.speler.playbackState() == QMediaPlayer.PlaybackState.StoppedState
            and self.huidige_index == -1)
        if was_leeg and nieuw and van_start_af:
            self.speel(0)  # alsof Winamp: meteen beginnen
        self._zet_besturing()
        return nieuw

    def _kies_map(self) -> None:
        map_naam = QFileDialog.getExistingDirectory(self, t("Kies een map met muziek"))
        if map_naam:
            self.playlist.bestanden.emit([map_naam])

    def _kies_bestanden(self) -> None:
        soorten = " ".join(f"*{v}" for v in sorted(MEDIA_EXTENSIES))
        namen, _ = QFileDialog.getOpenFileNames(
            self, t("Kies muziekbestanden"), "",
            t("Muziek ({soorten})").format(soorten=soorten))
        if namen:
            self.playlist.bestanden.emit(namen)

    def _wis_lijst(self) -> None:
        self.stoppen()
        self.playlist.clear()
        self.huidige_index = -1
        self._stel_nu_kies()
        self.schuif_voortgang.setValue(0)
        self.tijd_huidig.setText("0:00")
        self.tijd_totaal.setText("0:00")
        self._zet_besturing()

    # ----------------------------------------------------------- afspelen

    def speel(self, rij: int) -> None:
        if not 0 <= rij < self.aantal():
            return
        self.huidige_index = rij
        item = self.playlist.item(rij)
        self.playlist.setCurrentRow(rij)
        self.playlist.scrollToItem(item)
        pad = self._pad_van(rij)
        self._stel_nu_naam(self._naam_van(rij))
        self.nu_naam.setToolTip(pad or "")
        self.speler.stop()
        self.speler.setSource(QUrl.fromLocalFile(pad or ""))
        self.speler.play()
        self._zet_besturing()
        self._eq_routeer()
        self.viz.stel_bron(pad)

    def _naam_van(self, rij: int) -> str:
        item = self.playlist.item(rij)
        return item.text() if item is not None else ""

    def afspelen_of_pauzeren(self) -> None:
        if self.aantal() == 0:
            return
        if self.huidige_index == -1:
            self.speel(0)
            return
        if self.speler.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.speler.pause()
        else:
            self.speler.play()

    def stoppen(self) -> None:
        self.speler.stop()
        self.eq.stop()
        if self.aantal():
            self._stel_nu_gestopt()
        else:
            self._stel_nu_kies()

    def vorige(self) -> None:
        if self.huidige_index == -1:
            self.speel(0)
            return
        if self.speler.position() > 3000:
            self.speler.setPosition(0)  # langer dan 3 s: opnieuw beginnen
            self.eq.zoek(0)
            return
        volgend = self.huidige_index - 1
        if volgend < 0:
            volgend = (self.aantal() - 1 if self.herhaal_mode == 2 else 0)
        self.speel(volgend)

    def volgende(self) -> None:
        volgend = self._volgende_index()
        if volgend is None:
            self.stoppen()  # einde van de lijst en niet herhalen
            return
        self.speel(volgend)

    def _volgende_index(self) -> int | None:
        """Het volgende indexnummer, rekening houdend met willekeurig en herhalen."""
        if self.aantal() == 0:
            return None
        if self.willekeurig and self.aantal() > 1:
            over = [i for i in range(self.aantal()) if i != self.huidige_index]
            return random.choice(over)
        volgend = self.huidige_index + 1
        if volgend < self.aantal():
            return volgend
        if self.herhaal_mode == 2:  # "alle"
            return 0
        return None

    # ------------------------------------------------------------ geluidsdraden

    def _bij_toestand(self, stand: QMediaPlayer.PlaybackState) -> None:
        speelt = stand == QMediaPlayer.PlaybackState.PlayingState
        self.knop_afspelen.setText(t("Pauze") if speelt else t("Afspelen"))
        self._zet_besturing()
        if not self.eq_actief:
            return
        if speelt:
            self.eq.hervat()
        elif stand == QMediaPlayer.PlaybackState.PausedState:
            self.eq.pauze()
        else:
            self.eq.stop()

    def _bij_voortgang(self, positie: int) -> None:
        if not self._sleept:
            self.schuif_voortgang.setValue(positie)
        self.tijd_huidig.setText(formaat_tijd(positie))
        self.viz.stel_positie(positie)

    def _bij_duur(self, duur: int) -> None:
        self.schuif_voortgang.setRange(0, duur)
        self.tijd_totaal.setText(formaat_tijd(duur))

    def _bij_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.herhaal_mode == 1:
                self.speel(self.huidige_index)  # "één"
            else:
                self.volgende()

    def _bij_fout(self, fout: QMediaPlayer.Error, boodschap: str) -> None:
        if fout == QMediaPlayer.Error.NoError:
            return
        self.stoppen()                # eerst stoppen, daarna de fout tonen
        self._stel_nu_fout(boodschap)

    def _mors_balk(self, positie: int) -> None:
        self._sleept = True
        self.tijd_huidig.setText(formaat_tijd(positie))

    def _los_balk(self) -> None:
        self._sleept = False
        positie = self.schuif_voortgang.value()
        self.speler.setPosition(positie)
        self.eq.zoek(positie)

    def _zet_herhalen_tekst(self) -> None:
        etiket = {"uit": t("Herhalen: uit"), "een": t("Herhalen: één"),
                  "alle": t("Herhalen: alle")}
        self.knop_herhalen.setText(etiket[HERHALEN_MODES[self.herhaal_mode]])
        self.knop_herhalen.setChecked(self.herhaal_mode != 0)

    def _wissel_herhalen(self, _aan: bool | None = None) -> None:
        self.herhaal_mode = (self.herhaal_mode + 1) % len(HERHALEN_MODES)
        self._zet_herhalen_tekst()

    def _zet_volume(self, waarde: int) -> None:
        self.volume_tekst.setText(f"{waarde}%")
        self.eq.zet_volume(waarde / 100)
        self._zet_gids_volume()

    def _zet_besturing(self) -> None:
        heeft = self.aantal() > 0
        voorbij = heeft and self.huidige_index != -1
        self.knop_afspelen.setEnabled(heeft)
        self.knop_vorige.setEnabled(heeft)
        self.knop_volgende.setEnabled(heeft)
        self.knop_stop.setEnabled(voorbij)
        self.schuif_voortgang.setEnabled(voorbij)

    # ------------------------------------------------------------- mengpaneel

    def _bouw_eq_paneel(self, rij: QVBoxLayout) -> None:
        """De Equalizer-knop en het faderpaneel eronder in de speler-kaart."""
        self.knop_eq = QPushButton(t("Equalizer"))
        self.knop_eq.setCheckable(True)
        self.knop_eq.toggled.connect(self._eq_toonbaar)
        rij.addWidget(self.knop_eq)

        self.eq_paneel = QWidget()
        kolom = QVBoxLayout(self.eq_paneel)
        kolom.setContentsMargins(0, 0, 0, 0)
        kolom.setSpacing(6)

        knoppen = QHBoxLayout()
        knoppen.setSpacing(8)
        self.eq_aan_k = QCheckBox(t("EQ aan"))
        self.eq_aan_k.toggled.connect(self._eq_schakel)
        knop_standaard = QPushButton(t("Standaard"))
        knop_standaard.clicked.connect(self._eq_standaard)
        knoppen.addWidget(self.eq_aan_k)
        knoppen.addWidget(knop_standaard)
        knoppen.addSpacing(12)
        preset_label = QLabel(t("Preset"))
        self.preset_label = preset_label
        knoppen.addWidget(preset_label)
        self.kies_preset = QComboBox()
        for naam, _waarden in EQ_PRESETS:
            self.kies_preset.addItem(t(naam))
        self.kies_preset.setToolTip(t("Kies een vooraf ingestelde tooncurve"))
        self.kies_preset.currentIndexChanged.connect(self._eq_preset)
        knoppen.addWidget(self.kies_preset)
        knoppen.addStretch(1)
        self.eq_status = QLabel("")
        self.eq_status.setObjectName("tijd")
        knoppen.addWidget(self.eq_status)
        kolom.addLayout(knoppen)

        faders = QHBoxLayout()
        faders.setSpacing(8)
        self.eq_faders: list[QSlider] = []
        self.eq_waarden: list[QLabel] = []
        for _freq, etiket in EQUALIZER_BANDEN:
            vak = QVBoxLayout()
            vak.setSpacing(2)
            fader = EqFader()
            fader.setValue(0)
            fader.setToolTip(t("{etiket} Hz (dubbelklik = 0)").format(etiket=etiket))
            fader.valueChanged.connect(self._eq_band_gewijzigd)
            waarde = QLabel("0")
            waarde.setObjectName("tijd")
            waarde.setAlignment(Qt.AlignCenter)
            naam = QLabel(etiket)
            naam.setObjectName("tijd")
            naam.setAlignment(Qt.AlignCenter)
            vak.addWidget(fader, 0, Qt.AlignHCenter)
            vak.addWidget(waarde)
            vak.addWidget(naam)
            faders.addLayout(vak)
            self.eq_faders.append(fader)
            self.eq_waarden.append(waarde)

        # De preamp-fader helemaal rechts, net als op de Winamp-EQ.
        vak = QVBoxLayout()
        vak.setSpacing(2)
        self.eq_preamp = EqFader()
        self.eq_preamp.setValue(0)
        self.eq_preamp.setToolTip(t("Preamp (dubbelklik = 0)"))
        self.eq_preamp.valueChanged.connect(self._eq_preamp_gewijzigd)
        self.eq_preamp_waarde = QLabel("0")
        self.eq_preamp_waarde.setObjectName("tijd")
        self.eq_preamp_waarde.setAlignment(Qt.AlignCenter)
        pre_naam = QLabel(t("Pre"))
        pre_naam.setObjectName("tijd")
        pre_naam.setAlignment(Qt.AlignCenter)
        self.pre_naam = pre_naam
        vak.addWidget(self.eq_preamp, 0, Qt.AlignHCenter)
        vak.addWidget(self.eq_preamp_waarde)
        vak.addWidget(pre_naam)
        faders.addLayout(vak)
        faders.addStretch(1)
        kolom.addLayout(faders)

        self.eq_paneel.setVisible(False)
        rij.addWidget(self.eq_paneel)

    def _eq_toonbaar(self, aan: bool) -> None:
        self.eq_paneel.setVisible(aan)

    def _eq_band_gewijzigd(self, _waarde: int) -> None:
        fader = self.sender()
        if fader not in self.eq_faders:
            return
        nummer = self.eq_faders.index(fader)
        self.eq_waarden[nummer].setText(str(fader.value()))
        self.eq.zet_banden([f.value() for f in self.eq_faders])
        if not self._eq_preset_bezig:
            self.kies_preset.setCurrentIndex(0)   # handmatig = "Eigen"
        self._onthoud()

    def _eq_preamp_gewijzigd(self, waarde: int) -> None:
        self.eq_preamp_waarde.setText(str(waarde))
        self.eq.zet_preamp(waarde)
        self._onthoud()

    def _eq_preset(self, index: int) -> None:
        """Een vooraf ingestelde tooncurve op de faders zetten."""
        if index <= 0 or index >= len(EQ_PRESETS):
            return
        _naam, waarden = EQ_PRESETS[index]
        if waarden is None:
            return
        self._eq_preset_bezig = True
        try:
            for fader, waarde in zip(self.eq_faders, waarden):
                fader.setValue(int(waarde))
        finally:
            self._eq_preset_bezig = False
        self.eq.zet_banden([float(w) for w in waarden])
        self._onthoud()

    def _eq_standaard(self) -> None:
        self.kies_preset.setCurrentIndex(1)   # "Vlak"
        self._eq_preset(1)                    # ook als hij al op 1 stond
        self.eq_preamp.setValue(0)

    def _eq_schakel(self, aan: bool) -> None:
        self.eq_actief = aan
        self._onthoud()
        if not aan:
            self.eq.stop()
            self.eq_speelt = False
            self._stel_eq_status(None)
            self._zet_gids_volume()
            return
        self._eq_routeer()

    def _eq_routeer(self) -> None:
        """De EQ het huidige nummer laten verwerken en overnemen.

        Tijdens het decoderen blijft de gids gewoon hoorbaar; pas als de
        gefilterde stroom klaarstaat neemt de EQ het over.
        """
        if not self.eq_actief:
            return
        self.eq_speelt = False
        self._zet_gids_volume()
        pad = self._pad_van(self.huidige_index) if self.huidige_index != -1 else None
        if not pad:
            self._stel_eq_status("EQ wacht op een nummer.")
            return
        self.eq.vraag_aan(pad)
        self._stel_eq_status("EQ verwerkt nummer…")

    def _eq_bij_gereed(self) -> None:
        if not self.eq_actief:
            return
        if self.eq.begin(self.speler.position()):
            self.eq_speelt = True
            self._zet_gids_volume()   # de gids speelt voortaan stil
            self._stel_eq_status("EQ actief ({rate} kHz)",
                                 rate=f"{self.eq.rate / 1000:.0f}")
        else:
            self.eq_speelt = False
            self._zet_gids_volume()
            self._stel_eq_status("EQ kan dit nummer niet verwerken.")

    def _zet_dempen(self, aan: bool) -> None:
        self.uitvoer.setMuted(aan)
        self.eq.zet_dempen(aan)

    def _zet_gids_volume(self) -> None:
        basis = self.schuif_volume.value() / 100
        self.uitvoer.setVolume(0.0 if self.eq_speelt else basis)

    # ------------------------------------------------------------ visualizer

    def _bouw_viz_paneel(self, rij: QVBoxLayout) -> None:
        """De Visualizer-knop en de oscilloscoop eronder."""
        self.viz_open_k = QPushButton(t("Visualizer"))
        self.viz_open_k.setCheckable(True)
        self.viz_open_k.toggled.connect(self._viz_schakel)
        rij.addWidget(self.viz_open_k)

        self.viz_paneel = QWidget()
        viz_kolom = QVBoxLayout(self.viz_paneel)
        viz_kolom.setContentsMargins(0, 0, 0, 0)
        viz_kolom.setSpacing(6)
        self.viz.zet_kleuren(self.kleuren)
        viz_kolom.addWidget(self.viz)
        self.viz_paneel.setVisible(False)
        rij.addWidget(self.viz_paneel)

    def _viz_schakel(self, aan: bool) -> None:
        self.viz_paneel.setVisible(aan)
        if aan:
            self.viz.stel_bron(self._pad_van(self.huidige_index)
                               if self.huidige_index != -1 else None)
            self.viz.start()
        else:
            self.viz.stop()
        self._onthoud()


# --------------------------------------------------------------------------
# Starten
# --------------------------------------------------------------------------

def maak_app() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_TITEL)
    return app


def start(thema: str | None = None) -> int:
    app = maak_app()
    opslag = QSettings("Muziekspeler", APP_TITEL)
    if thema is None:
        thema = str(opslag.value("thema", "donker"))
    zet_taal(opslag.value("taal", systeemtaal()))
    venster = Muziekvenster(thema)
    venster.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(start())