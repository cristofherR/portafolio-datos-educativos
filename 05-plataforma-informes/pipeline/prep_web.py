# -*- coding: utf-8 -*-
"""Prepara los datos de la plataforma: estudiantes.json + copia local de credenciales.

- estudiantes.json: jerarquía oficial (vista reportes.vw_aj_dims_tov_2026) + estado
  del manifest de informes. Si la BD no responde, conserva la jerarquía local y solo
  refresca archivo/completo/faltan desde el manifest.
- plataforma.db: NO se borra. Solo se actualizan las cuentas cuyo hash o estado
  cambiaron; nunca se reinician intentos fallidos ni bloqueos.
"""
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AJ = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA = os.path.join(AJ, "web", "data")
EST_JSON = os.path.join(DATA, "estudiantes.json")
DB = os.path.join(DATA, "plataforma.db")
MANIFEST = os.path.join(AJ, "informes_2026", "manifest.json")
os.makedirs(DATA, exist_ok=True)


def desde_bd():
    try:
        from db import conn
        c = conn()
        cur = c.cursor()
        cur.execute("""select clave, dni, estudiante, genero, academia, ie, centro_poblado,
                              grado, salon, seccion
                       from reportes.vw_aj_dims_tov_2026""")
        cols = [d[0] for d in cur.description]
        est = [dict(zip(cols, r)) for r in cur.fetchall()]
        cur.execute("""select dni, password_hash, is_active, failed_attempts, locked_until,
                              last_login_at
                       from public.auth_accounts""")
        ac = [d[0] for d in cur.description]
        cuentas = [dict(zip(ac, r)) for r in cur.fetchall()]
        c.close()
        return est, cuentas
    except Exception as ex:
        print("  AVISO: BD no disponible (%s). Se conserva la jerarquía local." % type(ex).__name__)
        return None, None


def main():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    por_clave = {m["clave"]: m for m in man["informes"] if m.get("clave")}
    est, cuentas = desde_bd()

    if est:
        estudiantes = [{
            "clave": e["clave"], "dni": e["dni"], "estudiante": e["estudiante"],
            "genero": e["genero"], "academia": e["academia"], "ie": e["ie"],
            "centro_poblado": e["centro_poblado"], "grado": e["grado"],
            "aula": e["salon"], "seccion": e["seccion"],
            "archivo": (por_clave.get(e["clave"]) or {}).get("archivo"),
            "completo": bool((por_clave.get(e["clave"]) or {}).get("completo")),
            "faltan": (por_clave.get(e["clave"]) or {}).get("faltan", []),
        } for e in est]
        print("  jerarquía desde la BD:", len(estudiantes), "estudiantes")
    else:
        prev = json.load(open(EST_JSON, encoding="utf-8"))["estudiantes"]
        estudiantes = []
        for e in prev:
            m = por_clave.get(e.get("clave")) or {}
            estudiantes.append({**e,
                                "archivo": m.get("archivo", e.get("archivo")),
                                "completo": bool(m.get("completo", e.get("completo"))),
                                "faltan": m.get("faltan", e.get("faltan", []))})
        print("  jerarquía local conservada:", len(estudiantes), "estudiantes")

    faltan_archivo = [x["estudiante"] for x in estudiantes if not x.get("archivo")]
    estudiantes.sort(key=lambda x: (x["estudiante"] or "").upper())
    tmp = EST_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"generado": man["generado"], "total": len(estudiantes),
                   "completos": sum(1 for x in estudiantes if x["completo"]),
                   "sin_informe": len(faltan_archivo),
                   "estudiantes": estudiantes}, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, EST_JSON)  # escritura atómica: la web nunca ve un archivo a medias
    print(f"  estudiantes.json -> {len(estudiantes)} (sin informe: {len(faltan_archivo)})")

    if not cuentas:
        print("  plataforma.db: sin datos nuevos de la intranet (no se toca)")
        return 0

    sc = sqlite3.connect(DB)
    sc.execute("""create table if not exists cuentas(
        dni text primary key, password_hash text, is_active integer,
        failed_attempts integer default 0, locked_until text, last_login_at text)""")
    nuevos = cambios = iguales = 0
    for x in cuentas:
        row = sc.execute("select password_hash, is_active from cuentas where dni=?",
                         (x["dni"],)).fetchone()
        activo = 1 if x["is_active"] else 0
        if row is None:
            sc.execute("""insert into cuentas(dni, password_hash, is_active, failed_attempts,
                                             locked_until, last_login_at) values(?,?,?,?,?,?)""",
                       (x["dni"], x["password_hash"], activo, x["failed_attempts"] or 0,
                        x["locked_until"].isoformat() if x["locked_until"] else None,
                        x["last_login_at"].isoformat() if x["last_login_at"] else None))
            nuevos += 1
        elif row[0] != x["password_hash"] or row[1] != activo:
            # solo cambia credencial/estado: contadores y bloqueos se respetan
            sc.execute("update cuentas set password_hash=?, is_active=? where dni=?",
                       (x["password_hash"], activo, x["dni"]))
            cambios += 1
        else:
            iguales += 1
    sc.commit()
    n = sc.execute("select count(*) from cuentas").fetchone()[0]
    aj = sc.execute("select count(*) from cuentas where lower(dni) like 'aj%'").fetchone()[0]
    sc.close()
    print(f"  plataforma.db -> {n} cuentas ({aj} AJ*) | nuevas {nuevos} | actualizadas {cambios} "
          f"| sin cambio {iguales}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
