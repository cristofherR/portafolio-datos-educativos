# 03 · Academia Juvenil — visualización avanzada en Power BI (DAX + Deneb)

Programa de formación para estudiantes de secundaria. El reto analítico: mostrar **cómo cambian** las
habilidades socioemocionales (HSE) de cada estudiante entre dos cortes (Inicio → Proceso), sin exponer datos
individuales en el tablero.

## Dos visuales construidos a medida

### 1. Diagrama Sankey de cambio entre cortes
- **Qué muestra**: el flujo de estudiantes entre las 7 categorías oficiales del instrumento, de un corte a otro.
- **Cómo**: tabla de flujos (origen → destino → conteo) calculada en DAX y renderizada con un visual
  personalizado **Deneb / Vega-Lite**.
- **Detalle técnico**: solo se incluyen estudiantes que tienen **ambos cortes** válidos (mínimo de respuestas
  por corte), y las categorías se ordenan según las bandas oficiales del instrumento para que la lectura no
  dependa del color.

Archivos: `sankey/dax_sankey_hse_SOLO_PEGAR.txt` (medidas DAX) y
`sankey/deneb_sankey_hse_SOLO_PEGAR.json` (especificación Vega-Lite para Deneb).

### 2. Radar de habilidades
- **Qué muestra**: perfil de habilidades por estudiante y perfil grupal (aula / academia), comparando cortes.
- **Cómo**: especificación Deneb con ejes por habilidad y capas superpuestas por corte.

Archivos: `radar/spec_radar_deneb.json`.

## Generación de las figuras para informes
`python/hse_aj_sankey.py` genera los diagramas en PNG (uno por habilidad y academia) y un PDF consolidado,
a partir de agregados. **Nunca parte de datos identificables**: trabaja sobre conteos por categoría.

## Nota metodológica
Antes de cualquier gráfico se depura la base: se exige un mínimo de respuestas por corte, se excluyen registros
incompletos y se documenta cuántos casos quedan fuera y por qué. Un gráfico de flujo sin ese control miente.
