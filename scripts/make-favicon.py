#!/usr/bin/env python3
"""Genera el favicon y el logo a partir del arte del copo.

Fuente de producción: un PNG del copo (por defecto public/favicon-copodenieve.png).
El arte se centra en un tile #090E1F de bordes redondeados para verse bien en
temas claros y oscuros de cualquier navegador.

Salidas en public/:
  favicon.svg             envoltorio SVG con el master en base64 (nítido al escalar)
  favicon-16x16.png       favicon PNG 16px
  favicon-32x32.png       favicon PNG 32px
  favicon-192x192.png     favicon PNG 192px (Android/chromium)
  favicon.ico             16/24/32/48/64 multi-res (navegadores legacy)
  apple-touch-icon.png    180x180 (iOS)
  og-logo.png             1024x1024 branding (mismo tile)

Uso:
  python3 scripts/make-favicon.py [--source public/favicon-copodenieve.png]
                                  [--tile #090E1F] [--radius 0.22] [--content 0.82]
                                  [--frames]  # modo alternativo: proyección de frames ASCII
"""

from __future__ import annotations

import argparse
import base64
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Sequence

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
FRAME_DIR = ROOT / "public" / "frames"
PUBLIC = ROOT / "public"

DEFAULT_SOURCE = PUBLIC / "favicon-copodenieve.png"
MASTER_SIZE = 1024


# --------------------------------------------------------------------------
# Modo PNG (producción)
# --------------------------------------------------------------------------


def load_png(path: Path) -> Image.Image:
    img = Image.open(path)
    img.load()
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return img


def crop_content(img: Image.Image) -> Image.Image:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        sys.exit("El PNG no tiene contenido (alpha vacío).")
    return img.crop(bbox)


def rounded_mask(size: int, radius_ratio: float) -> Image.Image:
    ss = 4
    big = size * ss
    r = int(radius_ratio * size) * ss
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1], radius=r, fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def make_master(
    art: Image.Image,
    size: int = MASTER_SIZE,
    tile: tuple[int, int, int, int] = (9, 14, 31, 255),
    radius_ratio: float = 0.22,
    content_ratio: float = 0.82,
) -> Image.Image:
    content_side = round(size * content_ratio)
    art_scaled = art.resize(
        (content_side, content_side), Image.LANCZOS, reducing_gap=3
    )
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile_layer = Image.new("RGBA", (size, size), tile)
    canvas.paste(tile_layer, (0, 0), rounded_mask(size, radius_ratio))
    offset = (size - content_side) // 2
    canvas.alpha_composite(art_scaled, (offset, offset))
    return canvas


def write_png(img: Image.Image, path: Path, size: int) -> None:
    img.resize((size, size), Image.LANCZOS, reducing_gap=3).save(path, optimize=True)


def write_ico(img: Image.Image, path: Path) -> None:
    base = img.resize((256, 256), Image.LANCZOS, reducing_gap=3)
    base.save(
        path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)],
    )


def write_svg_wrapper(png: Image.Image, path: Path) -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "w.png"
        png.resize((192, 192), Image.LANCZOS, reducing_gap=3).save(tmp, optimize=True)
        b64 = base64.b64encode(tmp.read_bytes()).decode()
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192" '
        f'width="192" height="192"><image href="data:image/png;base64,{b64}" '
        'width="192" height="192"/></svg>\n'
    )


def ink_ratio(png: Image.Image) -> float:
    alpha = png.getchannel("A") if "A" in png.getbands() else png.convert("L")
    arr = list(alpha.get_flattened_data())
    return sum(1 for v in arr if v > 30) / len(arr)


def run_png_pipeline(source: Path, tile: str, radius: float, content: float) -> None:
    print(f"Cargando {source}...")
    art = crop_content(load_png(source))
    print(f"  arte recortado: {art.size[0]}x{art.size[1]}")

    tile_rgba = tuple(int(tile.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    master = make_master(art, MASTER_SIZE, tile_rgba, radius, content)
    band = list(master.getchannel("A").get_flattened_data())
    opaque = sum(1 for v in band if v > 30) / len(band)
    print(f"  master: {master.size[0]}x{master.size[1]}, cobertura {opaque*100:.1f}%")

    PUBLIC.mkdir(exist_ok=True)
    for s in (16, 32, 192):
        write_png(master, PUBLIC / f"favicon-{s}x{s}.png", s)
    write_png(master, PUBLIC / "apple-touch-icon.png", 180)
    write_png(master, PUBLIC / "og-logo.png", 1024)
    write_ico(master, PUBLIC / "favicon.ico")
    write_svg_wrapper(master, PUBLIC / "favicon.svg")
    print("  favicon.svg, favicon-{16,32,192}xN.png, .ico, apple-touch-icon, og-logo OK")


# --------------------------------------------------------------------------
# Modo frames ASCII (alternativo: --frames)
# --------------------------------------------------------------------------


def load_frames() -> List[List[str]]:
    paths = sorted(FRAME_DIR.glob("frame_*.txt"))
    if not paths:
        sys.exit(f"No hay frames en {FRAME_DIR}")
    frames: List[List[str]] = []
    for p in paths:
        lines = p.read_text().split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        frames.append(lines)
    return frames


def grid_dimensions(frames: Sequence[List[str]]) -> tuple[int, int]:
    return max(len(f) for f in frames), max(len(l) for f in frames for l in f)


def composite_grid(frames: Sequence[List[str]]) -> List[str]:
    height, width = grid_dimensions(frames)
    ink = [[False] * width for _ in range(height)]
    for f in frames:
        for r, line in enumerate(f):
            for c, ch in enumerate(line):
                if not ch.isspace():
                    ink[r][c] = True
    return [
        "".join("#" if ink[r][c] else " " for c in range(width))
        for r in range(height)
    ]


def ink_grid_binary(frames: Sequence[List[str]]) -> Image.Image:
    height, width = grid_dimensions(frames)
    grid = composite_grid(frames)
    img = Image.new("L", (width, height), 0)
    px = img.load()
    for r in range(height):
        for c in range(width):
            if grid[r][c] == "#":
                px[c, r] = 255
    return img


def fit_square_binary(mask: Image.Image, margin: float = 0.0) -> Image.Image:
    bbox = mask.getbbox()
    if not bbox:
        sys.exit("Imagen vacía.")
    left, top, right, bottom = bbox
    body = mask.crop((left, top, right, bottom))
    side = round(max(body.size) * (1 + 2 * margin))
    canvas = Image.new("L", (side, side), 0)
    canvas.paste(body, ((side - body.width) // 2, (side - body.height) // 2))
    return canvas


def save_pbm(mask: Image.Image, path: Path) -> None:
    data = mask.tobytes()
    w, h = mask.size
    row_bytes = (w + 7) // 8
    out = bytearray((f"P4\n{w} {h}\n").encode())
    for row in range(h):
        buf = bytearray(row_bytes)
        byte = 0
        bits = 0
        start = row * w
        for x in range(w):
            byte = (byte << 1) | (1 if data[start + x] > 128 else 0)
            bits += 1
            if bits == 8:
                buf[(x + 1) // 8 - 1] = byte
                byte = 0
                bits = 0
        if bits:
            buf[row_bytes - 1] = byte << (8 - bits)
        out += buf
    path.write_bytes(out)


def trace_svg(mask: Image.Image, turdsize: int, potrace: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pbm = td / "shape.pbm"
        out = td / "shape.svg"
        save_pbm(mask, pbm)
        res = subprocess.run(
            [potrace, "--svg", "--turdsize", str(turdsize), "-o", str(out), str(pbm)],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            sys.exit(f"potrace falló: {res.stderr}")
        return out.read_text()


def make_favicon_svg(traced: str) -> str:
    root = re.search(r"<svg[^>]*>", traced)
    body = re.search(r"<svg[^>]*>(.*)</svg>", traced, re.S)
    if not root or not body:
        sys.exit("SVG de potrace inesperado.")
    viewbox = re.search(r'viewBox="[^"]*"', root.group(0))
    viewbox_attr = viewbox.group(0) if viewbox else ""
    paths = re.sub(r'\s*(fill|stroke)="[^"]*"', "", body.group(1))
    paths = re.sub(r"\s*<metadata>.*?</metadata>\s*", "", paths, flags=re.S)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" {viewbox_attr}>\n'
        "  <style>\n"
        "    path { fill: #000; }\n"
        "    @media (prefers-color-scheme: dark) {\n"
        "      path { fill: #FFF; }\n"
        "    }\n"
        "  </style>\n"
        f"{paths}\n"
        "</svg>\n"
    )


def svg_to_png(rsvg: str, svg_path: Path, size: int, out: Path) -> None:
    res = subprocess.run(
        [rsvg, "-w", str(size), "-h", str(size), "-o", str(out), str(svg_path)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        sys.exit(f"rsvg-convert falló: {res.stderr}")


def run_frames_pipeline(turdsize: int, margin: float) -> None:
    potrace = shutil.which("potrace")
    rsvg = shutil.which("rsvg-convert")
    if not potrace or not rsvg:
        sys.exit("Modo --frames requiere potrace y rsvg-convert.")
    print("Modo frames: proyección de celdas + traza...")
    frames = load_frames()
    base = fit_square_binary(ink_grid_binary(frames), margin)
    sil = base.resize((640, 640), Image.LANCZOS).point(lambda p: 255 if p > 128 else 0, mode="L")
    traced = trace_svg(sil, turdsize, potrace)
    favicon_svg = PUBLIC / "favicon.svg"
    favicon_svg.write_text(make_favicon_svg(traced))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pngs = {}
        for s in (16, 32, 48, 64, 180):
            out = td / f"favicon_{s}.png"
            svg_to_png(rsvg, favicon_svg, s, out)
            img = Image.open(out)
            img.load()
            pngs[s] = img
        pngs[64].save(
            PUBLIC / "favicon.ico",
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)],
        )
        pngs[180].save(PUBLIC / "apple-touch-icon.png")
    print("Modo frames OK.")


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--tile", default="#090E1F")
    parser.add_argument("--radius", type=float, default=0.22)
    parser.add_argument("--content", type=float, default=0.82)
    parser.add_argument("--frames", action="store_true")
    parser.add_argument("--turdsize", type=int, default=30)
    parser.add_argument("--margin", type=float, default=0.15)
    args = parser.parse_args()

    if args.frames:
        run_frames_pipeline(args.turdsize, args.margin)
        return

    source = Path(args.source)
    if not source.is_file():
        sys.exit(f"No se encontró el PNG de origen: {source}")
    run_png_pipeline(source, args.tile, args.radius, args.content)


if __name__ == "__main__":
    main()