#!/usr/bin/env python3
"""
Genera el spec Deneb (Vega-Lite v5) del RADAR GRUPAL v2 de 12 areas del TOV.

Diferencia con la v1 (`hacer_spec_tov_radar.py`):
  1. `periodo` entra en el groupby y en el impute -> el radar puede mostrar la
     serie Inicio/Proceso (o quedar filtrado a un solo corte por el slicer de
     pagina), en vez de mezclar los dos cortes como hacia la v1.
  2. Bloque de configuracion al inicio (`cfg_*`) para ajustar colores/fuentes
     sin tocar la geometria.
  3. El cierre del poligono se hace por `detail` (una linea por corte) en vez de
     depender de que el orden de filas sea 1..12 sin cortes.
  4. `config.view.stroke` explicito a null (v1 lo dejaba implicito).

Campos que se arrastran al bucket Values de Deneb (todos "No resumir"):
    area, orden, valor, periodo, clave   (+ academia, centro_poblado, ie, grado, salon)

Salida: spec_tov_radar_grupal_v2.json
"""
import json, math, os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "spec_tov_radar_grupal_v2.json")
OUT_PEGAR = os.path.join(BASE, "TOV_radar_grupal_v2_SOLO_PEGAR.json")

N = 12
R_MAX = 5.5
R_TXT = 6.25
DOM = 6.8
UMBRAL = 3.41
AREAS = ["Ciencias", "Numérica", "Ingeniería", "Artística", "Social", "Emprendedora", "Salud",
         "Gastronómica", "Estética", "Deportiva", "Seguridad, defensa y orden público",
         "Aeronáutica y servicios de vuelo"]
SHORT = {"Seguridad, defensa y orden público": "Seguridad y\ndefensa",
         "Aeronáutica y servicios de vuelo": "Aeronáutica y\nvuelo",
         "Gastronómica": "Gastronomía"}
TRAMOS = ["Desacuerdo marcado", "Desacuerdo", "Posición intermedia", "Acuerdo", "Acuerdo marcado", "Sin datos"]
COLORES = ["#C00000", "#ED7D31", "#BFA26B", "#9CC069", "#2E7D32", "#D9D9D9"]


def pol(r, orden):
    ang = -math.pi / 2 + 2 * math.pi * (orden - 1) / N
    return round(r * math.cos(ang), 4), round(r * math.sin(ang), 4)


def anillo(r, nombre):
    pts = [pol(r, o) for o in range(1, N + 1)]
    pts.append(pts[0])
    return [{"x": x, "y": y, "o": i, "anillo": nombre} for i, (x, y) in enumerate(pts)]


rings, spokes, labels = [], [], []
for r in (1, 2, 3, 4, 5):
    rings += anillo(r, f"r{r}")
for o in range(1, N + 1):
    x, y = pol(R_MAX, o)
    spokes.append({"x": 0, "y": 0, "x2": x, "y2": y})
    xl, yl = pol(R_TXT, o)
    labels.append({"x": xl, "y": yl, "txt": SHORT.get(AREAS[o - 1], AREAS[o - 1])})

DESC_VL = ("datum.promedio == 0 ? 'Sin datos' : "
           "datum.promedio <= 1.80 ? 'Desacuerdo marcado' : "
           "datum.promedio <= 2.60 ? 'Desacuerdo' : "
           "datum.promedio <= 3.40 ? 'Posición intermedia' : "
           "datum.promedio <= 4.20 ? 'Acuerdo' : 'Acuerdo marcado'")

AGG = [{"op": "mean", "field": "valor", "as": "promedio"}, {"op": "valid", "field": "valor", "as": "n"}]
# El impute NO se usa: cada area tiene UN solo `orden` (1:1), asi que imputar
# `orden` dentro de groupby=["area","periodo"] expandia cada area a 12 filas
# (144 filas por corte) y el poligono se dibujaba en zigzag sobre las 144. Si un
# area se queda sin valores validos, su vertice simplemente no aparece.
CALC = [{"calculate": f"-PI/2 + 2*PI*(datum.orden-1)/{N}", "as": "ang"},
        {"calculate": "datum.promedio * cos(datum.ang)", "as": "x"},
        {"calculate": "datum.promedio * sin(datum.ang)", "as": "y"},
        {"calculate": DESC_VL, "as": "descriptor"}]
PIPE = ([{"filter": "isValid(datum.valor)"},
         {"aggregate": AGG, "groupby": ["area", "orden", "periodo"]}] + CALC)

XY = {"x": {"field": "x", "type": "quantitative", "scale": {"domain": [-DOM, DOM]}, "axis": None},
      "y": {"field": "y", "type": "quantitative", "scale": {"domain": [-DOM, DOM]}, "axis": None}}

PARAMS = [
    {"name": "cfg_fuente", "expr": "'Segoe UI'"},
    {"name": "cfg_anillo", "expr": "'#E6E6E6'"},
    {"name": "cfg_radio", "expr": "'#EDEDED'"},
    {"name": "cfg_umbral", "expr": "'#F0A868'"},
    {"name": "cfg_etq_color", "expr": "'#565656'"},
    {"name": "cfg_fs_etq", "expr": "9.5"},
    {"name": "cfg_color_inicio", "expr": "'#9CC0E0'"},
    {"name": "cfg_color_proceso", "expr": "'#1F4E79'"},
    {"name": "cfg_grosor", "expr": "2.6"},
    {"name": "cfg_ms_punto", "expr": "78"},
    {"name": "cfg_fs_leyenda", "expr": "9"},
]

spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": ("Radar grupal TOV v2 — 12 áreas de afinidad declarada (Academia Juvenil 2026). "
                    "Cada polígono es un corte (Inicio / Proceso); el slicer de página decide cuáles entran. "
                    "Anillo naranja punteado = umbral 3.41 'Acuerdo'. Ajusta colores en cfg_*."),
    "background": "transparent",
    "width": 400, "height": 400, "padding": 6,
    "config": {"view": {"stroke": None}},
    "params": PARAMS,
    "layer": [
        {"data": {"values": rings},
         "mark": {"type": "line", "color": {"expr": "cfg_anillo"}, "strokeWidth": 1},
         "encoding": {**XY, "detail": {"field": "anillo"}, "order": {"field": "o"}}},
        {"data": {"values": anillo(UMBRAL, "umbral")},
         "mark": {"type": "line", "color": {"expr": "cfg_umbral"}, "strokeWidth": 1.4,
                  "strokeDash": [5, 4]},
         "encoding": {**XY, "order": {"field": "o"}}},
        {"data": {"values": spokes},
         "mark": {"type": "rule", "color": {"expr": "cfg_radio"}},
         "encoding": {**XY, "x2": {"field": "x2"}, "y2": {"field": "y2"}}},
        {"data": {"values": labels},
         "mark": {"type": "text", "fontSize": {"expr": "cfg_fs_etq"}, "color": {"expr": "cfg_etq_color"},
                  "align": "center", "baseline": "middle"},
         "encoding": {**XY, "text": {"field": "txt"}}},
        {"transform": PIPE,
         "mark": {"type": "line", "strokeWidth": {"expr": "cfg_grosor"}, "opacity": 0.92,
                  "interpolate": "linear", "strokeJoin": "round"},
         "encoding": {**XY, "order": {"field": "ang"},
                      "color": {"field": "periodo", "type": "nominal",
                                "scale": {"domain": ["Inicio", "Proceso"],
                                          "range": [{"expr": "cfg_color_inicio"},
                                                    {"expr": "cfg_color_proceso"}]},
                                "legend": {"title": None, "orient": "bottom"}}}},
        {"transform": PIPE + [{"filter": "datum.orden == 1 || datum.orden == 12"}],
         "mark": {"type": "line", "strokeWidth": {"expr": "cfg_grosor"}, "opacity": 0.92},
         "encoding": {**XY, "order": {"field": "ang"},
                      "color": {"field": "periodo", "type": "nominal",
                                "scale": {"domain": ["Inicio", "Proceso"],
                                          "range": [{"expr": "cfg_color_inicio"},
                                                    {"expr": "cfg_color_proceso"}]},
                                "legend": None}}},
        {"transform": PIPE + [{"filter": "datum.promedio > 0"}],
         "mark": {"type": "circle", "size": {"expr": "cfg_ms_punto"}, "filled": True,
                  "stroke": "white", "strokeWidth": 1.2},
         "encoding": {**XY,
                      "color": {"field": "descriptor", "type": "nominal",
                                "scale": {"domain": TRAMOS, "range": COLORES},
                                "legend": {"title": None, "orient": "bottom", "columns": 3,
                                           "labelFontSize": {"expr": "cfg_fs_leyenda"}, "labelLimit": 200}},
                      "tooltip": [{"field": "area", "type": "nominal", "title": "Área"},
                                  {"field": "periodo", "type": "nominal", "title": "Corte"},
                                  {"field": "promedio", "type": "quantitative", "title": "Promedio grupo", "format": ".2f"},
                                  {"field": "n", "type": "quantitative", "title": "n válido"},
                                  {"field": "descriptor", "type": "nominal", "title": "Descriptor"}]}},
    ],
}

for ruta in (OUT, OUT_PEGAR):
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)

print("escrito:", os.path.basename(OUT), os.path.getsize(OUT), "B")
print("escrito:", os.path.basename(OUT_PEGAR), os.path.getsize(OUT_PEGAR), "B")
print("capas:", len(spec["layer"]), "| grupo del agregado: area, orden, periodo")
print("cfg (params):", ", ".join(p["name"] for p in PARAMS))
