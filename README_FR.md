# Lecteur de musique

[Nederlands](README.md) · [English](README_ENG.md) · **Français** · [Deutsch](README_DE.md)

Un lecteur de musique dans le style de [Top30](https://github.com/EsseteeStuff),
un « Winamp-light » construit avec **PySide6** (Qt 6). Ouvrez un dossier de
musique ou glissez des fichiers dans la fenêtre et lancez la lecture.
L'apparence est personnalisable avec plusieurs thèmes et toute l'interface est
disponible en quatre langues.

## Fonctionnalités

- **Liste de lecture** — choisissez un dossier (`Choisir un dossier…`) ou des
  fichiers isolés (`Fichiers…`), ou glissez des fichiers/dossiers dans la
  fenêtre. Les dossiers cachés sont ignorés.
- **Affichage** — affiche `artiste - titre` à partir des balises (via
  [mutagen](https://mutagen.readthedocs.io)) ; s'il n'y a pas de balise, le nom
  du fichier sans le numéro initial.
- **Commandes** — lecture/pause, précédent, suivant et arrêt, avec une barre de
  progression déplaçable et le volume avec sourdine.
- **Modes de lecture** — aléatoire et répétition (non → un → tous).
- **Égaliseur** — une table de mixage graphique à dix bandes (60 Hz – 16 kHz)
  plus préampli, dans le style Winamp. Avec des préréglages (Plat, Plus/Moins de
  basses, Voix, Pop, Rock, Électronique, Classique, Parole) ; un double-clic sur
  un fader le remet à 0 dB.
- **Visualiseur** — un oscilloscope qui dessine la forme d'onde autour de la
  position de lecture actuelle (±30 images par seconde).
- **Thèmes** — sombre, clair, minuit, forêt, sépia et néon.
- **Langues** — néerlandais, anglais, allemand et français ; la langue du
  système détermine la langue de départ et vous pouvez en changer dans la barre
  de titre.
- **Réglages** — le thème, la langue, le volume, les réglages de l'égaliseur et
  le visualiseur sont mémorisés entre les sessions (via `QSettings`).

## Prérequis

- Python 3.10 ou plus récent (développé et testé avec 3.15)
- Les paquets de [`requirements.txt`](requirements.txt), dont PySide6 6.12 et
  mutagen
- Un système avec prise en charge du multimédia Qt (macOS, Windows ou Linux)

## Installation

```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

Le script de démarrage fourni repère son propre dossier, utilise l'environnement
virtuel (venv) situé à côté et transmet les éventuels arguments à
`muziekspeler.py`. Il peut donc se trouver n'importe où, y compris comme lien
dans votre `PATH` :

```sh
./muziekspeler
```

Ou directement avec Python :

```sh
.venv/bin/python muziekspeler.py
```

## Raccourcis clavier

| Touche              | Action                          |
| ------------------- | ------------------------------- |
| `Espace`            | lecture / pause                 |
| `Ctrl+O`            | choisir un dossier              |
| `Ctrl+Flèche gauche`| piste précédente                |
| `Ctrl+Flèche droite`| piste suivante                  |
| `Ctrl+H`            | répétition (non → un → tous)    |
| `Ctrl+M`            | sourdine                        |

## À propos de l'égaliseur

Qt 6 n'offre pas de point d'accroche DSP entre la sortie audio et la carte son.
Dès que vous activez l'égaliseur, l'application décode donc entièrement la piste
en arrière-plan en échantillons stéréo 16 bits et les lit via son propre
`QAudioSink`, tandis que le `QMediaPlayer` continue de servir de guide pour
l'horloge, la fin de la piste et la barre de recherche. Les filtres se trouvent
dans le flux de lecture lui-même, de sorte qu'un déplacement de fader est
immédiatement audible.

## macOS : bundle d'application

`launcher.c` est un petit programme de lancement pour un bundle `.app`. Il se
trouve dans `Contents/MacOS/Muziekspeler` et intègre Python via la bibliothèque
framework. Comme l'exécutable se trouve dans notre propre bundle, macOS utilise
l'`Info.plist` de l'application pour l'icône du Dock et le nom dans la barre de
menus (au lieu de l'icône Python).

Compilation (avec le framework Python de Homebrew) :

```sh
PY_FW=/opt/homebrew/opt/python@3.15/Frameworks
clang launcher.c -o Muziekspeler \
    -F"$PY_FW" -framework Python \
    -I"$PY_FW/Python.framework/Versions/3.15/include/python3.15"
```

Copiez le résultat dans `Contents/MacOS/Muziekspeler` du bundle et signez de
nouveau (une signature ad hoc suffit pour un usage local) :

```sh
codesign --force --sign - Muziekspeler.app
```

Le lanceur recherche le dossier du projet (avec `muziekspeler.py` et `.venv`) au
démarrage, vous pouvez donc déplacer le projet sans recompiler le bundle.
L'ordre est le suivant :

1. la variable d'environnement `MUZIEKSPELER_HOME` ;
2. le chemin enregistré dans `~/Library/Application Support/Muziekspeler/home` ;
3. la recherche vers le haut depuis le bundle lui-même (pratique quand le `.app`
   se trouve dans le projet) ;
4. `~/MusicPlayer` et `~/Projects/MusicPlayer` ;
5. votre dossier personnel lui-même et `~/Projects` ;
6. les sous-dossiers directs de votre dossier personnel et de `~/Projects`.

Le chemin trouvé est mémorisé pour le prochain démarrage. Pour forcer un dossier
précis, lancez avec `MUZIEKSPELER_HOME=/chemin/vers/projet`.

## Licence

Ce projet est publié sous la
[GNU General Public License v3.0](LICENSE).
