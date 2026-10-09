# TOV — 5 gráficos de barrera de habilidades (Deneb)

Especificaciones Deneb del instrumento **TOV**: un radar polar construido a mano, un ranking de barras y
una composición apilada. Todos leen la tabla del modelo por `"data": {"name": "dataset"}`.
Los numéricos (`orden`, `valor`) van en Power BI **"No resumir"**.

## Archivos

| Gráfico | Vega-Lite | Vega nativo | Campos |
|---|---|---|---|
| **Radar grupal** (12 áreas) | `spec_tov_radar_grupal_vl_resp.json` · `_vl_fijo.json` | `spec_tov_radar_grupal_vega_*.json` | `area`, `orden`, `valor` |
| **Radar individual** (12 áreas) | `spec_tov_radar_individual_vl_resp.json` · `_vl_fijo.json` | `spec_tov_radar_individual_vega.json` | `area`, `orden`, `valor` (+ filtro de estudiante) |
| **Barras ordenadas** (12 áreas) | `spec_tov_barras_vl_resp.json` · `_vl_fijo.json` | `spec_tov_barras_vega.json` | `area`, `valor` |
| **Apilado 100 %** (por descriptor) | `spec_tov_apilado_vl_resp.json` · `_vl_fijo.json` | `spec_tov_apilado_vega.json` | `area`, `tramo`, `valor` |
| **Termómetro** (6 bloques) | `spec_tov_termometro_vl_resp.json` | `spec_tov_termometro_vega.json` | `bloque`, `orden`, `valor` |

**Radar grupal** tiene dos variantes de leyenda (mismo gráfico, distinta lectura):

- `*_leyenda_corte*` → **una sola leyenda "Corte: Inicio / Proceso"** (la más clara, recomendada).
- `*_dos_leyendas*` → mantiene el color del punto por nivel del área, con leyenda titulada y separada.

## Escala y tramos

Los 5 tramos del descriptor (de menor a mayor) y su color:

| Tramo | Rango (escala 1–5) | Color |
|---|---|---|
| Desacuerdo marcado | ≤ 1.80 | `#C00000` |
| Desacuerdo | 1.81 – 2.60 | `#ED7D31` |
| Posición intermedia | 2.61 – 3.40 | `#BFA26B` |
| Acuerdo | 3.41 – 4.20 | `#9CC069` |
| Acuerdo marcado | > 4.20 | `#2E7D32` |

El **umbral de "Acuerdo" = 3.41** se dibuja como línea/anillo de referencia en barras y radar.

## Cómo está construido el radar

No usa un tipo "radar" nativo: se calculan las coordenadas polares con `transform` (seno/coseno por eje),
se dibujan **anillos de referencia** (`r1…r5`), un **anillo de umbral** y una **capa de polígono/puntos**
por corte. El cierre del polígono va por `detail` (una línea por corte), no por el orden de las filas.
Si un área no llega al mínimo de ítems, el polígono cae a 0 en ese eje (`impute`).

## Apilado 100 %

Cada barra es una **composición porcentual** de estudiantes según el tramo del descriptor del área. Las
etiquetas de % van **dentro** de los tramos; los tramos con menos del 6 % no la muestran para no encimarse
(quedan visibles en el tooltip).

## Datos de ejemplo

`../data/synthetic/` (carpeta del proyecto) trae filas sintéticas con los campos de `TOV_Areas`. Son de
ejemplo; no provienen de estudiantes reales.
