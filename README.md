# Portafolio de datos educativos — Cristofher Rodríguez Atilano

Analista de datos · Monitoreo, Evaluación y Aprendizaje (MEL) · Educación e impacto social · Perú

Este repositorio reúne **procesos, código y estructuras** de los sistemas de información que diseño y mantengo
para programas educativos en Áncash (Perú). No contiene datos personales de estudiantes, familias ni docentes:
solo código, esquemas, especificaciones y resultados agregados.

## Qué encontrarás aquí

| Carpeta | Contenido |
|---|---|
| `01-cca-primera-infancia/` | Sistema de evaluación del programa Crecemos con Amor (CCA): esquema de base de datos, ETL y generador de datos sintéticos para pruebas. |
| `02-mente-sana/` | Estructura de datos del programa Mente Sana (transición primaria–secundaria): esquema relacional de roster, sesiones, asistencia y evaluación. |
| `03-academia-juvenil-visualizacion/` | Visualización avanzada en Power BI: diagrama Sankey de cambio entre cortes (DAX + Deneb/Vega-Lite) y radar de habilidades. |
| `04-stakeholders/` | Mapa de actores del ecosistema territorial (en preparación). |
| `05-plataforma-informes/` | Plataforma web de descarga de informes (FastAPI) + filtros cruzados, acceso por credencial y pipeline que la mantiene al día con un solo comando. |

## Stack

- **SQL**: Azure SQL / PostgreSQL — consultas, CTE, funciones de ventana, vistas, esquema estrella, calidad de datos.
- **Python**: pandas, openpyxl, matplotlib — ETL, validación, automatización de reportes.
- **BI**: Power BI (DAX, visuales personalizados con Deneb/Vega-Lite), Looker Studio.
- **Automatización**: Google Apps Script, jobs programados, validación front/back-end.
- **Nube**: Azure SQL, SharePoint, Power Apps.

## Principios de trabajo

1. **Calidad del dato primero**: validación en el recojo y en la carga, control de duplicados, huérfanos y rangos.
2. **Trazabilidad**: cada indicador tiene una definición documentada y una única fuente de verdad.
3. **Datos imperfectos**: se miden, se documentan los supuestos y se reportan con su incertidumbre visible.
4. **Privacidad**: los datos de niñas, niños y familias nunca salen del entorno institucional; aquí solo hay procesos.

## Cómo reproducirlo

Todo es ejecutable sin acceso a bases de datos institucionales y sin datos reales:
los ejemplos son **sintéticos** y se regeneran con un script.

```bash
pip install -r requirements.txt
python3 tools/make_synthetic_examples.py          # regenera los datos de ejemplo
python3 01-cca-primera-infancia/python/cca_etl.py --dry-run
python3 03-academia-juvenil-visualizacion/python/hse_aj_sankey.py   # → salidas/
```

Paso a paso detallado, variables de entorno y resultados esperados: **[REPRODUCIR.md](REPRODUCIR.md)**.

```
01-cca-primera-infancia/            02-mente-sana/
  python/cca_etl.py                   sql/mente_sana_esquema.sql
  python/generar_data_ficticia_cca.py 03-academia-juvenil-visualizacion/
  sql/cca_schema.sql                   python/ · sankey/ · radar/ · data/synthetic/
04-stakeholders/                    tools/
  README.md (en preparación)          make_synthetic_examples.py · sanitize_repo.py
```

Antes de publicar cualquier cambio: `python3 tools/sanitize_repo.py` → debe decir **Limpio**.

> Autor: Cristofher Alejandro Rodríguez Atilano · c.rodriguezatilano@gmail.com
