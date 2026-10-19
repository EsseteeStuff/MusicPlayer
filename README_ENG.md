# Music Player

[Nederlands](README.md) · **English** · [Français](README_FR.md) · [Deutsch](README_DE.md)

A music player in the style of [Top30](https://github.com/EsseteeStuff), a
"Winamp-light" built with **PySide6** (Qt 6). Open a folder of music or drag
files into the window and play them. The look can be changed with several
themes, and the whole interface is available in four languages.

## Features

- **Playlist** — choose a folder (`Choose folder…`) or individual files
  (`Files…`), or drag files/folders into the window. Hidden folders are
  skipped.
- **Display** — shows `artist - title` from the tags (via
  [mutagen](https://mutagen.readthedocs.io)); if there is no tag, the file
  name without the leading number.
- **Controls** — play/pause, previous, next and stop, with a progress bar you
  can drag, and volume with mute.
- **Playback modes** — shuffle and repeat (off → one → all).
- **Equalizer** — a graphical mixing panel with ten bands (60 Hz – 16 kHz)
  plus preamp, in Winamp style. Includes presets (Flat, More/Less bass, Vocal,
  Pop, Rock, Electronic, Classical, Speech); double-clicking a fader resets it
  to 0 dB.
- **Visualizer** — an oscilloscope that draws the waveform around the current
  playback position (±30 frames per second).
- **Themes** — dark, light, midnight, forest, sepia and neon.
- **Languages** — Dutch, English, German and French; the system language
  selects the initial one and you can switch in the title bar.
- **Settings** — theme, language, volume, EQ positions and the visualizer are
  remembered between sessions (via `QSettings`).

## Requirements

- Python 3.10 or newer (developed and tested with 3.15)
- The packages from [`requirements.txt`](requirements.txt), including PySide6
  6.12 and mutagen
- A system with Qt multimedia support (macOS, Windows or Linux)

## Installation

```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

The included start script locates its own folder, uses the venv beside it and
passes any arguments to `muziekspeler.py`. It can therefore live anywhere,
including as a link on your `PATH`:

```sh
./muziekspeler
```

Or directly with Python:

```sh
.venv/bin/python muziekspeler.py
```

## Keyboard shortcuts

| Key           | Action                        |
| ------------- | ----------------------------- |
| `Space`       | play / pause                  |
| `Ctrl+O`      | choose a folder               |
| `Ctrl+Left`   | previous track                |
| `Ctrl+Right`  | next track                    |
| `Ctrl+H`      | repeat (off → one → all)      |
| `Ctrl+M`      | mute                          |

## About the equalizer

Qt 6 offers no DSP hook between the audio output and the sound card. As soon as
you switch the equalizer on, the app therefore fully decodes the track in the
background to 16-bit stereo samples and plays them through its own
`QAudioSink`, while the `QMediaPlayer` keeps serving as the guide for the clock,
the end of the track and the seek bar. The filters sit in the read stream
itself, so moving a fader is audible immediately.

## macOS: app bundle

`launcher.c` is a small launcher program for a `.app` bundle. It sits in
`Contents/MacOS/Muziekspeler` and embeds Python via the framework library.
Because the executable sits in our own bundle, macOS uses the app's
`Info.plist` for the Dock icon and the name in the menu bar (instead of the
Python icon).

Build (with the Homebrew Python framework):

```sh
PY_FW=/opt/homebrew/opt/python@3.15/Frameworks
clang launcher.c -o Muziekspeler \
    -F"$PY_FW" -framework Python \
    -I"$PY_FW/Python.framework/Versions/3.15/include/python3.15"
```

Copy the result to `Contents/MacOS/Muziekspeler` in the bundle and sign it
again (ad-hoc is enough for local use):

```sh
codesign --force --sign - Muziekspeler.app
```

The launcher looks up the project folder (with `muziekspeler.py` and `.venv`)
at startup, so you can move the project without rebuilding the bundle. The
order is:

1. the `MUZIEKSPELER_HOME` environment variable;
2. the saved path in `~/Library/Application Support/Muziekspeler/home`;
3. searching upwards from the bundle itself (handy when the `.app` is inside
   the project);
4. `~/MusicPlayer` and `~/Projects/MusicPlayer`;
5. your home folder itself and `~/Projects`;
6. the direct subfolders of your home folder and of `~/Projects`.

The path found is remembered for the next start. To force a particular folder,
start with `MUZIEKSPELER_HOME=/path/to/project`.

## License

This project is released under the
[GNU General Public License v3.0](LICENSE).
