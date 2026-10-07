# -*- coding: utf-8 -*-
"""
Genera el informe personal AJ 2026 SOBRE el diseno de la plantilla (Canva).
- Solo agrega textos faltantes y recolorea los indicadores de avance (barras/circulos).
- Sin emojis.
"""
import fitz, json, sys, os, re, datetime

BASE_AJ = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "informe_personal_tov")
sys.path.insert(0, BASE_AJ)
import generar_informe_integrado as G

TPL = os.environ.get("AJ_TPL", os.path.join(os.path.dirname(os.path.abspath(__file__)),
      "plantilla", "Plantilla_informe_personal_AJ_2026.pdf"))
OUTDIR = os.environ.get("AJ_OUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
os.makedirs(OUTDIR, exist_ok=True)
# Centro poblado + IE reales por clave (fuente: reportes.vw_aj_dims_tov_2026)
try:
    CPIE = json.load(open(os.environ.get("AJ_CPIE", os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deneb_tov", "cp_ie_por_clave.json")), encoding="utf-8"))
except OSError:
    CPIE = {}  # sin el mapeo clave->centro poblado/IE se usa el dato del propio registro
MINUS = {"de", "del", "la", "las", "los", "y", "e", "el"}
ORD = {"3": "3er", "4": "4to", "5": "5to"}


def tit(s):
    return " ".join(w.lower() if (w.lower() in MINUS and i) else w.capitalize()
                    for i, w in enumerate(s.split()))

FONTS = os.environ.get("AJ_FONTS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))
FF = {"osr": FONTS + "/OpenSans-Regular.ttf",
      "osb": FONTS + "/OpenSans-Bold.ttf",
      "ossb": FONTS + "/OpenSans-SemiBold.ttf",
      "gr": FONTS + "/Montserrat-400.ttf",
      "gb": FONTS + "/Montserrat-700.ttf",
      "nun": FONTS + "/Nunito-Regular.ttf"}
F = {k: fitz.Font(fontfile=v) for k, v in FF.items()}

GRIS = "#CBCCCD"
TRACK = "#E0E0E0"
VERDE = "#00BF63"
NARANJA = "#FF914D"
CELESTE = "#00AEEF"
CELESTE2 = "#0097B2"
TEAL = "#44A6A6"
TERRA = "#A96847"
VERDE_T = "#009684"
AMARILLO = "#FDC42F"
NARANJA_O = "#FF834D"
ROJO = "#ED1C24"
NAVY = "#1F3460"  # borde de las tarjetas de la plantilla

DISPLAY = {"Gastronómica": "Gastronomía"}
# Paleta oficial HSE (imagen institucional, 06-oct-2026): 7 niveles, 7 colores.
PILL_HSE = {"MUY ALTO": "#0A67BF", "ALTO": "#0A9967", "PROMEDIO ALTO": "#76C344",
            "PROMEDIO": "#FBD40B", "PROMEDIO BAJO": "#F6692C", "BAJO": "#B20A09",
            "MUY BAJO": "#595959"}  # gris oscuro (nivel mas bajo, neutro)
# Niveles academicos (PRONABEC): 3 estados con color propio.
NIVEL3_COLOR = {"En inicio": ROJO, "En proceso": NARANJA_O, "Tercio superior": "#166534"}
FILTRO_NIVEL = {"En inicio": ROJO, "En proceso": "#F47245"}


def col(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def tw(text, fk, size):
    return F[fk].text_length(text, size)


def put(page, x, y, text, fk, size, color, align="l"):
    if align == "c":
        x -= tw(text, fk, size) / 2
    elif align == "r":
        x -= tw(text, fk, size)
    page.insert_text((x, y), text, fontname=fk, fontsize=size, color=col(color))


def parse_rich(text, fk_reg, fk_bold):
    segs = []
    for m in re.split(r"(<b>.*?</b>)", text):
        if not m:
            continue
        if m.startswith("<b>"):
            segs.append((m[3:-4], fk_bold))
        else:
            segs.append((m, fk_reg))
    return segs


REG = {}  # registro de reducciones aplicadas (0 = cupo justo, <0 = hubo que reducir)


def wrap_lines(segs, size, maxw):
    words = []
    for t, fk in segs:
        for w in t.split(" "):
            if w:
                words.append((w, fk))
    lines, cur, curw = [], [], 0.0
    for w, fk in words:
        ww = tw(w, fk, size)
        sp = tw(" ", cur[-1][1], size) if cur else 0.0
        if cur and curw + sp + ww > maxw:
            lines.append(cur); cur = [(w, fk)]; curw = ww
        else:
            curw += sp; cur.append((w, fk)); curw += ww
    if cur:
        lines.append(cur)
    return lines


def fit_rich(segs, base, min_size, maxw, max_lines, key):
    """Baja el tamano de a 0.5 pt hasta que el texto entre en max_lines."""
    s = base
    while s > min_size and len(wrap_lines(segs, s, maxw)) > max_lines:
        s -= 0.5
    if key:
        REG[key] = round(s - base, 2)
    return s


def fit_cruce(msgs, base, floor, maxw, start, gap, lh, limit):
    """Tamano UNICO para todo el cruce: ninguna linea ('baseline') debe pasar
    de `limit` (borde inferior de la tarjeta) y el bloque arranca en `start`."""
    s = base
    while s > floor:
        y, ok = start, True
        for seg in msgs:
            n = len(wrap_lines(seg, s, maxw))
            if y > limit:
                ok = False
                break
            y += (n - 1) * lh + gap
        if ok and (y - gap) <= limit:
            return s
        s -= 0.5
    return floor


def fit_fill(msgs, floor, ceil, maxw, start, limit, ratio=1.30):
    """Tamano dinamico para llenar el contenedor: el mayor (hasta `ceil`) que
    hace que todo el bloque entre en [start, limit]; si ni con `floor` entra,
    devuelve `floor`. Devuelve (tamano, interlineado)."""
    s = ceil
    while s > floor:
        lh = round(ratio * s, 2)
        y, ok = start, True
        for seg in msgs:
            if y > limit:
                ok = False
                break
            y += (len(wrap_lines(seg, s, maxw)) - 1) * lh + lh
        if ok and (y - lh) <= limit:
            return s, lh
        s -= 0.5
    return floor, round(ratio * floor, 2)


def fit_block(msgs, floor, ceil, maxw, start, limit, ratio=1.30):
    """Mayor prefijo de `msgs` que entra en [start, limit], con el tamano mas
    grande posible en [floor, ceil] e interlineado proporcional. Garantiza que
    el texto NUNCA cruce el borde de la tarjeta (recorta parrafos si hiciera
    falta, empezando por el final). Devuelve (parrafos, tamano, interlineado)."""
    for n in range(len(msgs), 0, -1):
        s = ceil
        while s >= floor:
            lh = round(ratio * s, 2)
            y = start
            for seg in msgs[:n]:
                y += (len(wrap_lines(seg, s, maxw)) - 1) * lh + lh
            if (y - lh) <= limit:
                return msgs[:n], s, lh
            s -= 0.5
    return msgs[:1], floor, round(ratio * floor, 2)


def put_rich(page, x, y0, size, lh, segs, color, maxw):
    lines = wrap_lines(segs, size, maxw)
    for i, line in enumerate(lines):
        cx = x
        for j, (w, fk) in enumerate(line):
            if j:
                cx += tw(" ", line[j - 1][1], size)
            page.insert_text((cx, y0 + i * lh), w, fontname=fk, fontsize=size, color=col(color))
            cx += tw(w, fk, size)
    return y0 + (len(lines) - 1) * lh


def rrect(page, r, fill, rpt):
    """rpt = radio en puntos; PyMuPDF espera fraccion del lado menor."""
    frac = max(0.0, min(0.5, rpt / max(0.1, min(r.width, r.height))))
    page.draw_rect(r, color=None, fill=col(fill), radius=frac)


def chips(page, items, x0, y0, maxr, fk="nun", size=10.0):
    h, pad, gap, rgap = 14.5, 4.0, 8.9, 20.5
    x, y = x0, y0
    for t in items:
        w = tw(t, fk, size) + pad * 2
        if x + w > maxr:
            x = x0; y += rgap
        rrect(page, fitz.Rect(x, y, x + w, y + h), GRIS, 3)
        put(page, x + pad, y + 10.29, t, fk, size, "#000000")
        x += w + gap
    return y


def bar(page, x0, y0, w, h, pct, fillcol):
    rrect(page, fitz.Rect(x0, y0, x0 + w, y0 + h), TRACK, h / 2)
    fw = max(0.0, w * max(0.0, min(1.0, pct)))
    if fw > 1:
        rrect(page, fitz.Rect(x0, y0, x0 + max(fw, h), y0 + h), fillcol, h / 2)


def dot(page, x0, y0, color):
    """Circulo de avance: borra el cuadro de la plantilla y dibuja un circulo real."""
    page.draw_rect(fitz.Rect(x0 - 0.6, y0 - 0.6, x0 + 12.7, y0 + 12.7),
                   color=None, fill=(1, 1, 1))
    page.draw_circle(fitz.Point(x0 + 6.05, y0 + 6.05), 6.05, color=None, fill=col(color))


def flecha(page, y0, up, color):
    """Triangulo de cambio (como el ejemplo): arriba=Mejoro, abajo=Cambio."""
    x0, x1, cx = 525.81, 543.82, 534.82
    y0, y1 = y0 + 0.30, y0 + 9.25
    pts = [(cx, y0), (x0, y1), (x1, y1)] if up else [(x0, y0), (x1, y0), (cx, y1)]
    page.draw_polyline(pts, color=None, fill=col(color), closePath=True)


def fit_line(text, fk, size, maxw, drop=("con", "de", "del", "y", "e", "o", "u", "para", "en", "a", "por", "sin", "que", "la", "el", "los", "las", "un", "una", "al")):
    """Recorta a UNA linea: la barra de la plantilla no debe tapar texto."""
    if tw(text, fk, size) <= maxw:
        return text
    ws = text.split()
    while ws:
        ws.pop()
        while ws and ws[-1].strip(".,;:").lower() in drop:
            ws.pop()
        cand = " ".join(ws).rstrip(".,;:") + "."
        if tw(cand, fk, size) <= maxw:
            return cand
    return text


def build(e):
    REG.clear()
    ctx = G.construir(e)
    doc = fitz.open(TPL)
    p1, p2, p3 = doc[0], doc[1], doc[2]

    # Plantilla NUEVA (06-oct-2026): el cruce ya viene ampliado en el diseño y
    # "Próximos pasos" quedó compacto (pestaña a la izquierda + 4 pasos a la
    # derecha, texto real). Ya no hay nada que redactar ni rectángulo blanco.

    for pg in doc:
        for k in FF:
            pg.insert_font(fontname=k, fontfile=FF[k])

    nome = ctx["est"]
    tops = ctx["tops"][:3]

    # ---------- P1 ----------
    put(p1, 41.74, 99.99, nome, "osb", 13, "#000000")
    acad, cp, ie = CPIE.get(e.get("clave"), ("", "", ""))
    partes = [ctx["ie"]]
    if cp:
        partes.append(f"CP: {tit(cp)}")
    if ie:
        partes.append(f"IE: IE {tit(ie)}")
    partes.append(f'{ORD.get(ctx["grado"], ctx["grado"])} grado Secundaria')
    meta = " - ".join(partes)
    ms = 11
    while ms > 8 and tw(meta, "osr", ms) > 505:
        ms -= 0.5
    REG["cabecera"] = round(ms - 11, 2)
    put(p1, 44.60, 115.75, meta, "osr", ms, "#000000")

    CX = [121.45, 297.75, 476.0]
    # Orden visual del ejemplo: la 1.ª afinidad va al CENTRO, la 2.ª a la IZQUIERDA y la 3.ª a la DERECHA
    tops = [tops[1], tops[0], tops[2]] if len(tops) == 3 else tops
    for i, t in enumerate(tops):
        if i > 2:
            break
        nm = DISPLAY.get(t["area"], t["area"])
        put(p1, CX[i], 289.01, nm, "gb", 12, "#000000", align="c")
        put(p1, CX[i], 304.32, f'Puntaje {int(round(t["valor"]))}/5 - {t["nivel"]}', "gr", 9, "#000000", align="c")

    segs = parse_rich(ctx["narrativa"], "osr", "osb")
    ns = fit_rich(segs, 10, 7.5, 516.2, 4, "narrativa")
    put_rich(p1, 39.78, 364.85, ns, 13.51, segs, "#000000", 516.2)

    BLQ_Y = [576.23, 617.02, 657.81, 698.60, 739.39, 780.18]
    DOT_X = [485.3, 499.5, 513.8, 528.0, 542.3]   # las 5 columnas de la plantilla
    DOT_Y = [561.1, 601.9, 642.7, 683.5, 724.2, 765.0]
    IND = tw(" " * 14, "osr", 9)  # misma sangria que el ejemplo: el texto no pisa los iconos
    for i, b in enumerate(ctx["bloques"]):
        segb = [(b["texto"], "osr")]
        bs = fit_rich(segb, 9, 7.0, 400, 1, f"bloque{i + 1}")
        put_rich(p1, 42.57 + IND, BLQ_Y[i], bs, 11.0, segb, "#000000", 400)
        n_dots = min(5, max(1, int(round(b["pintar"]))))
        dc = VERDE if b["color"] == "#15803D" else NARANJA
        for s in range(5):
            dot(p1, DOT_X[s], DOT_Y[i], dc if s < n_dots else GRIS)

    chips(p1, ctx["fortalezas"], 47.7, 462.9, 535.6)

    # ---------- P2 ----------
    AREA_Y = [103.32, 177.42, 251.51]
    CHIP_Y = [113.9, 187.2, 262.9]
    for i, t in enumerate(tops):
        if i > 2:
            break
        put(p2, 73.36, AREA_Y[i], DISPLAY.get(t["area"], t["area"]), "gb", 12, "#000000")
        put(p2, 186.41, AREA_Y[i] + 1.2, f'¿dónde estudiar?: {t["donde"]}', "gr", 9, "#000000")
        chips(p2, t["carreras"], 43.7, CHIP_Y[i], 552.4)

    NOMB_Y = [452.51, 526.37, 600.24, 674.11]
    DESC_Y = [468.07, 541.94, 615.81, 689.68]
    PUNT_Y = [496.19, 570.06, 643.93, 717.80]
    PILL_Y = [439.5, 513.3, 587.2, 661.1]
    BARY = [478.2, 552.1, 626.0, 699.8]
    DELY = [451.1, 524.9, 598.7, 672.6]
    DELT_Y = [474.47, 548.34, 622.21, 696.08]
    for i, d in enumerate(ctx["hse_dims"]):
        # la plantilla ya trae el nombre de la habilidad: no se reescribe
        p2.draw_rect(fitz.Rect(94.5, DESC_Y[i] - 11.5, 462, DESC_Y[i] + 4.5), color=None, fill=col("#FFFFFF"))
        put(p2, 94.92, DESC_Y[i], fit_line(d["desc"], "gr", 11, 356), "gr", 11, "#000000")
        p2.draw_rect(fitz.Rect(96, PUNT_Y[i] - 11.5, 178, PUNT_Y[i] + 4.5), color=None, fill=col("#FFFFFF"))
        put(p2, 96.87, PUNT_Y[i], f'Puntaje: {d["valor"]}/{d["max"]}', "gr", 9, "#000000")
        pillc = PILL_HSE.get(d["nivel"], VERDE_T)
        pw = tw(d["nivel"], "gr", 10) + 8
        rrect(p2, fitz.Rect(311.8, PILL_Y[i], 311.8 + pw, PILL_Y[i] + 16), pillc, 4)
        put(p2, 315.8, PILL_Y[i] + 10.98, d["nivel"], "gr", 10, "#FFFFFF", align="l")
        bar(p2, 94.3, BARY[i], 456.1, 9.1, d["valor"] / d["max"], VERDE)
        up = (d["delta"] or 0) > 0
        dc = "#9E968C" if d["delta"] == 0 else (TEAL if up else TERRA)
        flecha(p2, DELY[i], up or d["delta"] == 0, dc)
        txt, tc = ("Mejoró", VERDE_T) if up else ("Cambió", TERRA)
        if d["delta"] == 0:
            txt, tc = "Igual", "#9E968C"
        put(p2, 547.61, DELT_Y[i], txt, "gb", 12, tc, align="r")

    ht = ctx["hse_total"]
    if ht and ctx["hse_dims"]:
        put_rich(p2, 57.47, 759.19, 9, 11,
                 [("Nivel socioemocional general ", "osr"), (f'({ht["nivel"]})', "osb"),
                  (" · todas las habilidades cuentan: crecer en una ayuda a las demás.", "osr")],
                 "#000000", 520)
        put(p2, 271.33, 775.74, f'{ht["valor"]} /', "gb", 12, "#000000", align="r")
        put(p2, 274.34, 774.99, f'{ht["max"]}', "gr", 10, "#000000")
    else:
        # Estudiantes sin resultados socioemocionales: se avisa en la tarjeta.
        put(p2, 94.3, 450.0, "Información no disponible", "gr", 11, "#000000")
        put(p2, 57.47, 759.19, "Nivel socioemocional general: Información no disponible.",
            "osr", 9, "#000000")

    # ---------- P3 ----------
    # Plantilla NUEVA (06-oct-2026): todo el bloque academico de la pag. 3
    # subio 33.6 pt (los paneles PRONABEC y sus filas). Las x no cambiaron.
    P3_TIT_Y = [124.08, 340.86]
    P3_PILL_Y = [109.9, 327.7]
    P3_CORR_Y = [123.33, 340.10]
    P3_BARY = [132.6, 349.4]
    P3_CONS_Y = [247.48, 464.25]
    LIM_CONS = [299.0, 518.0]  # borde inferior UTIL de cada tarjeta (real: 303.4 / 522.9)
    NAME_L = [[163.52, 187.75, 211.69], [380.29, 404.52, 428.46]]
    NAME_R = [[163.52, 187.75], [380.29, 404.52]]
    SC_L = [[163.85, 188.09, 212.02], [380.63, 404.86, 428.80]]
    SC_R = [[163.85, 188.09], [380.63, 404.86]]
    TB_L = [[156.4, 180.7, 204.6], [373.2, 397.5, 421.4]]
    TB_R = [[156.4, 180.7], [373.2, 397.5]]
    SLOTS = [[("texto literario", 0, 0), ("texto expositivo", 1, 0), ("texto argumentativo", 0, 1),
              ("infografía", 1, 1), ("texto instructivo", 0, 2)],
             [("estadística", 0, 0), ("probabilidad", 1, 0), ("geometría", 0, 1),
              ("aritmética", 1, 1), ("álgebra", 0, 2)]]
    BX = [173.4, 431.6]
    SX = [284.0, 544.0]

    for k in (0, 1):
        if k >= len(ctx["acad"]):
            # Sin resultados academicos (PRONABEC): se avisa en la seccion.
            put(p3, 45.37, P3_CONS_Y[k], "Información no disponible", "gr", 9, "#000000")
            continue
        ac = ctx["acad"][k]
        filas = {f["hab"].strip().lower(): f for f in ac["filas"]}
        niv_disp = ac.get("nivel3") or ac["nivel"]
        ncol = NIVEL3_COLOR.get(niv_disp, VERDE)
        pw = tw(niv_disp, "gr", 10) + 8
        rrect(p3, fitz.Rect(551.9 - pw, P3_PILL_Y[k], 551.9, P3_PILL_Y[k] + 16), ncol, 4)
        put(p3, 547.9, P3_PILL_Y[k] + 10.98, niv_disp, "gr", 10, "#FFFFFF", align="r")
        put(p3, 251.35, P3_CORR_Y[k], f'{ac["correctas"]}/{ac["total"]} Correctas', "gr", 9, "#000000")
        bar(p3, 69.7, P3_BARY[k], 456.1, 9.1, ac["correctas"] / ac["total"], CELESTE)
        for hab, cidx, ridx in SLOTS[k]:
            f = filas.get(hab)
            if not f:
                continue
            nb = (NAME_L if cidx == 0 else NAME_R)[k][ridx]
            sb = (SC_L if cidx == 0 else SC_R)[k][ridx]
            tb = (TB_L if cidx == 0 else TB_R)[k][ridx]
            put(p3, SX[cidx], sb, f'{f["c"]}/{f["t"]}', "gr", 9, "#000000", align="r")
            bar(p3, BX[cidx], tb, 88.1, 8.9, f["c"] / max(1, f["t"]), CELESTE2)
        msgsA, csA, lhA = fit_block(
            [parse_rich(p, "gr", "gb") for p in ac["seccion"]], 6.5, 9.0, 510,
            P3_CONS_Y[k], LIM_CONS[k])
        REG[f"consejo{k + 1}"] = round(csA - 9, 2)
        y = P3_CONS_Y[k]
        for segc in msgsA:
            ly = put_rich(p3, 45.37, y, csA, lhA, segc, "#000000", 510)
            y = ly + lhA

    # Cruce: se escribe dentro de la tarjeta que la plantilla ya trae ampliada
    # (x 74.7-558.3, y 541.1-715.8, título horneado en 545-560). No se redibuja
    # borde ni fondo ni título.
    CRUCE_X = 81.7
    CRUCE_Y, CRUCE_LIM = 573.0, 706.0
    msgsC = [([("• ", "osr")] + parse_rich(m["texto"], "osr", "osb"))
             for m in ctx["cruce"]["mensajes"]]
    if ctx["cruce"].get("sintesis"):
        msgsC.append([("• ", "osr")] + parse_rich(ctx["cruce"]["sintesis"], "osr", "osb"))
    cs, lhc = fit_fill(msgsC, 6.0, 10.5, 462, CRUCE_Y, CRUCE_LIM)
    REG["cruce"] = round(cs - 9, 2)
    y = CRUCE_Y
    for j, segm in enumerate(msgsC):
        ly = put_rich(p3, CRUCE_X, y, cs, lhc, segm, "#000000", 462)
        y = ly + lhc

    return doc, ctx


def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def main():
    q = " ".join(sys.argv[1:]).upper() or "OBREGON VERAMENDI"
    data = json.load(open(BASE_AJ + "/datos_integrados_ancash.json", encoding="utf-8"))
    sel = [x for x in data if q in (x.get("estudiante") or "").upper()]
    if not sel:
        print("no encontrado"); return
    e = sel[0]
    doc, ctx = build(e)
    out = f'{OUTDIR}/Muestra_AJ_{slug(e["estudiante"])}.pdf'
    doc.save(out)
    print("OK", out, os.path.getsize(out))


if __name__ == "__main__":
    main()
