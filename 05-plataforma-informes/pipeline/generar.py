# -*- coding: utf-8 -*-
"""Genera o ACTUALIZA los informes AJ 2026 de forma incremental.

- Solo rehace el PDF cuyo contenido cambió (huella por estudiante).
- Reescribe manifest.json (total, completos, incompletos, huella, bytes).
- Mueve a informes_2026/_obsoletos/ los PDF de estudiantes que ya no están.

Uso:  python3 pipeline/generar.py [--todo]
      --todo  rehace los 284 aunque no hayan cambiado
"""
import hashlib
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fitz  # noqa: E402
import gen as GEN  # noqa: E402

AJ = os.path.dirname(HERE)
TOV = os.path.join(AJ, "informe_personal_tov")
FUENTE = os.environ.get("AJ_FUENTE", os.path.join(TOV, "datos_integrados_ancash.json"))
OUT = os.environ.get("AJ_INFORMES", os.path.join(AJ, "informes_2026"))
MANIFEST = os.path.join(OUT, "manifest.json")
OBSOLETOS = os.path.join(OUT, "_obsoletos")
PLANTILLA = os.path.join(HERE, "plantilla", "Plantilla_informe_personal_AJ_2026.pdf")


def version_pipeline() -> str:
    """Huella del motor + plantilla: si cambia, se rehace todo."""
    h = hashlib.sha256()
    for f in (os.path.join(HERE, "gen.py"), PLANTILLA):
        with open(f, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()[:12]


def huella(e: dict, ver: str) -> str:
    d = json.dumps({"v": ver, "e": e}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(d.encode()).hexdigest()[:16]


def main():
    todo = "--todo" in sys.argv
    ver = version_pipeline()
    data = json.load(open(FUENTE, encoding="utf-8"))
    data.sort(key=lambda x: (x.get("estudiante") or "").upper())

    prev = {}
    if os.path.exists(MANIFEST):
        m = json.load(open(MANIFEST, encoding="utf-8"))
        prev = {x.get("clave"): x for x in m.get("informes", []) if x.get("clave")}

    os.makedirs(OUT, exist_ok=True)
    mtime_fuente = os.path.getmtime(FUENTE)
    nuevos = actualizados = iguales = 0
    errores = []
    cambiados = []
    man = []
    t0 = time.time()

    for e in data:
        nom = e.get("estudiante") or "(sin nombre)"
        h = huella(e, ver)
        p = prev.get(e.get("clave")) or {}
        arch = p.get("archivo") or ("AJ_2026_" + GEN.slug(nom) + ".pdf")
        ruta = os.path.join(OUT, arch)
        existe = os.path.exists(ruta)
        bytes_ok = existe and os.path.getsize(ruta) == p.get("bytes")

        # sin cambios -> se conserva tal cual
        if not todo and existe and bytes_ok and (
                p.get("huella") == h or
                (not p.get("huella") and os.path.getmtime(ruta) >= mtime_fuente)):
            man.append({**p, "huella": h, "archivo": arch})
            iguales += 1
            continue

        try:
            doc, ctx = GEN.build(e)
            acad_ok = len(ctx["acad"]) >= 2
            hse_ok = bool(ctx["hse_total"]) and len(ctx["hse_dims"]) >= 1
            faltan = []
            if not acad_ok:
                faltan.append("academico")
            if not hse_ok:
                faltan.append("socioemocional")
            tmp = ruta + ".tmp"
            doc.save(tmp, garbage=4, deflate=True)
            doc.close()
            os.replace(tmp, ruta)
            man.append({"estudiante": nom, "archivo": arch, "completo": bool(acad_ok and hse_ok),
                        "faltan": faltan, "grado": ctx.get("grado"), "ie": ctx.get("ie"),
                        "clave": e.get("clave"), "bytes": os.path.getsize(ruta), "huella": h})
            if p:
                actualizados += 1
            else:
                nuevos += 1
            cambiados.append(e.get("clave"))
        except Exception as ex:
            errores.append((nom, type(ex).__name__ + ": " + str(ex)[:90]))
            if p:
                man.append(p)  # se conserva el informe anterior válido

    # PDF de estudiantes que ya no están en la fuente
    vigentes = {x["archivo"] for x in man if x.get("archivo")}
    obsoletos = []
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".pdf") and f not in vigentes:
            os.makedirs(OBSOLETOS, exist_ok=True)
            shutil.move(os.path.join(OUT, f), os.path.join(OBSOLETOS, f))
            obsoletos.append(f)

    json.dump({"generado": time.strftime("%Y-%m-%d %H:%M"),
               "version_pipeline": ver,
               "fuente": os.path.relpath(FUENTE, AJ),
               "total": len(man),
               "completos": sum(1 for m in man if m["completo"]),
               "incompletos": sum(1 for m in man if not m["completo"]),
               "informes": man},
              open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # lista de lo que cambió, para auditar solo eso en la próxima corrida
    logs = os.path.join(HERE, "logs")
    os.makedirs(logs, exist_ok=True)
    json.dump({"version": ver, "todo": bool(todo or not man),
               "claves": [c for c in cambiados if c]},
              open(os.path.join(logs, "cambiados.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    mb = sum(m.get("bytes") or 0 for m in man) / 1e6
    print(f"INFORMES -> total {len(man)} | nuevos {nuevos} | actualizados {actualizados} | "
          f"sin cambio {iguales} | obsoletos {len(obsoletos)} | errores {len(errores)} | "
          f"{mb:.0f} MB | {time.time()-t0:.0f}s")
    for n, msg in errores[:8]:
        print("   ERR", n[:34], "|", msg)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
