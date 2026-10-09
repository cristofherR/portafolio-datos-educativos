#!/usr/bin/env python3
"""
Specs Deneb (Vega-Lite v5) de la PÁGINA INDIVIDUAL del TOV AJ 2026 · SOLO ÁNCASH.

v3 (28-sep-2026) — alineado a las vistas nuevas de la BD:
    radar      -> campos  area, orden, valor
    termómetro -> campos  bloque, orden, valor

Cambios vs v2:
  1. El top-3 de áreas YA NO viene del modelo (no existen area_top1..3): se
     calcula DENTRO del spec con un transform `window` (rank descendente sobre
     el promedio del estudiante filtrado).
  2. El bloque se llama exactamente "Barreras percibidas" (antes "(P63-P64)").
  3. No se arrastra `estudiante` al bucket: el nombre va en una tarjeta nativa
     de Power BI. Menos campos obligatorios = el visual no se rompe.
  4. Si un área no llega al mínimo de ítems del manual, el polígono cae a 0 en
     ese eje (transform `impute`).

Salidas:
    TOV_radar_individual_v3_SOLO_PEGAR.json
    TOV_termometro_individual_v3_SOLO_PEGAR.json
"""
import json, math, os

BASE = os.path.dirname(os.path.abspath(__file__))

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

DESC_VL = ("datum.promedio == 0 ? 'Sin datos' : "
           "datum.promedio <= 1.80 ? 'Desacuerdo marcado' : "
           "datum.promedio <= 2.60 ? 'Desacuerdo' : "
           "datum.promedio <= 3.40 ? 'Posición intermedia' : "
           "datum.promedio <= 4.20 ? 'Acuerdo' : 'Acuerdo marcado'")

TAM_LEYENDA = {"title": None, "orient": "bottom", "columns": 3, "labelFontSize": 9, "labelLimit": 200}
DESC_ENC = {"field": "descriptor", "type": "nominal",
            "scale": {"domain": TRAMOS, "range": COLORES}, "legend": TAM_LEYENDA}


def pol(r, orden, n=N):
    ang = -math.pi / 2 + 2 * math.pi * (orden - 1) / n
    return round(r * math.cos(ang), 4), round(r * math.sin(ang), 4)


def anillo(r, nombre, n=N):
    pts = [pol(r, o, n) for o in range(1, n + 1)]
    pts.append(pts[0])
    return [{"x": x, "y": y, "o": i, "anillo": nombre} for i, (x, y) in enumerate(pts)]


# --------------------------------------------------------------------------
# 1) RADAR INDIVIDUAL
# --------------------------------------------------------------------------
rings, spokes, labels = [], [], []
for r in (1, 2, 3, 4, 5):
    rings += anillo(r, f"r{r}")
for o in range(1, N + 1):
    x, y = pol(R_MAX, o)
    spokes.append({"x": 0, "y": 0, "x2": x, "y2": y})
    xl, yl = pol(R_TXT, o)
    labels.append({"x": xl, "y": yl, "txt": SHORT.get(AREAS[o - 1], AREAS[o - 1])})

PIPE = [
    {"filter": "isValid(datum.valor)"},
    {"aggregate": [{"op": "mean", "field": "valor", "as": "promedio"},
                   {"op": "valid", "field": "valor", "as": "n"}],
     "groupby": ["area", "orden"]},
    {"impute": "promedio", "key": "orden", "keyvals": list(range(1, N + 1)), "value": 0},
    {"impute": "n", "key": "orden", "keyvals": list(range(1, N + 1)), "value": 0},
    {"calculate": f"-PI/2 + 2*PI*(datum.orden-1)/{N}", "as": "ang"},
    {"calculate": "datum.promedio * cos(datum.ang)", "as": "x"},
    {"calculate": "datum.promedio * sin(datum.ang)", "as": "y"},
    {"calculate": DESC_VL, "as": "descriptor"},
]
# Vega-Lite: cada item de `transform` es UNA sola operación. `filter` NO puede
# convivir con `window`/`sort` en el mismo objeto (rompe la validación del Logs
# de Deneb: "must NOT have additional properties"). Van en dos objetos.
RANK = [{"filter": "datum.promedio > 0"},
        {"window": [{"op": "rank", "as": "rk"}],
         "sort": [{"field": "promedio", "order": "descending"},
                  {"field": "orden", "order": "ascending"}]}]

XY = {"x": {"field": "x", "type": "quantitative", "scale": {"domain": [-DOM, DOM]}, "axis": None},
      "y": {"field": "y", "type": "quantitative", "scale": {"domain": [-DOM, DOM]}, "axis": None}}

radar = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": ("Radar individual TOV · 12 áreas de afinidad declarada (Academia Juvenil 2026, Áncash). "
                    "El radio es el puntaje del estudiante filtrado en la página (escala 1-5). El aro naranja "
                    "punteado es el umbral 3.41 'Acuerdo' del manual. Los 3 ejes de mayor afinidad llevan aro "
                    "rojo (el top-3 se calcula aquí dentro). Arrastra area, orden y valor (No resumir)."),
    "background": "transparent",
    "width": 400, "height": 400, "padding": 6,
    "config": {"font": "Segoe UI", "view": {"stroke": None}},
    "layer": [
        {"data": {"values": rings},
         "mark": {"type": "line", "color": "#E6E6E6", "strokeWidth": 1},
         "encoding": {**XY, "detail": {"field": "anillo"}, "order": {"field": "o"}}},
        {"data": {"values": anillo(UMBRAL, "umbral")},
         "mark": {"type": "line", "color": "#F0A868", "strokeWidth": 1.4, "strokeDash": [5, 4]},
         "encoding": {**XY, "order": {"field": "o"}}},
        {"data": {"values": spokes},
         "mark": {"type": "rule", "color": "#EDEDED"},
         "encoding": {**XY, "x2": {"field": "x2"}, "y2": {"field": "y2"}}},
        {"data": {"values": labels},
         "mark": {"type": "text", "fontSize": 10, "color": "#565656",
                  "align": "center", "baseline": "middle"},
         "encoding": {**XY, "text": {"field": "txt"}}},
        {"transform": PIPE,
         "mark": {"type": "line", "color": "#1F4E79", "strokeWidth": 2.8, "opacity": 0.95,
                  "interpolate": "linear", "strokeJoin": "round"},
         "encoding": {**XY, "order": {"field": "ang"}}},
        {"transform": PIPE + [{"filter": "datum.orden == 1 || datum.orden == 12"}],
         "mark": {"type": "line", "color": "#1F4E79", "strokeWidth": 2.8, "opacity": 0.95},
         "encoding": {**XY, "order": {"field": "ang"}}},
        {"transform": PIPE + [{"filter": "datum.promedio > 0"}],
         "mark": {"type": "circle", "size": 80, "filled": True, "stroke": "white", "strokeWidth": 1.2},
         "encoding": {**XY, "color": DESC_ENC,
                      "tooltip": [{"field": "area", "type": "nominal", "title": "Área"},
                                  {"field": "promedio", "type": "quantitative", "title": "Puntaje", "format": ".2f"},
                                  {"field": "descriptor", "type": "nominal", "title": "Descriptor"},
                                  {"field": "n", "type": "quantitative", "title": "Ítems válidos"}]}},
        {"transform": PIPE + RANK + [{"filter": "datum.rk <= 3"}],
         "mark": {"type": "circle", "size": 260, "filled": False, "stroke": "#C00000",
                  "strokeWidth": 1.8, "opacity": 0.85},
         "encoding": XY},
    ],
}

# --------------------------------------------------------------------------
# 2) TERMÓMETRO DE BLOQUES
# --------------------------------------------------------------------------
BLOQUES = [("Claridad subjetiva", 1), ("Confianza decisional", 2), ("Metas personales", 3),
           ("Influencia familiar", 4), ("Apoyo familiar", 5), ("Barreras percibidas", 6)]

TERMO_TRAMOS = ["Desacuerdo marcado", "Desacuerdo", "Posición intermedia", "Acuerdo",
                "Acuerdo marcado", "Barreras percibidas (se lee al revés)"]
TERMO_COLORES = ["#C00000", "#ED7D31", "#BFA26B", "#9CC069", "#2E7D32", "#5B6B7B"]

PIPE_T = [
    {"filter": "isValid(datum.valor)"},
    {"aggregate": [{"op": "mean", "field": "valor", "as": "promedio"},
                   {"op": "valid", "field": "valor", "as": "n"}],
     "groupby": ["bloque", "orden"]},
    {"calculate": DESC_VL, "as": "descriptor"},
    {"calculate": "datum.bloque == 'Barreras percibidas' ? 'Barreras percibidas (se lee al revés)' "
                  ": (datum.promedio == 0 ? 'Sin datos' : datum.descriptor)",
     "as": "color_key"},
    {"calculate": "datum.promedio + 0.14", "as": "xlab"},
]

Y = {"field": "bloque", "type": "nominal", "sort": {"field": "orden", "op": "min"},
     "axis": {"title": None, "labelFontSize": 11, "labelLimit": 260, "labelPadding": 6,
              "domain": False, "ticks": False}}
X = {"field": "promedio", "type": "quantitative", "scale": {"domain": [1, 5], "nice": False},
     "axis": {"title": "Puntaje (escala 1-5)", "values": [1, 2, 3, 4, 5], "grid": True,
              "gridColor": "#F0F0F0", "titleFontSize": 10, "labelFontSize": 10}}

termo = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": ("Termómetro de bloques del TOV (Academia Juvenil 2026, Áncash). 6 bloques del proceso "
                    "de decisión, escala 1-5; la línea naranja punteada es el umbral 3.41 'Acuerdo'. "
                    "'Barreras percibidas' va en azul grisáceo porque se lee al revés. "
                    "Arrastra bloque, orden y valor (No resumir)."),
    "background": "transparent",
    "width": 430, "height": 210, "padding": 6,
    "config": {"font": "Segoe UI", "view": {"stroke": None}, "bar": {"cornerRadiusEnd": 3}},
    "layer": [
        {"transform": [{"filter": "isValid(datum.valor)"}],
         "mark": {"type": "rule", "color": "#F0A868", "strokeWidth": 1.4, "strokeDash": [5, 4]},
         "encoding": {"x": {"datum": UMBRAL}}},
        {"transform": PIPE_T,
         "mark": {"type": "bar", "height": 16},
         "encoding": {"y": Y, "x": X,
                      "color": {"field": "color_key", "type": "nominal",
                                "scale": {"domain": TERMO_TRAMOS, "range": TERMO_COLORES},
                                "legend": {"title": None, "orient": "bottom", "columns": 3,
                                           "labelFontSize": 9, "labelLimit": 220}},
                      "tooltip": [{"field": "bloque", "type": "nominal", "title": "Bloque"},
                                  {"field": "promedio", "type": "quantitative", "title": "Puntaje", "format": ".2f"},
                                  {"field": "descriptor", "type": "nominal", "title": "Descriptor"},
                                  {"field": "n", "type": "quantitative", "title": "Ítems válidos"}]}},
        {"transform": PIPE_T + [{"filter": "datum.promedio > 0"}],
         "mark": {"type": "text", "align": "left", "baseline": "middle", "fontSize": 10,
                  "fontWeight": "bold", "color": "#404040", "dx": 2},
         "encoding": {"y": Y, "x": {"field": "xlab", "type": "quantitative", "scale": {"domain": [1, 5]}},
                      "text": {"field": "promedio", "type": "quantitative", "format": ".1f"}}},
    ],
}

SALIDAS = [("TOV_radar_individual_v3_SOLO_PEGAR.json", radar),
           ("TOV_termometro_individual_v3_SOLO_PEGAR.json", termo)]

for nombre, spec in SALIDAS:
    ruta = os.path.join(BASE, nombre)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    print(f"escrito: {nombre} ({os.path.getsize(ruta)} B, {len(spec['layer'])} capas)")
