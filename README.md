# nievasys

Portfolio personal con un home de ASCII art: el copo de nieve animado.

## Stack

- [Astro](https://astro.build) (SSG estático)
- [Tailwind CSS v4](https://tailwindcss.com)
- React (para el reproductor de frames ASCII)

## Fuentes

Self-hosted vía `@fontsource-variable/*`, sin requests externos:

- **Geist Variable** — fuente primaria del sitio (`--font-sans`)
- **JetBrains Mono Variable** — logo y animación ASCII (`--font-mono`)

## Desarrollo

Todos los comandos se corren desde la raíz del proyecto:

| Comando             | Acción                                        |
| :------------------ | :-------------------------------------------- |
| `npm install`       | Instala dependencias                          |
| `npm run dev`       | Dev server en `localhost:4321`               |
| `npm run build`     | Build de producción a `./dist/`               |
| `npm run preview`   | Previsualiza el build local                   |

## Contenido

- **Animación ASCII**: frames en `public/frames/`, reprodutor en
  `src/components/ascii-animation.tsx`. Regenerás los frames con
  `./ascii.sh <video>`.
- **Favicon y logo**: generados desde `public/favicon-copodenieve.png` con
  `python3 scripts/make-favicon.py`.

## Contribuir

Ver [`CONTRIBUTING.md`](./CONTRIBUTING.md).