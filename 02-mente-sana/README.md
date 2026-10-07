# 02 · Mente Sana — transición primaria–secundaria

Programa de acompañamiento socioemocional en la transición de primaria a secundaria, con cobertura de
22 instituciones educativas y 4 unidades de gestión territorial (UGT).

## Qué construí

- **Instrumentos digitales** para estudiantes, familias y docentes (encuestas de bienestar y transición).
- **Procesamiento y análisis** de las respuestas: limpieza, control de faltantes y construcción de indicadores.
- **Tablero de resultados** por UGT, institución educativa y grado, para la lectura territorial del proceso.

## Estructura de datos

Esquema relacional en PostgreSQL / Azure SQL con cuatro entidades principales:

| Tabla | Rol |
|---|---|
| `ms_roster` | Padrón de participantes por institución, grado y UGT. |
| `ms_sesion` | Sesiones de acompañamiento realizadas (fecha, tipo, responsables). |
| `ms_asistencia` | Asistencia de participantes a cada sesión. |
| `ms_evaluacion_estudiante` | Respuestas del instrumento de evaluación socioemocional por corte. |

- `sql/mente_sana_esquema.sql` — definición de las tablas e índices.

## Nota sobre los datos

El análisis se hace sobre datos institucionales y **solo a nivel agregado**. Este repositorio no publica
registros individuales ni identificadores de estudiantes, familias o docentes.
