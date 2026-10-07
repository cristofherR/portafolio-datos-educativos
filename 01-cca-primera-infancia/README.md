# 01 · Crecemos con Amor (CCA) — sistema de evaluación de primera infancia

Programa de primera infancia que acompaña a niñas y niños de 3 a 5 años, sus familias y docentes de educación
inicial en instituciones educativas públicas del territorio.

## Qué construí

Un sistema de evaluación de extremo a extremo con cuatro módulos digitales:

1. **Reporte al día** — registro diario de la actividad en aula.
2. **Asistencias** — seguimiento de participación de niñas y niños.
3. **Evaluación de docentes** — observación de la práctica pedagógica.
4. **Evaluación de familias** — percepción y prácticas de acompañamiento en el hogar.

## Arquitectura

```
Formulario / aplicativo digital  ->  Google Apps Script (validación)  ->  Azure SQL (PostgreSQL)
                                                                            |
                                                              vistas SQL -> Power BI / dashboard en servidor
                                                                            |
                                                                      capa de caché + alertas
```

- **Recojo**: formularios digitales con validación en el momento de la captura.
- **Procesamiento**: Apps Script y Python para estandarizar, validar llaves y rangos, y cargar por lotes.
- **Almacenamiento**: esquema relacional con catálogos geográficos (departamento, provincia, distrito, centro
  poblado), instituciones educativas, unidades de gestión territorial (UGT), facilitadores y asignaciones.
- **Explotación**: dashboard operativo publicado con capa de caché para no golpear la base en cada consulta.

## Archivos

- `sql/cca_schema.sql` — esquema completo de la base de datos (catálogos, IIEE, UGT, evaluaciones).
- `python/cca_etl.py` — ETL: lee la data de origen, la normaliza y genera/ejecuta la carga SQL.
- `python/generar_data_ficticia_cca.py` — genera datos sintéticos reproducibles para probar el pipeline sin
  usar información real.

## Privacidad

Este repositorio **no incluye** datos de participantes. Los ejemplos usan datos sintéticos. Las credenciales de
base de datos se leen de variables de entorno y no se versionan.
