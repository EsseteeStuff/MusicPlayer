# Muziekspeler

**Nederlands** · [English](README_ENG.md) · [Français](README_FR.md) · [Deutsch](README_DE.md)

Een muziekspeler in de stijl van [Top30](https://github.com/EsseteeStuff),
een "Winamp-light" gebouwd met **PySide6** (Qt 6). Je opent een map met
muziek of sleept bestanden in het venster en speelt ze af. De vormgeving is
aanpasbaar met meerdere thema's en de hele interface is beschikbaar in vier
talen.

## Functies

- **Afspeellijst** — kies een map (`Map kiezen…`) of losse bestanden
  (`Bestanden…`), of sleep bestanden/mappen in het venster. Verborgen mappen
  worden overgeslagen.
- **Weergave** — toont `artiest - titel` uit de tags (via
  [mutagen](https://mutagen.readthedocs.io)); is er geen tag, dan de
  bestandsnaam zonder het voorloopnummer.
- **Bediening** — afspelen/pauzeren, vorige, volgende en stoppen, met een
  voortgangsbalk die je kunt verslepen, en volume met dempen.
- **Afspeelmodi** — willekeurig en herhalen (uit → één → alle).
- **Equalizer** — een grafische mengpaneel met tien banden (60 Hz – 16 kHz)
  plus preamp, in Winamp-stijl. Inclusief presets (Vlak, Meer/Minder bas,
  Stem, Pop, Rock, Elektronisch, Klassiek, Spraak); een dubbelklik op een
  fader zet hem terug op 0 dB.
- **Visualizer** — een oscilloscoop die de golfvorm rond de huidige
  afspeelpositie tekent (±30 beelden per seconde).
- **Thema's** — donker, licht, middernacht, bos, sepia en neon.
- **Talen** — Nederlands, Engels, Duits en Frans; de systeemtaal kiest de
  starttaal en in de kopbalk kun je wisselen.
- **Instellingen** — thema, taal, volume, EQ-standen en de visualizer worden
  onthouden tussen sessies (via `QSettings`).

## Vereisten

- Python 3.10 of nieuwer (ontwikkeld en getest met 3.15)
- De pakketten uit [`requirements.txt`](requirements.txt), waaronder PySide6
  6.12 en mutagen
- Een systeem met Qt-multimedia-ondersteuning (macOS, Windows of Linux)

## Installatie

```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Starten

Het meegeleverde startscript zoekt zijn eigen map op, gebruikt de venv ernaast
en geeft eventuele argumenten door aan `muziekspeler.py`. Het mag dus overal
staan, ook als koppeling op je `PATH`:

```sh
./muziekspeler
```

Of rechtstreeks met Python:

```sh
.venv/bin/python muziekspeler.py
```

## Sneltoetsen

| Toets        | Actie                         |
| ------------ | ----------------------------- |
| `Spatie`     | afspelen / pauzeren           |
| `Ctrl+O`     | een map kiezen                |
| `Ctrl+Links` | vorige nummer                 |
| `Ctrl+Rechts`| volgende nummer               |
| `Ctrl+H`     | herhalen (uit → één → alle)   |
| `Ctrl+M`     | dempen                        |

## Over de equalizer

Qt 6 biedt geen DSP-haak tussen de audiouitgang en de geluidskaart. Zodra je de
equalizer aanzet, decodeert de app het nummer daarom volledig op de achtergrond
naar 16-bit-stereomonsters en speelt die via een eigen `QAudioSink`, terwijl de
`QMediaPlayer` als gids blijft dienen voor de klok, het einde van het nummer en
de zoekbalk. De filters zitten in de leesstroom zelf, zodat een verschuiving van
een fader direct hoorbaar is.

## macOS: appbundel

`launcher.c` is een klein startprogramma voor een `.app`-bundel. Het staat in
`Contents/MacOS/Muziekspeler` en sluit Python in via de framework-bibliotheek.
Omdat het uitvoerbare bestand in de eigen bundel zit, gebruikt macOS de
`Info.plist` van de app voor het Dock-icoon en de naam in de menubalk (in plaats
van het Python-icoon).

Bouwen (met de Python-framework van Homebrew):

```sh
PY_FW=/opt/homebrew/opt/python@3.15/Frameworks
clang launcher.c -o Muziekspeler \
    -F"$PY_FW" -framework Python \
    -I"$PY_FW/Python.framework/Versions/3.15/include/python3.15"
```

Kopieer het resultaat naar `Contents/MacOS/Muziekspeler` in de bundel en
onderteken opnieuw (ad-hoc volstaat voor lokaal gebruik):

```sh
codesign --force --sign - Muziekspeler.app
```

De launcher zoekt de projectmap (met `muziekspeler.py` en `.venv`) bij het
starten zelf op, dus je kunt het project verhuizen zonder de bundel opnieuw te
bouwen. De volgorde is:

1. de omgevingsvariabele `MUZIEKSPELER_HOME`;
2. het bewaarde pad in `~/Library/Application Support/Muziekspeler/home`;
3. omhoog zoeken vanaf de bundel zelf (handig als de `.app` in het project
   staat);
4. `~/MusicPlayer` en `~/Projects/MusicPlayer`;
5. je thuismap zelf en `~/Projects`;
6. de directe submappen van je thuismap en van `~/Projects`.

Het gevonden pad wordt onthouden voor de volgende start. Wil je een bepaalde
map forceren, dan start je met `MUZIEKSPELER_HOME=/pad/naar/project`.

## Licentie

Dit project valt onder de [GNU General Public License v3.0](LICENSE).
