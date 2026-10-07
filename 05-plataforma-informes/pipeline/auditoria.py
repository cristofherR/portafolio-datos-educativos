# -*- coding: utf-8 -*-
"""Auditoria geometrica: detecta TEXTO que cruza el borde de una tarjeta
en las 3 paginas del informe (mismo criterio para todas las secciones)."""
import json, sys, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fitz, gen as GEN

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "informe_personal_tov")
TOL = 1.0  # pt de tolerancia sobre el borde


def bordes(p):
    """Aristas (h y v) de las tarjetas con contorno."""
    H, V = [], []
    for dr in p.get_drawings():
        if dr.get("type") != "s":
            continue
        r = dr["rect"]
        if r.width > 100 and r.height > 15:
            H.append((r.y0, r.x0, r.x1, "top"))
            H.append((r.y1, r.x0, r.x1, "bot"))
            V.append((r.x0, r.y0, r.y1, "left"))
            V.append((r.x1, r.y0, r.y1, "right"))
    return H, V


def violaciones(doc):
    out = []
    for i in range(3):
        p = doc[i]
        H, V = bordes(p)
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    t = s["text"].strip()
                    if not t:
                        continue
                    x0, y0, x1, y1 = s["bbox"]
                    for (yy, ax0, ax1, cual) in H:
                        if ax0 - 2 <= x0 and x1 <= ax1 + 2 and (y0 - TOL) < yy < (y1 + TOL):
                            out.append((i + 1, cual, t[:55], round(yy, 1)))
                    for (xx, ay0, ay1, cual) in V:
                        if ay0 - 2 <= y0 and y1 <= ay1 + 2 and (x0 - TOL) < xx < (x1 + TOL):
                            out.append((i + 1, cual, t[:55], round(xx, 1)))
    return out


def main():
    data = json.load(open(BASE + "/datos_integrados_ancash.json", encoding="utf-8"))
    # --cambiados: audita solo lo que regenero la ultima corrida de generar.py
    if "--cambiados" in sys.argv:
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "cambiados.json")
        if os.path.exists(ruta):
            info = json.load(open(ruta, encoding="utf-8"))
            if not info.get("todo"):
                claves = set(info.get("claves") or [])
                data = [e for e in data if e.get("clave") in claves]
            print(f"   (auditoria acotada: {len(data)} informe(s) regenerado(s))")
    firmas = defaultdict(list)
    err = 0
    docs_ok = 0
    for e in data:
        try:
            doc, ctx = GEN.build(e)
        except Exception:
            err += 1
            continue
        docs_ok += 1
        for (pg, cual, txt, pos) in violaciones(doc):
            firmas[(pg, cual, txt, pos)].append(e["estudiante"])
        doc.close()
    print(f"documentos auditados: {docs_ok} | build con error: {err}")
    print(f"firmas de violacion distintas: {len(firmas)}")
    tot = sum(len(v) for v in firmas.values())
    print(f"violaciones totales: {tot}")
    for (pg, cual, txt, pos), est in sorted(firmas.items(), key=lambda x: -len(x[1]))[:25]:
        print(f"  p{pg} {cual:5} y/x={pos:6.1f} n={len(est):3}  :: {txt}")
    json.dump({f"p{k[0]}|{k[1]}|{k[2]}|{k[3]}": v for k, v in firmas.items()},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "auditoria.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
