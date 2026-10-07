# Cómo reproducir este portafolio

Todo lo que hay aquí se puede ejecutar **sin acceso a ninguna base de datos institucional
y sin datos reales**: los ejemplos incluidos son **sintéticos** y se regeneran con un
script. El objetivo es que cualquiera pueda clonar el repo, correr los comandos y ver
los mismos resultados.

## Requisitos

- Python 3.10+
- `pip install -r requirements.txt` (pandas, openpyxl, matplotlib, requests)

## 0. Regenerar los datos sintéticos (opcional)

```bash
python3 tools/make_synthetic_examples.py
```

Crea:

- `01-cca-primera-infancia/python/cca_sheet_data.csv` — 14 IIEE de ejemplo.
- `03-academia-juvenil-visualizacion/data/synthetic/agregados_hse_crecimiento.json` — 4 diagramas de flujo (2 academias × 2 habilidades).

## 1. CCA · esquema + ETL

```bash
# 1a) Resumen del ETL sobre el CSV sintético (no escribe nada)
python3 01-cca-primera-infancia/python/cca_etl.py --dry-run

# 1b) Generar el SQL de carga (INSERTs normalizados)
python3 01-cca-primera-infancia/python/cca_etl.py --sql-output /tmp/carga.sql

# 1c) Crear el esquema (PostgreSQL 14+). En SQLite funciona igual salvo SERIAL.
psql "$DATABASE_URL" -f 01-cca-primera-infancia/sql/cca_schema.sql
```

**Qué demuestra:** normalización de entidades (provincia → distrito → centro poblado →
UGT → IIEE), detección de duplicados por código modular y separación entre IIEE
escolarizadas y no escolarizadas.

> El generador de Excel (`generar_data_ficticia_cca.py`) necesita una **plantilla propia**
> con las hojas `BD`, `Familias`, `Docentes`, `Reportes_Rapidos`, `Asistencia` e
> `Historial`, porque el script solo rellena filas y conserva formatos:
>
> ```bash
> CCA_TEMPLATE_XLSX=/ruta/a/tu_plantilla.xlsx python3 01-cca-primera-infancia/python/generar_data_ficticia_cca.py
> ```

## 2. Mente Sana · esquema

```bash
psql "$DATABASE_URL" -f 02-mente-sana/sql/mente_sana_esquema.sql
```

**Qué demuestra:** modelo relacional con roster (persona × IE × grado), sesiones,
asistencia y un módulo de observación de habilidades por corte, con índices y comentarios
de columna.

## 3. Academia Juvenil · diagrama Sankey (DAX + Deneb)

```bash
python3 03-academia-juvenil-visualizacion/python/hse_aj_sankey.py
# → salidas/graficos_sankey/*.png  y  salidas/Sankey_HSE_AJ.pdf
```

Variables de entorno opcionales:

| Variable | Para qué |
|---|---|
| `AJ_ENTRADA` | carpeta con `agregados_hse_crecimiento.json` (por defecto, el ejemplo sintético) |
| `AJ_SALIDA` | carpeta de salida (por defecto `./salidas`) |

**Qué demuestra:** lectura de agregados por habilidad y academia, cálculo de flujos
entre cortes (subió / se mantuvo / bajó) y render de un diagrama Sankey completo
(posiciones proporcionales, cintas por flujo, leyenda y controles de conteo).

Los archivos para Power BI/Deneb se pegan tal cual:

- `sankey/dax_sankey_hse_SOLO_PEGAR.txt` — medida DAX que arma la tabla de flujos.
  **Trae placeholders `<UUID_EVALUACION_INICIO>` / `<UUID_EVALUACION_PROCESO>`**: pon los IDs
  de tu propio modelo.
- `sankey/deneb_sankey_hse_SOLO_PEGAR.json` — spec Vega del visual.
- `radar/spec_radar_deneb.json` — spec del radar de habilidades (con los datos de ejemplo
  incluidos en el propio archivo).

## 4. Verificación antes de publicar

```bash
python3 tools/sanitize_repo.py
```

Recorre el repo y avisa si aparece una credencial, un host interno, un ID de hoja de
cálculo o un identificador personal. Si dice **Limpio**, se puede publicar.

## Estructura

```
01-cca-primera-infancia/     programa de primera infancia (evaluación)
  python/cca_etl.py            ETL: CSV → entidades normalizadas → SQL
  python/generar_data_ficticia_cca.py
  sql/cca_schema.sql           esquema relacional
02-mente-sana/               transición primaria–secundaria
  sql/mente_sana_esquema.sql
03-academia-juvenil-visualizacion/
  python/hse_aj_sankey.py      Sankey de cambio entre cortes
  python/aj_radar_habilidades.py
  sankey/ | radar/             specs para Power BI + Deneb
  data/synthetic/              agregados de ejemplo
04-stakeholders/             mapa de actores (en preparación)
tools/                       utilidades (datos sintéticos, verificación)
```

## Privacidad

- Los ejemplos son **sintéticos** y se generan con `tools/make_synthetic_examples.py`.
- Ninguna credencial se versiona: todo se lee de variables de entorno (ver `.env.example`).
- Los datos de niñas, niños y familias nunca salen del entorno institucional.
