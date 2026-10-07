#!/usr/bin/env python3
"""Sankey HSE Academia Juvenil — flujo de estudiantes entre categorias oficiales.

Base: SOLO estudiantes con ambos cortes (Inicio y Proceso) — la base la filtra
`hse_aj_crecimiento.py` (>=38/42 respuestas en cada corte).

12 diagramas: 4 habilidades socioemocionales x 3 academias
(AJ Cuenca, AJ Huaripampa, AJ Huarmey). Valle Fortaleza queda fuera: sin corte Proceso.

Las categorias son las 7 OFICIALES del instrumento, por habilidad
(bandas HSE_RANGOS del radar AJ).

Uso: python3 python/hse_aj_sankey.py
Entrada: <AJ_ENTRADA>/agregados_hse_crecimiento.json
         (por defecto, el ejemplo SINTÉTICO incluido en data/synthetic/)
Salida:  <AJ_SALIDA>/graficos_sankey/*.png  +  <AJ_SALIDA>/Sankey_HSE_AJ.pdf

Variables de entorno opcionales:
  AJ_ENTRADA  carpeta con el JSON de entrada
  AJ_SALIDA   carpeta de salida (por defecto ./salidas)

Solo agregados: nunca datos identificables de estudiantes.
"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.backends.backend_pdf import PdfPages

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.environ.get("AJ_ENTRADA", os.path.join(RAIZ, "data", "synthetic"))
SALIDA = os.environ.get("AJ_SALIDA", os.path.join(RAIZ, "salidas"))
DEST = os.path.join(SALIDA, "graficos_sankey")
os.makedirs(DEST, exist_ok=True)

NIVEL7 = ["MUY BAJO", "BAJO", "PROMEDIO BAJO", "PROMEDIO", "PROMEDIO ALTO", "ALTO", "MUY ALTO"]
TOP = list(reversed(NIVEL7))          # dibujo de arriba (mejor) hacia abajo (peor)

# color por categoria (verde = mejor)
COLOR_NIVEL = {
    "MUY ALTO": "#1B5E20", "ALTO": "#43A047", "PROMEDIO ALTO": "#A5D6A7",
    "PROMEDIO": "#FDD835", "PROMEDIO BAJO": "#FB8C00",
    "BAJO": "#E53935", "MUY BAJO": "#8E1F1F",
}
C_SUBE, C_BAJA, C_IGUAL = "#2E7D32", "#C62828", "#9E9E9E"

with open(os.path.join(ENTRADA, "agregados_hse_crecimiento.json"), encoding="utf-8") as fh:
    AGG = json.load(fh)

SANK = AGG["sankey"]


def layout(conteos, alto=1.0, hueco=0.012):
    """Devuelve {nivel: (y0, y1)} proporcional al conteo, de arriba hacia abajo."""
    total = sum(conteos.values()) or 1
    n_vis = sum(1 for n in TOP if conteos.get(n))
    espacio = alto - hueco * max(0, n_vis - 1)
    pos, y = {}, alto
    for n in TOP:
        c = conteos.get(n, 0)
        if c:
            h = espacio * c / total
            pos[n] = (y - h, y)
            y -= h + hueco
    return pos


def cintas(ax, pos_i, pos_p, flujos, x0=0.16, x1=0.84):
    """Dibuja las cintas. Usa acumuladores para repartir la altura de cada nodo."""
    usado_i = {n: pos_i[n][1] for n in pos_i}          # se llena de arriba hacia abajo
    usado_p = {n: pos_p[n][1] for n in pos_p}
    total = sum(flujos.values()) or 1

    def orden(k):
        a, b = k.split(" -> ")
        return (TOP.index(a), TOP.index(b))

    for k in sorted(flujos, key=orden):
        c = flujos[k]
        if not c:
            continue
        a, b = k.split(" -> ")
        if a not in pos_i or b not in pos_p:
            continue
        hi = (pos_i[a][1] - pos_i[a][0]) * c / max(1, sum(v for kk, v in flujos.items()
                                                        if kk.split(" -> ")[0] == a))
        hp = (pos_p[b][1] - pos_p[b][0]) * c / max(1, sum(v for kk, v in flujos.items()
                                                        if kk.split(" -> ")[1] == b))
        y0a, y0b = usado_i[a], usado_i[a] - hi
        y1a, y1b = usado_p[b], usado_p[b] - hp
        usado_i[a] -= hi
        usado_p[b] -= hp
        if TOP.index(b) > TOP.index(a):
            col, al = C_BAJA, 0.45
        elif TOP.index(b) < TOP.index(a):
            col, al = C_SUBE, 0.45
        else:
            col, al = C_IGUAL, 0.30
        xm = (x0 + x1) / 2
        verts = [(x0, y0a), (xm, y0a), (xm, y1a), (x1, y1a),
                 (x1, y1b), (xm, y1b), (xm, y0b), (x0, y0b), (x0, y0a)]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                 Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), facecolor=col, alpha=al,
                               edgecolor="none", lw=0))


def etiquetas(ax, pos, conteos, x, lado, sep=0.032):
    """Etiquetas legibles: si dos nodos quedan muy juntos, las separa y traza guia."""
    total = sum(conteos.values()) or 1
    filas = [{"niv": n, "y": (y0 + y1) / 2, "c": conteos[n]}
             for n, (y0, y1) in sorted(pos.items(), key=lambda kv: -kv[1][1])]
    y_lab = None
    for f in filas:
        y = f["y"] if y_lab is None else min(f["y"], y_lab - sep)
        f["yl"] = y
        y_lab = y
    # si el conjunto se fue demasiado abajo, lo empujo hacia arriba
    if filas and filas[-1]["yl"] < 0.005:
        y_lab = None
        for f in reversed(filas):
            y = f["y"] if y_lab is None else max(f["y"], y_lab + sep)
            f["yl"] = y
            y_lab = y
    for f in filas:
        pct = 100 * f["c"] / total
        txt = f"{f['niv']}  {f['c']} ({pct:.0f}%)"
        if lado == "i":
            ax.plot([x - 0.004, x - 0.030], [f["y"], f["yl"]], color="#BDBDBD", lw=0.6, zorder=1)
            ax.text(x - 0.034, f["yl"], txt, ha="right", va="center", fontsize=8.4)
        else:
            ax.plot([x + 0.039, x + 0.065], [f["y"], f["yl"]], color="#BDBDBD", lw=0.6, zorder=1)
            ax.text(x + 0.069, f["yl"], txt, ha="left", va="center", fontsize=8.4)


def dibujar(ax, d, titulo, subtitulo):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.06); ax.axis("off")
    ax.set_title(titulo, fontsize=13, fontweight="bold", loc="left", pad=14)
    ax.text(0, 1.015, subtitulo, fontsize=9.2, color="#333", va="bottom")

    pos_i = layout(d["niveles_inicio"])
    pos_p = layout(d["niveles_proceso"])
    cintas(ax, pos_i, pos_p, {k: v for k, v in d["flujos"].items()})

    for pos, x in ((pos_i, 0.16), (pos_p, 0.84)):
        for niv, (y0, y1) in pos.items():
            ax.add_patch(Rectangle((x, y0), 0.035, max(y1 - y0, 0.004),
                                   facecolor=COLOR_NIVEL[niv], edgecolor="white", lw=0.6))

    etiquetas(ax, pos_i, d["niveles_inicio"], 0.16, "i")
    etiquetas(ax, pos_p, d["niveles_proceso"], 0.84, "p")
    ax.text(0.16, 0.995, "INICIO", ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    ax.text(0.84, 0.995, "PROCESO", ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    ley = (f"verde = subio de categoria ({d['subieron']})   ·   "
           f"rojo = bajo ({d['bajaron']})   ·   gris = se quedo igual ({d['mismo']})")
    ax.text(0.5, -0.035, ley, ha="center", va="top", fontsize=9, color="#333")


pdf = PdfPages(os.path.join(SALIDA, "Sankey_HSE_AJ.pdf"))
hechos = []
for clave, d in SANK.items():
    ac, hab = d["academia"], d["habilidad"]
    titulo = f"{ac} · {hab}"
    subt = (f"n={d['n']} estudiantes con AMBOS cortes · "
            f"subieron de categoria: {100*d['subieron']/max(1,d['n']):.0f}% · "
            f"bajaron: {100*d['bajaron']/max(1,d['n']):.0f}% · "
            f"igual: {100*d['mismo']/max(1,d['n']):.0f}%")
    fig = plt.figure(figsize=(11.5, 7.6), dpi=150)
    ax = fig.add_axes([0.13, 0.10, 0.74, 0.78])
    dibujar(ax, d, titulo, subt)
    nombre = f"Sankey_{ac.replace('AJ ','').replace(' ','_')}_{hab.replace(' ','_')}.png"
    fig.savefig(os.path.join(DEST, nombre), bbox_inches="tight", facecolor="white")
    pdf.savefig(fig, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    hechos.append(nombre)

pdf.close()
print(f"{len(hechos)} diagramas -> {DEST}")
for h in hechos:
    print("  ", h)
print("PDF ->", os.path.join(SALIDA, "Sankey_HSE_AJ.pdf"))
