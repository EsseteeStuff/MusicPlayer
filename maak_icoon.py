#!/usr/bin/env python3
"""Maak icon.png en icon.ico voor de muziekspeler.

Het icoon is een afgeronde donkerblauwe tegel met twee losse muzieknoten,
drie equalizerbalken en een zachte gloed. Kleuren komen overeen met het
standaardthema van de app (#5b8cff en #37c8ff).

Gebruik: python3 maak_icoon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4                      # eerst tekenen op 4x, dan verkleinen voor scherpe randen
N = 512 * S
UITVOER = Path(__file__).resolve().parent

BLAAUW = (91, 140, 255, 255)     # #5b8cff
CYAAN = (55, 200, 255, 255)      # #37c8ff
TOP = (29, 42, 68)
ONDER = (14, 19, 32)
LETTER = "♪"                     # één achtste noot; we plaatsen er twee
FONTPAD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def maak_tegel() -> Image.Image:
    """Afgeronde tegel met een zachte verticale gradient."""
    tegel = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    gradient = Image.new("RGBA", (N, N))
    teken = ImageDraw.Draw(gradient)
    for y in range(N):
        t = y / (N - 1)
        kleur = tuple(int(TOP[i] + (ONDER[i] - TOP[i]) * t) for i in range(3)) + (255,)
        teken.line((0, y, N, y), fill=kleur)
    masker = Image.new("L", (N, N), 0)
    ImageDraw.Draw(masker).rounded_rectangle(
        (0, 0, N - 1, N - 1), radius=int(N * 0.22), fill=255
    )
    tegel.paste(gradient, (0, 0), masker)
    ImageDraw.Draw(tegel).rounded_rectangle(
        (int(N * 0.018),) * 2 + (N - int(N * 0.018), N - int(N * 0.018)),
        radius=int(N * 0.205),
        outline=(120, 165, 255, 80),
        width=int(N * 0.005),
    )
    return tegel


def teken_balken(tegel: Image.Image) -> None:
    """Drie equalizerbalken achter de noten, met een zachte gloed."""
    balken = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    teken = ImageDraw.Draw(balken)
    for cx, fractie in [(0.24, 0.18), (0.50, 0.28), (0.76, 0.21)]:
        breedte = N * 0.055
        hoogte = N * fractie
        x = cx * N - breedte / 2
        y = N * 0.82 - hoogte
        teken.rounded_rectangle(
            (x, y, x + breedte, N * 0.82),
            radius=breedte / 2,
            fill=(55, 200, 255, 145),
        )
    tegel.alpha_composite(balken.filter(ImageFilter.GaussianBlur(N * 0.012)))
    tegel.alpha_composite(balken)


def plak_noot(tegel: Image.Image, cx: float, cy: float, grootte: float, kleur) -> None:
    """Teken één noot, gecentreerd op (cx, cy) in verhoudingen van het formaat."""
    font = ImageFont.truetype(FONTPAD, int(N * grootte))
    bb = font.getbbox(LETTER)
    breedte, hoogte = bb[2] - bb[0], bb[3] - bb[1]
    x = cx * N - breedte / 2 - bb[0]
    y = cy * N - hoogte / 2 - bb[1]

    gloed = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(gloed).text((x, y), LETTER, font=font, fill=(*kleur[:3], 210))
    tegel.alpha_composite(gloed.filter(ImageFilter.GaussianBlur(N * 0.016)))

    noot = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(noot).text((x, y), LETTER, font=font, fill=kleur)
    tegel.alpha_composite(noot)


def main() -> None:
    tegel = maak_tegel()
    teken_balken(tegel)
    # Twee losse noten: links lager en kleiner, rechts hoger en groter.
    plak_noot(tegel, 0.34, 0.53, 0.40, BLAAUW)
    plak_noot(tegel, 0.66, 0.43, 0.46, CYAAN)

    icoon = tegel.resize((512, 512), Image.Resampling.LANCZOS)
    icoon.save(UITVOER / "icon.png")
    icoon.save(
        UITVOER / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("icon.png en icon.ico gemaakt met twee noten")


if __name__ == "__main__":
    main()
