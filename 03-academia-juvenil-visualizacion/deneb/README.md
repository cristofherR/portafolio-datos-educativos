# Deneb · visuales construidos a medida (Vega / Vega-Lite) para Power BI

Especificaciones **Deneb** del tablero de Academia Juvenil. Este directorio contiene **solo la parte
estructural**: geometría, escalas, ejes, paleta de colores, umbrales y las fórmulas/señales que hacen
funcionar cada gráfico. **No hay datos de estudiantes, ni credenciales, ni cadenas de conexión, ni
nombres de servidores.** Los ejemplos de `data/synthetic/` son sintéticos y se regeneran con un script.

Cada spec **no trae datos**: declara `"data": {"name": "dataset"}` para que Deneb inyecte ahí la tabla
que arrastres al visual. Por eso son reutilizables con cualquier origen.

## Contenido

| Carpeta | Gráfico | Qué demuestra |
|---|---|---|
| `sankey_hse_v13_kpis/` | Diagrama **Sankey** de cambio entre cortes + banda de 3 indicadores (retención / crecimiento / retroceso) | Flujo categoría→categoría con geometría manual de nodos y cintas, y KPIs calculados dentro del spec |
| `tov/` | 5 gráficos del **TOV**: radar grupal, radar individual, barras ordenadas, apilado 100 %, termómetro de bloques | Radar polar construido a mano, escalas de tramo y umbral, etiquetas dentro de las marcas |
| `guion/` | **Tarjeta de conclusiones dinámicas** | Bloque de texto que se reescribe según los filtros y ajusta su salto de línea al ancho del contenedor |
| `python/` | Generadores | Scripts autocontenidos que producen las specs (colores y geometría en constantes, sin datos) |

## Dos proveedores: elige el archivo correcto

Deneb puede ejecutar un spec como **Vega-Lite** o como **Vega**. Si pegas un spec Vega-Lite en un visual
configurado como *Vega*, falla con `/data must be array of #/properties/data/type` (el esquema de Vega no
acepta `data` como objeto único). Para evitarlo cada gráfico trae ambos:

- `*_vl_resp.json` → **Vega-Lite**, tamaño atado al contenedor (recomendado).
- `*_vl_fijo.json` → **Vega-Lite**, tamaño numérico (plan B si el contenedor da problemas).
- `*_vega.json` → **Vega nativo** (sin `width`/`height`, para que herede el tamaño del visual).

En Deneb: **Settings (⚙) → General → Provider**. No toques *"Compiled Vega / Switch to Vega"* salvo que
sepas lo que hace: cambia el proveedor y reemplaza el spec.

## Campos que se arrastran al visual (todos "No resumir" los numéricos)

| Gráfico | Tabla del modelo | Campos |
|---|---|---|
| Sankey HSE | *(tabla de flujos)* | `Habilidad`, `Categoria_Origen`, `Orden_Corte_Origen`, `Categoria_Destino`, `Orden_Corte_Destino`, `N` |
| Radar grupal / individual | `TOV_Areas` | `area`, `orden`, `valor` (+ slicer de estudiante en el individual) |
| Barras ordenadas | `TOV_Areas` | `area`, `valor` |
| Apilado 100 % | `TOV_Areas` | `area`, `tramo`, `valor` |
| Termómetro de bloques | `TOV_Bloques` | `bloque`, `orden`, `valor` |
| Tarjeta de guion | `Guion_TOV` | `orden`, `grafico`, `TXT_Parrafo` |

> Los nombres de tabla/campo corresponden a un modelo de ejemplo: **ajústalos a los de tu modelo**. Lo
> que importa es el tipo y, en los numéricos, que Power BI **no** los agregue (si `valor` se suma, el
> gráfico miente).

## Probar sin Power BI

En el editor de Vega (`https://vega.github.io/editor/`) el spec no encuentra `dataset`. Para previsualizar,
sustituye la primera línea de datos por un arreglo embebido:

```json
"data": {"values": [ /* copia aquí data/synthetic/tov_areas_demo.json */ ]}
```

`data/synthetic/` trae filas de ejemplo para las tablas `TOV_Areas` y del Sankey. Son sintéticas.

## Lecciones de Deneb 2.0 (evitan errores que costaron horas)

1. **Tamaño responsivo en Vega-Lite**: `"width": "container"`. **No** `{"expr": …}` ni `{"signal": …}`
   (eso produce `VegaEmbed error: Cannot read properties of undefined (reading 'format')`).
   En **Vega nativo** sí vale el signal `denebContainer.width` / `.height`.
2. **Binding de datos**: el spec debe declarar `"data": {"name": "dataset"}`. Sin eso, nunca lee el
   visual. Modo seguro: sin `$schema`, sin `params`, sin `autosize`, solo literales.
3. **Cada ítem de `transform` es una sola operación**: `filter` no puede ir junto con `window`/`sort` en el
   mismo objeto.
4. **Vega nativo responsivo**: si declaras `width`/`height`, Deneb respeta el número y el gráfico no
   crece; omítelos para que herede el contenedor.
5. **Barras de "un solo color"** casi siempre es un problema de **dato** (casi todos los grupos caen en un
   mismo tramo), no de código; la leyenda muestra el rango completo de tramos.
6. **Radar**: no cambies el campo de color de la capa de puntos; ajusta **propiedades de leyenda**.
   Verifica con `toSVG()` contando trazos, no solo con "compila".
7. **Deneb 2.x** compila con vega-lite v6 y ya aplica el tamaño responsivo por su cuenta si el spec no
   declara `width`/`height`.
