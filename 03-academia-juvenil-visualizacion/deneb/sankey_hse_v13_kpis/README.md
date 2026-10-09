# Sankey HSE — cambio entre cortes + banda de 3 indicadores (v13)

**Archivo:** `spec_sankey_hse_v13_kpis.json` (Vega-Lite, autosize fit).

## Qué muestra

El **flujo de estudiantes** entre las categorías oficiales del instrumento HSE, de un corte a otro
(Inicio → Proceso), y al pie una **banda de 3 indicadores** calculada dentro del propio spec:

| Indicador | Color | Regla (sobre los flujos Inicio→Proceso) |
|---|---|---|
| **Retención** | azul `#193966` | de quienes iniciaron en el bloque alto (`o_ord ≥ 5`), % que sigue ahí en el Proceso |
| **Crecimiento** | verde oscuro `#1B5E20` | de quienes iniciaron en promedio o menos (`o_ord ≤ 4`), % que subió ≥ 1 nivel |
| **Retroceso** | rojo oscuro `#8E1F1F` | de quienes iniciaron en el bloque alto (`o_ord ≥ 5`), % que bajó ≥ 2 niveles |

El umbral del retroceso es **configurable** en las señales `kpi_retro_num` (niveles de caída) y
`kpi_*_base` (bloque de partida). Con un umbral de 2 niveles el retroceso tiende a bajar y el crecimiento
a subir; ambos se ajustan sin tocar la geometría.

## Datos que espera (`dataset`)

Una fila por flujo observado:

| Campo | Tipo | Uso |
|---|---|---|
| `Habilidad` | texto | filtro: se dibuja una habilidad a la vez |
| `Categoria_Origen` / `Categoria_Destino` | texto | etiqueta del nodo |
| `Orden_Corte_Origen` / `Orden_Corte_Destino` | entero 1..N | **orden** oficial de las categorías (manda la lectura, no el color) |
| `N` | entero | tamaño de la cinta (conteo de estudiantes) |

Las 7 categorías y su orden vienen del instrumento; el spec no inventa orden, lo lee de
`Orden_Corte_*`.

## Detalles de construcción

- **Nodos** izquierda/derecha y **cintas** se generan con `transform`s encadenados (7–26 pasos por capa):
  acumulados, posiciones `y_top`/`y_bot`, alturas y ribbons con curvas.
- **Banda KPI**: tres bloques rectangulares con etiqueta, valor y base de cálculo.
- **Encabezado** sin solapamiento: `esp_topo = 118`, título en `pad_t * 0.42`, subtítulo en `pad_t * 0.64`
  y cabecera de corte en `pad_t - 8`.
- **Tipografía**: Montserrat en el gráfico; **Calibri** solo en la leyenda de notas.

## Nota metodológica

Un Sankey de flujo sin control de casos miente: el spec debe alimentarse de la tabla de flujos que ya
excluye registros incompletos y exige **ambos cortes válidos**. Los conteos por categoría son agregados;
nunca se publican identificadores individuales.
