# Musikspieler

[Nederlands](README.md) · [English](README_ENG.md) · [Français](README_FR.md) · **Deutsch**

Ein Musikspieler im Stil von [Top30](https://github.com/EsseteeStuff), ein
„Winamp-light", gebaut mit **PySide6** (Qt 6). Du öffnest einen Musikordner
oder ziehst Dateien in das Fenster und spielst sie ab. Das Aussehen lässt sich
mit mehreren Designs ändern, und die gesamte Oberfläche ist in vier Sprachen
verfügbar.

## Funktionen

- **Wiedergabeliste** — wähle einen Ordner (`Ordner wählen…`) oder einzelne
  Dateien (`Dateien…`), oder ziehe Dateien/Ordner in das Fenster. Versteckte
  Ordner werden übersprungen.
- **Anzeige** — zeigt `Interpret - Titel` aus den Tags (über
  [mutagen](https://mutagen.readthedocs.io)); gibt es kein Tag, den Dateinamen
  ohne die führende Nummer.
- **Bedienung** — Wiedergabe/Pause, Zurück, Weiter und Stopp, mit einem
  verschiebbaren Fortschrittsbalken und Lautstärke mit Stummschaltung.
- **Wiedergabemodi** — Zufällig und Wiederholen (aus → eins → alle).
- **Equalizer** — ein grafisches Mischpult mit zehn Bändern (60 Hz – 16 kHz)
  plus Vorverstärker, im Winamp-Stil. Inklusive Voreinstellungen (Flach,
  Mehr/Weniger Bass, Stimme, Pop, Rock, Elektronisch, Klassisch, Sprache); ein
  Doppelklick auf einen Fader setzt ihn auf 0 dB zurück.
- **Visualisierer** — ein Oszilloskop, das die Wellenform um die aktuelle
  Wiedergabeposition zeichnet (±30 Bilder pro Sekunde).
- **Designs** — Dunkel, Hell, Mitternacht, Wald, Sepia und Neon.
- **Sprachen** — Niederländisch, Englisch, Deutsch und Französisch; die
  Systemsprache bestimmt die Startsprache, in der Titelleiste kannst du
  wechseln.
- **Einstellungen** — Design, Sprache, Lautstärke, EQ-Stände und der
  Visualisierer werden zwischen Sitzungen beibehalten (über `QSettings`).

## Voraussetzungen

- Python 3.10 oder neuer (entwickelt und getestet mit 3.15)
- Die Pakete aus [`requirements.txt`](requirements.txt), darunter PySide6 6.12
  und mutagen
- Ein System mit Qt-Multimedia-Unterstützung (macOS, Windows oder Linux)

## Installation

```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Starten

Das mitgelieferte Startskript findet seinen eigenen Ordner, verwendet die venv
daneben und übergibt etwaige Argumente an `muziekspeler.py`. Es darf also
überall liegen, auch als Verknüpfung in deinem `PATH`:

```sh
./muziekspeler
```

Oder direkt mit Python:

```sh
.venv/bin/python muziekspeler.py
```

## Tastenkürzel

| Taste         | Aktion                        |
| ------------- | ----------------------------- |
| `Leertaste`   | Wiedergabe / Pause            |
| `Ctrl+O`      | einen Ordner wählen           |
| `Ctrl+Links`  | vorheriger Titel              |
| `Ctrl+Rechts` | nächster Titel                |
| `Ctrl+H`      | Wiederholen (aus → eins → alle) |
| `Ctrl+M`      | Stumm                         |

## Über den Equalizer

Qt 6 bietet keine DSP-Schnittstelle zwischen Audioausgang und Soundkarte. Sobald
du den Equalizer einschaltest, dekodiert die App den Titel daher vollständig im
Hintergrund zu 16-Bit-Stereo-Samples und spielt diese über einen eigenen
`QAudioSink` ab, während der `QMediaPlayer` weiterhin als Führung für die Uhr,
das Ende des Titels und den Suchbalken dient. Die Filter sitzen im Lesestrom
selbst, sodass eine Fader-Bewegung sofort hörbar ist.

## macOS: App-Bundel

`launcher.c` ist ein kleines Startprogramm für ein `.app`-Bundel. Es liegt in
`Contents/MacOS/Muziekspeler` und bindet Python über die Framework-Bibliothek
ein. Da das ausführbare Programm im eigenen Bundel liegt, verwendet macOS die
`Info.plist` der App für das Dock-Symbol und den Namen in der Menüleiste (statt
des Python-Symbols).

Bauen (mit dem Python-Framework von Homebrew):

```sh
PY_FW=/opt/homebrew/opt/python@3.15/Frameworks
clang launcher.c -o Muziekspeler \
    -F"$PY_FW" -framework Python \
    -I"$PY_FW/Python.framework/Versions/3.15/include/python3.15"
```

Kopiere das Ergebnis nach `Contents/MacOS/Muziekspeler` im Bundel und signiere
neu (ad-hoc genügt für lokale Nutzung):

```sh
codesign --force --sign - Muziekspeler.app
```

Das Startprogramm sucht den Projektordner (mit `muziekspeler.py` und `.venv`)
beim Start selbst, du kannst das Projekt also verschieben, ohne das Bundel neu
zu bauen. Die Reihenfolge ist:

1. die Umgebungsvariable `MUZIEKSPELER_HOME`;
2. der gespeicherte Pfad in `~/Library/Application Support/Muziekspeler/home`;
3. die Suche nach oben vom Bundel selbst (praktisch, wenn die `.app` im Projekt
   liegt);
4. `~/MusicPlayer` und `~/Projects/MusicPlayer`;
5. dein Home-Ordner selbst und `~/Projects`;
6. die direkten Unterordner deines Home-Ordners und von `~/Projects`.

Der gefundene Pfad wird für den nächsten Start gemerkt. Willst du einen
bestimmten Ordner erzwingen, starte mit `MUZIEKSPELER_HOME=/pfad/zum/projekt`.

## Lizenz

Dieses Projekt steht unter der
[GNU General Public License v3.0](LICENSE).
