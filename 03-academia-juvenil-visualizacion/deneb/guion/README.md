# Tarjeta de conclusiones dinámicas

Un bloque de **texto** que se reescribe según los filtros del tablero: por cada gráfico, un título en
negrita con su párrafo de conclusión. El texto llega como medida DAX (reacciona a los filtros) y el visual
solo lo maqueta.

## Archivos

| Archivo | Proveedor | Uso |
|---|---|---|
| `spec_tarjeta_guion_vl_resp.json` | Vega-Lite | un carril por gráfico (`orden`), texto multilínea |
| `spec_tarjeta_guion_vega.json` | Vega nativo | equivalente |
| `spec_tarjeta_texto_completo_vega.json` | Vega nativo | los párrafos como **texto corrido**; el salto de línea se calcula con el ancho real del contenedor |
| `MEDIDAS_DAX_GUION_DINAMICO.txt` | — | medidas DAX que arman `TXT_Parrafo` |

## Datos que espera

Tabla `Guion_TOV` con: `orden` (posición del bloque), `grafico` (título) y `TXT_Parrafo` (medida de texto).
El spec filtra los párrafos vacíos y, en la versión "texto completo", **envuelve** el texto calculando
cuántos caracteres entran por línea según el ancho del contenedor (`signals` W/H) y ajusta el bloque a la
altura disponible.

## Nota

`TXT_Parrafo` es una **medida**: su contenido depende de los filtros de la página, no de filas de datos.
No se publica ningún texto de resultado real.
