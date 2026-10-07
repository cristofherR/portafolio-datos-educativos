#!/usr/bin/env python3
"""
=============================================================================
 AJ RADAR HABILIDADES — Tabla larga para Deneb (radar + cartilla estudiante)
=============================================================================
Genera una fila por (estudiante × prueba × área × habilidad) con:
  - Correctas / Total_Items / Pct_Estudiante  (% de logro por habilidad)
  - Pct_Aula                                   (promedio del aula del estudiante)
  - idx / N                                    (para el radar de ejes dinámicos)
  - Titulo                                     (header del radar)
  - Categoria_Semaforo                         (Tercio superior / En proceso / Requiere apoyo)
  - Categoria_HSE                              (7 niveles oficiales, solo HSE)

Fuente: rptas_correctas.metadatos (habilidad por pregunta) — verificado completo.
HSE: los pesos YA vienen invertidos en la BD (Nunca=5 en items inversos).

Uso:  python3 aj_radar_habilidades.py
Salida: aj_radar_habilidades.csv  +  aj_radar_habilidades.json
=============================================================================
"""
import psycopg2
import json
import os
import csv
from collections import defaultdict

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", ""),
    "dbname": os.environ.get("DB_NAME", ""),
    "user": os.environ.get("DB_USER", ""),
    "password": os.environ.get("DB_PASSWORD", ""),  # nunca versionar credenciales
    "sslmode": "require",
}
if not all([DB_CONFIG["host"], DB_CONFIG["dbname"], DB_CONFIG["user"], DB_CONFIG["password"]]):
    raise SystemExit(
        "Faltan credenciales: define DB_HOST, DB_NAME, DB_USER y DB_PASSWORD "
        "como variables de entorno (ver .env.example)."
    )

AJ_EVALUACIONES = {  # IDs de evaluación de tu propio modelo; no versionar los reales
    "COAR": os.environ.get("AJ_EVAL_COAR", "<UUID_COAR>"),
    "Pronabec_Comunicacion": os.environ.get("AJ_EVAL_PRONABEC_COM", "<UUID_PRONABEC_COM>"),
    "Pronabec_Matematica": os.environ.get("AJ_EVAL_PRONABEC_MAT", "<UUID_PRONABEC_MAT>"),
    "HSE Academia Juvenil": os.environ.get("AJ_EVAL_HSE", "<UUID_HSE>"),
}

CONTEXTOS_SEDE = {
    "AJCuenca": "<UUID_INTERNO>",
    "AJHuaripampa": "<UUID_INTERNO>",
    "AJHuarmey": "<UUID_INTERNO>",
    "AJValleFortaleza": "<UUID_INTERNO>",
    "AJVistoso": "<UUID_INTERNO>",
    "AJAgropecuario": "<UUID_INTERNO>",
    "AJAyashPichiu": "<UUID_INTERNO>",
    "AJHppAlto": "<UUID_INTERNO>",
    "AJHppBajo": "<UUID_INTERNO>",
    "AJTecnico": "<UUID_INTERNO>",
    "AJPIURA": "<UUID_INTERNO>",
    "AJAncash": "342a9135-1a0d-4efa-9971-038e7e33ancash",
}

BLANCO_KEYWORDS = {"En blanco", "BL.", "No respondió la pregunta"}
INVALIDO_KEYWORD = "Inválido"

# Mapa (prueba, área) → header del radar
TITULOS = {
    ("COAR", "Mate"): "MATEMÁTICA · COAR",
    ("COAR", "Comu"): "COMUNICACIÓN · COAR",
    ("Pronabec_Comunicación", "Comu"): "COMUNICACIÓN · PRONABEC",
    ("Pronabec_Matemática", "Mate"): "MATEMÁTICA · PRONABEC",
    ("HSE Academia Juvenil", "HSE"): "HSE · HABILIDADES SOCIOEMOCIONALES",
}

# Área según curso del metadato (solo COAR los distingue)
AREA_POR_CURSO = {
    "Comprensión lectora": "Comu",
    "Razonamiento matemático": "Mate",
}

# Rangos oficiales HSE (7 niveles) por habilidad — para semáforo fiel al instrumento
HSE_RANGOS = {
    "Asertividad": [(50, "MUY ALTO"), (45, "ALTO"), (42, "PROMEDIO ALTO"), (39, "PROMEDIO"), (33, "PROMEDIO BAJO"), (21, "BAJO"), (0, "MUY BAJO")],
    "Comunicación": [(40, "MUY ALTO"), (36, "ALTO"), (33, "PROMEDIO ALTO"), (30, "PROMEDIO"), (25, "PROMEDIO BAJO"), (20, "BAJO"), (0, "MUY BAJO")],
    "Autoestima": [(55, "MUY ALTO"), (51, "ALTO"), (47, "PROMEDIO ALTO"), (42, "PROMEDIO"), (35, "PROMEDIO BAJO"), (21, "BAJO"), (0, "MUY BAJO")],
    "Toma de decisiones": [(41, "MUY ALTO"), (37, "ALTO"), (34, "PROMEDIO ALTO"), (30, "PROMEDIO"), (25, "PROMEDIO BAJO"), (17, "BAJO"), (0, "MUY BAJO")],
}
HSE_3_ESTADOS = {"MUY BAJO": "Requiere apoyo", "BAJO": "Requiere apoyo",
                 "PROMEDIO BAJO": "En proceso", "PROMEDIO": "En proceso", "PROMEDIO ALTO": "En proceso",
                 "ALTO": "Tercio superior", "MUY ALTO": "Tercio superior"}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def as_dict(v):
    return v if isinstance(v, dict) else (json.loads(v) if v else {})


def categoria_pct(pct):
    """Semáforo académico por % de logro."""
    if pct >= 70:
        return "Tercio superior"
    if pct >= 40:
        return "En proceso"
    return "Requiere apoyo"


def categoria_hse(puntaje, habilidad):
    """7 niveles oficiales HSE → luego mapear a 3 estados."""
    for umbral, nivel in HSE_RANGOS.get(habilidad, [(0, "MUY BAJO")]):
        if puntaje >= umbral:
            return nivel
    return "MUY BAJO"


def main():
    print("=" * 66)
    print("  📡 AJ RADAR HABILIDADES — tabla larga para Deneb")
    print("=" * 66)
    conn = get_conn()
    cur = conn.cursor()
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # ── 1. Definiciones de las 4 pruebas ─────────────────────────────────
    pruebas = {}
    for nombre, pk in AJ_EVALUACIONES.items():
        cur.execute("""SELECT curso, rptas_correctas FROM bd_evaluaciones.evaluacion WHERE pk=%s""", (pk,))
        row = cur.fetchone()
        if not row:
            print(f"  [WARN] {nombre} no encontrada"); continue
        rc = as_dict(row[1])
        pruebas[nombre] = {
            "pk": pk,
            "curso": row[0],
            "preguntas": rc.get("preguntas", {}),
            "metadatos": rc.get("metadatos", {}),
            "es_likert": "hse" in (row[0] or "").lower() or "habilidades" in (row[0] or "").lower(),
        }
        print(f"  [OK] {nombre}: {len(pruebas[nombre]['preguntas'])} preguntas")

    # ── 2. Datos maestros (bulk) ─────────────────────────────────────────
    cur.execute("SELECT pk, nombres_completo, dni_ce, genero FROM bd_evaluaciones.estudiantes")
    estudiantes = {r[0]: r for r in cur.fetchall()}

    cur.execute("SELECT id_estudiante, id_seccion FROM bd_evaluaciones.matriculacion_estudiantes WHERE anio='2026'")
    matricula = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT pk, num_grado, nivel_grado, seccion, fk_salon FROM bd_evaluaciones.secciones")
    secciones = {r[0]: r for r in cur.fetchall()}

    cur.execute("SELECT pk, nombre, id_ie, codmod FROM bd_evaluaciones.salones")
    salones = {r[0]: r for r in cur.fetchall()}

    # mapa sección → sede
    mapa_sec_sede = {}
    for cod_sede, ctx_pk in CONTEXTOS_SEDE.items():
        cur.execute("""SELECT idseccion FROM bd_evaluaciones.rel_salon_contexto WHERE idcontexto=%s""", (ctx_pk,))
        for (sec,) in cur.fetchall():
            mapa_sec_sede[sec] = cod_sede

    # ── 3. Scoring por habilidad ─────────────────────────────────────────
    # Precomputar área por habilidad para cada prueba (evita usar área de la última pregunta)
    area_por_habilidad = {}
    for nombre_prueba, info in pruebas.items():
        for num_preg, def_preg in info["preguntas"].items():
            meta = info["metadatos"].get(num_preg, {})
            habilidad = (meta.get("habilidad") or "SIN HABILIDAD").strip()
            curso_meta = (meta.get("curso") or "").strip()
            area = AREA_POR_CURSO.get(curso_meta) or (
                "HSE" if info["es_likert"]
                else ("Comu" if "Comunicación" in nombre_prueba else "Mate"))
            area_por_habilidad[(nombre_prueba, habilidad)] = area

    # filas: (estudiante, prueba, area, habilidad) → acumuladores
    acum = defaultdict(lambda: {"correctas": 0, "total": 0})
    info_est = {}   # id_estudiante → datos fijos
    evaluados_por_prueba = defaultdict(int)

    for nombre_prueba, info in pruebas.items():
        cur.execute("""
            SELECT e.fk_evaluado, e.respuestas
            FROM bd_evaluaciones.evaluaciones e
            WHERE e.fk_caracteristica_evaluacion = %s
              AND e.respuestas IS NOT NULL AND e.respuestas::text != '{}'
              AND e.fk_digitador IS NOT NULL AND e.fecha_entrega IS NOT NULL
        """, (info["pk"],))
        rows = cur.fetchall()
        print(f"\n  Procesando {nombre_prueba}: {len(rows)} evaluaciones reales")

        for fk_evaluado, respuestas in rows:
            resp = as_dict(respuestas)
            est_row = estudiantes.get(fk_evaluado)
            if not est_row:
                continue
            evaluados_por_prueba[nombre_prueba] += 1

            # acumular por habilidad
            por_habilidad = defaultdict(lambda: {"correctas": 0, "total": 0})
            for num_preg, def_preg in info["preguntas"].items():
                meta = info["metadatos"].get(num_preg, {})
                habilidad = (meta.get("habilidad") or "SIN HABILIDAD").strip()

                resp_alumno = resp.get(f"preg_{num_preg}", "")
                puntajes = [r["peso"] for r in def_preg.get("respuestas", [])]
                max_preg = max(puntajes) if puntajes else 0
                por_habilidad[habilidad]["total"] += max_preg

                if resp_alumno in BLANCO_KEYWORDS or resp_alumno == INVALIDO_KEYWORD:
                    continue
                peso = 0
                for opcion in def_preg.get("respuestas", []):
                    if opcion["texto"] == resp_alumno:
                        peso = opcion["peso"]
                        break
                por_habilidad[habilidad]["correctas"] += peso

            # guardar info del estudiante
            id_seccion = matricula.get(fk_evaluado)
            sec_row = secciones.get(id_seccion) if id_seccion else None
            salon_row = salones.get(sec_row[4]) if sec_row and sec_row[4] else None
            info_est[fk_evaluado] = {
                "estudiante": est_row[1] or "SIN NOMBRE",
                "dni": est_row[2] or "-",
                "genero": (est_row[3] or "S/D").strip().title()[:1] if est_row[3] else "S/D",
                "sede": mapa_sec_sede.get(id_seccion, "Sin sede") if id_seccion else "Sin sede",
                "grado": f"{sec_row[1]}° {sec_row[2]}" if sec_row and sec_row[1] else "",
                "aula": sec_row[3] if sec_row else "",
                "ie": salon_row[1] if salon_row else "",
                "id_seccion": id_seccion or None,
            }

            for habilidad, acc in por_habilidad.items():
                area = area_por_habilidad.get((nombre_prueba, habilidad), "Sin area")
                clave = (fk_evaluado, nombre_prueba, area, habilidad)
                acum[clave]["correctas"] += acc["correctas"]
                acum[clave]["total"] += acc["total"]

    # ── 4. Ensamblar filas ───────────────────────────────────────────────
    filas = []
    for (fk_evaluado, prueba, area, habilidad), acc in acum.items():
        est = info_est[fk_evaluado]
        pct = round(acc["correctas"] / acc["total"] * 100, 1) if acc["total"] else 0.0
        if prueba == "HSE Academia Juvenil":
            nivel7 = categoria_hse(acc["correctas"], habilidad)
            cat = HSE_3_ESTADOS.get(nivel7, "En proceso")
        else:
            nivel7 = ""
            cat = categoria_pct(pct)
        filas.append({
            "Estudiante": est["estudiante"], "DNI": est["dni"], "Genero": est["genero"],
            "Sede_AJ": est["sede"], "Grado": est["grado"], "Aula": est["aula"], "IE": est["ie"],
            "Prueba": prueba, "Area": area, "Habilidad": habilidad,
            "Correctas": acc["correctas"], "Total_Items": acc["total"],
            "Pct_Estudiante": pct, "Pct_Aula": None,
            "idx": None, "N": None, "Titulo": TITULOS.get((prueba, area), prueba),
            "Categoria_Semaforo": cat, "Categoria_HSE": nivel7,
            "_id_seccion": est["id_seccion"],
        })

    # ── 5. Pct_Aula (promedio por aula) + idx/N por grupo ────────────────
    # Pct_Aula: promedio de Pct_Estudiante por (id_seccion, prueba, area, habilidad)
    aula_prom = defaultdict(list)
    for f in filas:
        if f["_id_seccion"]:
            aula_prom[(f["_id_seccion"], f["Prueba"], f["Area"], f["Habilidad"])].append(f["Pct_Estudiante"])

    # idx/N: POR ESTUDIANTE — posicion de la habilidad (1..k) y N = numero de ejes
    # del radar de ese estudiante (NO el total de filas del grupo)
    grupos = defaultdict(list)
    for f in filas:
        grupos[(f["Estudiante"], f["Prueba"], f["Area"])].append(f)

    for (est, prueba, area), lista in grupos.items():
        lista.sort(key=lambda x: x["Habilidad"])
        n = len(lista)
        for i, f in enumerate(lista, start=1):
            f["idx"] = i
            f["N"] = n

    # asignar Pct_Aula
    for f in filas:
        if f["_id_seccion"]:
            vals = aula_prom.get((f["_id_seccion"], f["Prueba"], f["Area"], f["Habilidad"]), [])
            f["Pct_Aula"] = round(sum(vals) / len(vals), 1) if vals else None
        del f["_id_seccion"]

    # ── 6. Salida ────────────────────────────────────────────────────────
    cols = ["Estudiante", "DNI", "Genero", "Sede_AJ", "Grado", "Aula", "IE",
            "Prueba", "Area", "Habilidad", "Correctas", "Total_Items",
            "Pct_Estudiante", "Pct_Aula", "idx", "N", "Titulo",
            "Categoria_Semaforo", "Categoria_HSE"]
    csv_path = os.path.join(output_dir, "aj_radar_habilidades.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    json_path = os.path.join(output_dir, "aj_radar_habilidades.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=1)

    # ── 7. Resumen ───────────────────────────────────────────────────────
    print("\n" + "=" * 66)
    print("  📊 RESUMEN")
    print("=" * 66)
    for prueba, n in sorted(evaluados_por_prueba.items()):
        print(f"  {prueba:<30} {n} estudiantes")
    print(f"\n  Filas totales (habilidad×estudiante): {len(filas)}")
    for (prueba, area), lista in sorted(grupos.items()):
        habs = sorted({f['Habilidad'] for f in lista})
        print(f"  {prueba} | {area}: N={len(habs)} ejes -> {', '.join(habs)}")
    sin_aula = sum(1 for f in filas if f["Pct_Aula"] is None)
    print(f"  Filas sin aula (Pct_Aula vacío): {sin_aula} ({round(sin_aula/len(filas)*100,1)}%)")
    print(f"\n  ✅ CSV:  {csv_path}")
    print(f"  ✅ JSON: {json_path}")

    conn.close()


if __name__ == "__main__":
    main()
