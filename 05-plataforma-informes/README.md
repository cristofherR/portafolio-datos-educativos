# 05 · Plataforma de descarga de informes + pipeline automatizado

Plataforma web que entrega el **informe personal** de cada estudiante de Academia Juvenil (Áncash)
y el **pipeline** que la mantiene al día desde la base de datos institucional, sin intervención manual.

El foco de este módulo es la **construcción de la plataforma**, sus **filtros**, el **modo de acceso
por credencial** y la **automatización de reportes**. No contiene credenciales ni datos de estudiantes.

## Qué resuelve

Cada estudiante recibe un PDF de 3 páginas que integra cuatro fuentes:
evaluación vocacional (TOV), socioemocional (HSE Inicio → Proceso), académica (PRONABEC) y COAR.
Cuando llega nueva información, todo se regenera con **un solo comando** y la web se actualiza sola.

```bash
python3 pipeline/actualizar.py             # BD -> datos -> informes -> web + auditoría
python3 pipeline/actualizar.py --sin-bd    # no consulta la base: usa el JSON local
python3 pipeline/actualizar.py --solo-web  # solo lista de la web + credenciales
python3 pipeline/actualizar.py --todo      # rehace todos los PDF aunque no cambien
```

## Estructura

```
web/app.py                  Plataforma (FastAPI): login, filtros cruzados, ZIP, logout
pipeline/actualizar.py      Orquestador de punta a punta (1 comando)
pipeline/generar.py         Genera/actualiza PDFs de forma incremental (huella por estudiante)
pipeline/gen.py             Motor del informe sobre la plantilla (sin emojis)
pipeline/prep_web.py        Construye estudiantes.json + copia local de credenciales
pipeline/auditoria.py       Auditoría geométrica: texto que cruza el borde de una tarjeta
pipeline/db.py              Conexión a la base por variables de entorno
pipeline/sync_programado.sh Ejecución desatendida; imprime NO_REPLY si no hay cambios
informe_personal_tov/       Capa de dominio: consolidación y contenido del informe
config/                     Identificadores de evaluaciones (ejemplo; el real no se versiona)
data/ejemplo_estudiantes.json  Datos SINTÉTICOS para probar la plataforma
```

## La plataforma (`web/app.py`)

- **Login** con las mismas credenciales de la intranet (copia local en SQLite, `bcrypt`).
- **Alcance por credencial**: cada cuenta `AJ<NOMBRE>` ve **solo su academia**. Las cuentas de
  coordinación con DNI son rechazadas con un mensaje claro.
- **Filtros cruzados** tipo Power BI (academia → centro poblado → IE → aula) y búsqueda por nombre:
  cada filtro se recalcula según los demás.
- **Selección con checkboxes** y descarga de un **ZIP** con los informes marcados.
- **Cierre de sesión** que borra la cookie y evita que el botón "atrás" muestre el panel.
- **Recarga en caliente**: lee `estudiantes.json` cuando cambia en disco → no hay que reiniciar el
  servicio tras actualizar los informes.

## Cómo se mantiene al día

| Paso | Script | Qué produce |
|---|---|---|
| 1 | `informe_personal_tov/consolidar_datos.py` | Un JSON por estudiante (TOV + HSE + PRONABEC + COAR) |
| 2 | `pipeline/generar.py` | PDFs + `manifest.json` (solo rehace lo que cambió) |
| 3 | `pipeline/prep_web.py` | Lista de la web + credenciales |
| 4 | `pipeline/auditoria.py` | Control de calidad geométrico de los informes regenerados |

- **Incremental por huella** (contenido + motor + plantilla): sin cambios = segundos; cambiar un dato
  regenera solo ese informe; quitar un estudiante lo mueve a `_obsoletos/`; cambiar la plantilla rehace
  todos. Un error en un estudiante no detiene el resto.
- **Escritura atómica** de la lista: la web nunca ve un archivo a medias.
- **Programado** dos veces al día: solo avisa si hay informes nuevos, actualizados o retirados;
  si no cambió nada, queda en silencio.

## Privacidad

- Credenciales y cadenas de conexión **solo por variables de entorno** (`.env`, no versionado).
- La base se consulta en **modo lectura** sobre vistas de reportes.
- `estudiantes.json`, la base local de contraseñas y los PDF **nunca se versionan**.
- Los datos de este módulo son **sintéticos** (`data/ejemplo_estudiantes.json`).

## Puesta en marcha

```bash
pip install -r requirements.txt
cp .env.example .env                  # completa host/base/usuario/clave
cp config/evaluaciones.example.json config/evaluaciones.json   # coloca tus identificadores
export AJ_WEB=web AJ_INFORMES=informes_2026
uvicorn app:app --host 0.0.0.0 --port 8080    # desde la carpeta web/
```

Requiere además la plantilla del informe y las fuentes tipográficas, que no se versionan por licencia.
