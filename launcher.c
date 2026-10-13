/* Klein startprogramma voor Muziekspeler.
 *
 * Dit programma staat in de appbundel (Contents/MacOS/Muziekspeler) en sluit
 * Python in via de framework-bibliotheek. Omdat het uitvoerbare bestand in
 * onze eigen bundel zit, gebruikt macOS onze Info.plist voor het Dock-icoon en
 * de naam in de menubalk (in plaats van het Python-icoon).
 *
 * De projectmap (met muziekspeler.py en .venv) wordt bij het starten opgezocht,
 * zodat de bundel blijft werken als je het project verhuist. De volgorde is:
 *
 *   1. de omgevingsvariabele MUZIEKSPELER_HOME;
 *   2. het bewaarde pad in ~/Library/Application Support/Muziekspeler/home;
 *   3. omhoog zoeken vanaf de eigen bundel (handig als de .app in het project
 *      zelf staat);
 *   4. ~/MusicPlayer en ~/Projects/MusicPlayer;
 *   5. de thuismap zelf en ~/Projects;
 *   6. de directe submappen van de thuismap en van ~/Projects (met een
 *      voorkeur voor een map die "MusicPlayer" heet).
 *
 * Een gevonden pad wordt in het configuratiebestand bewaard, zodat volgende
 * starts meteen goed zijn.
 */
#include <Python.h>

#include <dirent.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define MAX_PAD 4096
#define PROJECT_NAAM "MusicPlayer"
#define PROJECT_BESTAND "muziekspeler.py"
#define VENV_PYTHON ".venv/bin/python"
#define CONFIG_MAP "Library/Application Support/Muziekspeler/home"

static int is_bestand(const char *pad) {
    struct stat st;
    return stat(pad, &st) == 0 && S_ISREG(st.st_mode);
}

static int is_map(const char *pad) {
    struct stat st;
    return stat(pad, &st) == 0 && S_ISDIR(st.st_mode);
}

/* Een geldige projectmap bevat muziekspeler.py én de venv-python. */
static int is_project(const char *map) {
    char pad[MAX_PAD];
    if (map == NULL || map[0] == '\0') {
        return 0;
    }
    snprintf(pad, sizeof(pad), "%s/%s", map, PROJECT_BESTAND);
    if (!is_bestand(pad)) {
        return 0;
    }
    snprintf(pad, sizeof(pad), "%s/%s", map, VENV_PYTHON);
    return is_bestand(pad);
}

/* Is `map` een projectmap? Zo ja, dan naar `uit` kopiëren. */
static int probeer(const char *map, char *uit, size_t grootte) {
    if (is_project(map)) {
        snprintf(uit, grootte, "%s", map);
        return 1;
    }
    return 0;
}

/* De map van het draaiende programma (zonder de bestandsnaam). */
static void eigen_map(char *uit, size_t grootte) {
    char ruw[MAX_PAD];
    char echt[MAX_PAD];
    uint32_t n = (uint32_t)sizeof(ruw);

    uit[0] = '\0';
    if (_NSGetExecutablePath(ruw, &n) != 0) {
        return;
    }
    if (realpath(ruw, echt) == NULL) {
        snprintf(echt, sizeof(echt), "%s", ruw);
    }
    char *schuine = strrchr(echt, '/');
    if (schuine != NULL) {
        *schuine = '\0';
    }
    snprintf(uit, grootte, "%s", echt);
}

/* Zoek een projectmap in `start` en in elke bovenliggende map. */
static int zoek_omhoog(const char *start, char *uit, size_t grootte) {
    char map[MAX_PAD];
    snprintf(map, sizeof(map), "%s", start);
    for (;;) {
        if (is_project(map)) {
            snprintf(uit, grootte, "%s", map);
            return 1;
        }
        char *schuine = strrchr(map, '/');
        if (schuine == NULL) {
            return 0;
        }
        if (schuine == map) {
            map[1] = '\0';   /* "/iets" wordt "/" */
            if (is_project(map)) {
                snprintf(uit, grootte, "%s", map);
                return 1;
            }
            return 0;
        }
        *schuine = '\0';
    }
}

/* Zoek een projectmap in de directe submappen van `map` (niet recursief).
 * Vindt hij er meer dan één, dan wint de map die "MusicPlayer" heet. */
static int zoek_in_buren(const char *map, char *uit, size_t grootte) {
    DIR *d = opendir(map);
    if (d == NULL) {
        return 0;
    }
    char eerste[MAX_PAD];
    eerste[0] = '\0';
    int gevonden = 0;
    struct dirent *item;
    while (!gevonden && (item = readdir(d)) != NULL) {
        if (item->d_name[0] == '.') {
            continue;
        }
        char sub[MAX_PAD];
        snprintf(sub, sizeof(sub), "%s/%s", map, item->d_name);
        if (!is_project(sub)) {
            continue;
        }
        if (strcmp(item->d_name, PROJECT_NAAM) == 0) {
            snprintf(uit, grootte, "%s", sub);
            gevonden = 1;
        } else if (eerste[0] == '\0') {
            snprintf(eerste, sizeof(eerste), "%s", sub);
        }
    }
    closedir(d);
    if (!gevonden && eerste[0] != '\0') {
        snprintf(uit, grootte, "%s", eerste);
        gevonden = 1;
    }
    return gevonden;
}

/* Het pad van het bewaarde configuratiebestand. */
static void config_pad(char *uit, size_t grootte) {
    const char *thuis = getenv("HOME");
    uit[0] = '\0';
    if (thuis == NULL || thuis[0] == '\0') {
        return;
    }
    snprintf(uit, grootte, "%s/%s", thuis, CONFIG_MAP);
}

/* Het bewaarde projectpad lezen; leeg of ongeldig telt als "niet gevonden". */
static int lees_config(char *uit, size_t grootte) {
    char pad[MAX_PAD];
    config_pad(pad, sizeof(pad));
    if (pad[0] == '\0') {
        return 0;
    }
    FILE *f = fopen(pad, "r");
    if (f == NULL) {
        return 0;
    }
    if (fgets(uit, (int)grootte, f) == NULL) {
        fclose(f);
        return 0;
    }
    fclose(f);
    size_t n = strlen(uit);
    while (n > 0 && (uit[n - 1] == '\n' || uit[n - 1] == '\r' ||
                     uit[n - 1] == ' ' || uit[n - 1] == '\t')) {
        uit[--n] = '\0';
    }
    return is_project(uit);
}

/* Een map aanmaken, inclusief ontbrekende bovenliggende mappen. */
static void maak_mappen(const char *pad) {
    char deel[MAX_PAD];
    snprintf(deel, sizeof(deel), "%s", pad);
    for (char *p = deel + 1; *p != '\0'; p++) {
        if (*p == '/') {
            *p = '\0';
            mkdir(deel, 0755);
            *p = '/';
        }
    }
    mkdir(deel, 0755);
}

/* Het gevonden pad onthouden voor een volgende start (best effort). */
static void schrijf_config(const char *waarde) {
    const char *thuis = getenv("HOME");
    char pad[MAX_PAD];
    char map[MAX_PAD];

    if (thuis == NULL || thuis[0] == '\0') {
        return;
    }
    snprintf(map, sizeof(map), "%s/Library/Application Support/Muziekspeler", thuis);
    maak_mappen(map);
    snprintf(pad, sizeof(pad), "%s/%s", thuis, CONFIG_MAP);
    FILE *f = fopen(pad, "w");
    if (f == NULL) {
        return;
    }
    fprintf(f, "%s\n", waarde);
    fclose(f);
}

/* De site-packages van de venv: .venv/lib/pythonX.Y/site-packages. */
static int vind_site_packages(const char *project, char *uit, size_t grootte) {
    char lib[MAX_PAD];
    snprintf(lib, sizeof(lib), "%s/.venv/lib", project);
    DIR *d = opendir(lib);
    if (d == NULL) {
        return 0;
    }
    int gevonden = 0;
    struct dirent *item;
    while (!gevonden && (item = readdir(d)) != NULL) {
        if (strncmp(item->d_name, "python", 6) != 0) {
            continue;
        }
        char kand[MAX_PAD];
        snprintf(kand, sizeof(kand), "%s/%s/site-packages", lib, item->d_name);
        if (is_map(kand)) {
            snprintf(uit, grootte, "%s", kand);
            gevonden = 1;
        }
    }
    closedir(d);
    return gevonden;
}

/* De projectmap bepalen volgens de volgorde in de kop van dit bestand. */
static int bepaal_project(char *uit, size_t grootte) {
    const char *env = getenv("MUZIEKSPELER_HOME");
    if (env != NULL && env[0] != '\0' && probeer(env, uit, grootte)) {
        return 1;
    }

    if (lees_config(uit, grootte)) {
        return 1;
    }

    char exe[MAX_PAD];
    eigen_map(exe, sizeof(exe));
    if (exe[0] != '\0' && zoek_omhoog(exe, uit, grootte)) {
        return 1;
    }

    const char *thuis = getenv("HOME");
    if (thuis != NULL && thuis[0] != '\0') {
        char kand[MAX_PAD];
        snprintf(kand, sizeof(kand), "%s/%s", thuis, PROJECT_NAAM);
        if (probeer(kand, uit, grootte)) {
            return 1;
        }
        snprintf(kand, sizeof(kand), "%s/Projects/%s", thuis, PROJECT_NAAM);
        if (probeer(kand, uit, grootte)) {
            return 1;
        }
        if (probeer(thuis, uit, grootte)) {
            return 1;
        }
        if (zoek_in_buren(thuis, uit, grootte)) {
            return 1;
        }
        snprintf(kand, sizeof(kand), "%s/Projects", thuis);
        if (probeer(kand, uit, grootte)) {
            return 1;
        }
        if (zoek_in_buren(kand, uit, grootte)) {
            return 1;
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    char project[MAX_PAD];
    if (!bepaal_project(project, sizeof(project))) {
        fprintf(stderr,
                "Muziekspeler: kan de projectmap niet vinden. Zet de map met\n"
                "muziekspeler.py en .venv naast de app of geef hem mee via de\n"
                "omgevingsvariabele MUZIEKSPELER_HOME.\n");
        return 1;
    }
    schrijf_config(project);

    char venv_python[MAX_PAD];
    char script[MAX_PAD];
    snprintf(venv_python, sizeof(venv_python), "%s/%s", project, VENV_PYTHON);
    snprintf(script, sizeof(script), "%s/%s", project, PROJECT_BESTAND);

    /* Laat de ingesloten Python de pakketten uit de venv vinden. */
    char site[MAX_PAD];
    if (vind_site_packages(project, site, sizeof(site))) {
        const char *vorige = getenv("PYTHONPATH");
        char nieuw_pad[MAX_PAD * 2];
        if (vorige != NULL && vorige[0] != '\0') {
            snprintf(nieuw_pad, sizeof(nieuw_pad), "%s:%s", site, vorige);
        } else {
            snprintf(nieuw_pad, sizeof(nieuw_pad), "%s", site);
        }
        setenv("PYTHONPATH", nieuw_pad, 1);
    }
    setenv("PYTHONEXECUTABLE", venv_python, 1);

    /* Nieuwe argumentenlijst: [programma, script, ...oorspronkelijke args] */
    int n = argc + 1;
    char **nieuw = (char **)malloc(sizeof(char *) * (n + 1));
    if (!nieuw) {
        return 1;
    }
    nieuw[0] = argv[0];
    nieuw[1] = script;
    for (int i = 1; i < argc; i++) {
        nieuw[i + 1] = argv[i];
    }
    nieuw[n] = NULL;

    return Py_BytesMain(n, nieuw);
}
