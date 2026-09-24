# Contributing

## Setup

Requisito: Node >= 22 (ver `engines` en `package.json`).

```sh
npm install
npm run dev     # servidor local en http://localhost:4321
```

## Verificación antes de commitear

- `npm run build` debe pasar sin errores.
- No se commitea `dist/`, `.astro/` ni `node_modules/` (ignorados).
- Los artefactos de Python (`scripts/__pycache__/`, `*.pyc`) están ignorados.

## Estructura

```
src/
  pages/index.astro            Home (usa About)
  components/About.astro       Logo ASCII + animación del copo
  components/ascii-animation.tsx  Reproductor de frames ASCII (React)
  layouts/Layout.astro         Head, iconos, imports de fuentes
  styles/global.css            Tokens de tema y @theme de fuentes
public/
  frames/                      Frames ASCII (frame_%04d.txt + frames.json)
  favicon-* , apple-touch-icon, og-logo   Assets generados del copo
scripts/
  make-favicon.py              Pipeline de favicon/logo
ascii.sh                       Video -> frames ASCII
```

## Fuentes

- `--font-sans` → **Geist Variable** (primaria del sitio).
- `--font-mono` → **JetBrains Mono Variable** (logo + animación ASCII).

Ambas son self-hosted vía `@fontsource-variable/*`; se importan en
`src/layouts/Layout.astro` y se declaran en `@theme` en
`src/styles/global.css`. No hace falta configurar nada para usarlas:
`font-sans` / `font-mono`.

## Animación ASCII

- El reproductor `ascii-animation.tsx` consume `public/frames/frames.json`
  (manifiesto con `count`) y los `frame_%04d.txt`.
- Para regenerar los frames desde un video:

  ```sh
  ./ascii.sh public/snowflake.mp4
  ```

  Requiere `ffmpeg` e ImageMagick (`magick`). El script publica en
  `public/frames/` y actualiza `frames.json`.
- La animación pausa con `visibilitychange` (pestaña oculta) y respeta
  `prefers-reduced-motion`.

## Favicon y logo

La fuente del arte es `public/favicon-copodenieve.png`; los assets se
derivan de ahí (tile `#090E1F` redondeado, visible en claro y oscuro):

```sh
python3 scripts/make-favicon.py [--radius 0.22] [--content 0.82] [--tile #090E1F]
```

Salidas que genera:

- `public/favicon.svg` (envoltorio SVG con el PNG en base64)
- `public/favicon-{16,32,192}xN.png`
- `public/favicon.ico` (16/24/32/48/64)
- `public/apple-touch-icon.png` (180)
- `public/og-logo.png` (1024)

Requisitos: `python3` + Pillow, `potrace` y `rsvg-convert`.

Modo alternativo `--frames`: genera la silueta desde la proyección de celdas
de los frames ASCII (no es la ruta de producción).

## Convención de commits

Mensajes cortos en minúscula con prefijo de tipo convencional:

- `feat: ...` una feature nueva
- `fix: ...` una corrección
- `chore: ...` tareas de mantenimiento
- `docs: ...` documentación

Ejemplos: `feat: animación ascii del copo en el home`, `docs: agregar CONTRIBUTING`.