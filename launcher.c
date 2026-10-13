/* Klein startprogramma voor Muziekspeler.
 *
 * Dit programma staat in de appbundel (Contents/MacOS/Muziekspeler) en sluit
 * Python in via de framework-bibliotheek. Omdat het uitvoerbare bestand in
 * onze eigen bundel zit, gebruikt macOS onze Info.plist voor het Dock-icoon en
 * de naam in de menubalk (in plaats van het Python-icoon).
 *
 * Het draait /Users/serge/MusicPlayer/muziekspeler.py met de pakketten uit de
 * venv.
 */
#include <Python.h>
#include <stdlib.h>

#define APP_MAP    "/Users/serge/MusicPlayer"
#define SCRIPT     APP_MAP "/muziekspeler.py"
#define SITE_PAK   APP_MAP "/.venv/lib/python3.15/site-packages"

int main(int argc, char **argv) {
    /* Laat de ingesloten Python de pakketten uit de venv vinden. */
    char oude_pad[8192];
    const char *vorige = getenv("PYTHONPATH");
    if (vorige && vorige[0]) {
        snprintf(oude_pad, sizeof(oude_pad), "%s:%s", SITE_PAK, vorige);
    } else {
        snprintf(oude_pad, sizeof(oude_pad), "%s", SITE_PAK);
    }
    setenv("PYTHONPATH", oude_pad, 1);
    setenv("PYTHONEXECUTABLE", APP_MAP "/.venv/bin/python", 1);

    /* Nieuwe argumentenlijst: [programma, script, ...oorspronkelijke args] */
    int n = argc + 1;
    char **nieuw = (char **)malloc(sizeof(char *) * (n + 1));
    if (!nieuw) return 1;
    nieuw[0] = argv[0];
    nieuw[1] = (char *)SCRIPT;
    for (int i = 1; i < argc; i++) {
        nieuw[i + 1] = argv[i];
    }
    nieuw[n] = NULL;

    return Py_BytesMain(n, nieuw);
}
