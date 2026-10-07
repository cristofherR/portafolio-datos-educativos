# -*- coding: utf-8 -*-
"""
Consejos académicos y cruce TOV<->académico — Academia Juvenil Áncash 2026.
Explica, en lenguaje de estudiante, QUÉ falló por tema y QUÉ reforzar según su área vocacional.
"""

# ---- Habilidades -> consejo accionable (lenguaje amigable) ----
HAB_CONSEJO = {
    # Matemática
    "Aritmética": "Practica operaciones, fracciones, porcentajes y proporciones. Es la base de casi todo cálculo.",
    "Álgebra": "Refuerza ecuaciones, expresiones y funciones. Es clave para ingeniería, economía y datos.",
    "Geometría": "Repasa figuras, áreas, volúmenes y ángulos con ejercicios visuales y dibujos.",
    "Estadística": "Aprende a leer tablas, gráficos y promedios. Sirve en casi todas las carreras.",
    "Estadística y probabilidad": "Combina lectura de datos y situaciones de azar; base para analizar información.",
    "Probabilidad": "Practica situaciones de azar y conteo. Aparece en salud, negocios y ciencia.",
    "Lógico-matemático": "Entrena acertijos, secuencias y patrones lógicos, poco a poco y sin apuro.",
    "Patrones y sucesiones": "Busca regularidades en números y figuras; fortalece el razonamiento.",
    "Razonamiento espacial": "Practica ver figuras en 2D y 3D: plegado, rotación y volumen.",
    # Comunicación
    "Texto literario": "Lee cuentos y poemas, y pregúntate qué quiso decir el autor y cómo lo logró.",
    "Texto informativo": "Identifica la idea principal y los detalles en noticias y textos escolares.",
    "Texto argumentativo": "Aprende a reconocer tesis, argumentos y conclusiones. Clave para derecho, comunicación y liderazgo.",
    "Texto expositivo": "Practica resumir y ordenar la información de un texto en tus propias palabras.",
    "Texto instructivo": "Lee procedimientos y recetas siguiendo el orden de los pasos; ayuda a la comprensión.",
    "Infografía": "Combina texto, íconos y gráficos: practica leer datos presentados en imágenes.",
}

# ---- Qué temas conviene reforzar según el área vocacional ----
AREA_CLAVE = {
    "Ciencias": ["Aritmética", "Estadística", "Estadística y probabilidad", "Texto informativo", "Texto expositivo"],
    "Numérica": ["Aritmética", "Álgebra", "Estadística", "Probabilidad", "Estadística y probabilidad"],
    "Ingeniería": ["Álgebra", "Geometría", "Aritmética", "Razonamiento espacial"],
    "Artística": ["Texto literario", "Texto argumentativo"],
    "Social": ["Texto argumentativo", "Texto informativo", "Texto literario"],
    "Emprendedora": ["Aritmética", "Estadística", "Texto argumentativo"],
    "Salud": ["Aritmética", "Estadística", "Probabilidad", "Texto informativo"],
    "Gastronómica": ["Aritmética", "Texto instructivo"],
    "Estética": ["Texto instructivo", "Aritmética"],
    "Deportiva": ["Texto informativo", "Aritmética"],
    "Seguridad, defensa y orden público": ["Texto informativo", "Aritmética", "Razonamiento espacial"],
    "Aeronáutica y servicios de vuelo": ["Aritmética", "Geometría", "Razonamiento espacial"],
}

NOMBRE_PRUEBA = {
    "pronabec_com": "PRONABEC · Comunicación",
    "pronabec_mat": "PRONABEC · Matemática",
    "coar": "COAR",
}

def nivel_pct(pct):
    if pct >= 70: return ("Alto", "#15803D")
    if pct >= 50: return ("Medio", "#D97706")
    if pct >= 30: return ("En proceso", "#B45309")
    return ("Inicial", "#B91C1C")

def _pct(c, t):
    return round(100.0 * c / t) if t else 0

def nivel_pct3(pct):
    """Semáforo académico de 3 estados (fiel a categoria_pct del proyecto)."""
    if pct >= 70: return ("Tercio superior", "#166534")
    if pct >= 40: return ("En proceso", "#FF834D")
    return ("En inicio", "#ED1C24")

def _seccion(d):
    """Párrafos de la sección 'Para mejorar en PRONABEC ...'
    (máx. 4, para que quepan en la tarjeta)."""
    p = []
    if d["mejorar"]:
        for f in d["mejorar"][:3]:
            p.append(f"• <b>{f['hab']} —</b> {f['consejo']}")
        for f in d["impulso"]:
            if len(p) >= 3:
                break
            p.append(f"• Un pequeño impulso en <b>{f['hab']}</b> ({f['c']}/{f['t']}): {f['consejo']}")
        p.append("• Con práctica diaria, aunque sea 20 minutos, vas a cerrar esas brechas.")
    else:
        p.append("¡Felicitaciones! No hay temas por reforzar: dominas lo que evalúa esta prueba.")
        if d["fortalece"]:
            fts = ", ".join(f"<b>{f['hab']}</b> ({f['c']}/{f['t']})" for f in d["fortalece"][:2])
            p.append(f"• Tus puntos más fuertes: {fts}.")
        for f in d["impulso"][:2]:
            p.append(f"• Un pequeño impulso en <b>{f['hab']}</b> ({f['c']}/{f['t']}): {f['consejo']}")
        if not d["impulso"]:
            p.append("• Las dominas todas: mantén ese ritmo con un repaso constante.")
    return p[:4]

def detalle_prueba(prueba, label):
    """Devuelve filas por habilidad ordenadas de más débil a más fuerte."""
    hab = prueba.get("hab", {})
    filas = []
    for h, v in hab.items():
        if not v.get("t"): continue
        p = _pct(v["c"], v["t"])
        filas.append({
            "hab": h, "c": v["c"], "t": v["t"], "pct": p,
            "nivel": nivel_pct(p)[0], "color": nivel_pct(p)[1],
            "consejo": HAB_CONSEJO.get(h, "Practica este tema con ejercicios y repaso constante."),
        })
    filas.sort(key=lambda x: (x["pct"], -x["t"]))
    ok = [f for f in filas if f["pct"] >= 60]
    mej = [f for f in filas if f["pct"] < 60]
    pct_tot = _pct(prueba.get("correctas", 0), prueba.get("total", 0))
    d = {
        "label": label,
        "correctas": prueba.get("correctas", 0), "total": prueba.get("total", 0),
        "pct": pct_tot, "nivel": nivel_pct(pct_tot)[0], "color": nivel_pct(pct_tot)[1],
        "filas": filas, "mejorar": mej[:3], "fortalece": ok[::-1][:3],
    }
    d["nivel3"] = nivel_pct3(pct_tot)[0]
    d["impulso"] = [f for f in filas if 60 <= f["pct"] < 100][:2]
    d["seccion"] = _seccion(d)
    return d

def pruebas_estudiante(e):
    out = []
    for k in ("coar", "pronabec_mat", "pronabec_com"):
        if e.get(k):
            out.append(detalle_prueba(e[k], NOMBRE_PRUEBA[k]))
    out.sort(key=lambda x: -x["pct"])
    return out

# ---- Cruce TOV <-> HSE: qué exige cada área en lo socioemocional ----
DIM_DISPLAY = {"Asertividad": "Asertividad", "Comunicacion": "Comunicación",
               "Autoestima": "Autoestima", "TomaDecisiones": "Toma de decisiones"}
HSE_DEBIL = {"MUY BAJO", "BAJO", "PROMEDIO BAJO", "PROMEDIO"}
HSE_MEDIO = {"PROMEDIO ALTO"}
HSE_FUERTE = {"ALTO", "MUY ALTO"}

# área TOV -> (dimensiones HSE que esa área exige, por qué en una frase)
AREA_HSE = {
    "Ciencias": (["Comunicacion", "Autoestima"], "exige curiosidad, constancia y comunicar lo que descubres"),
    "Numérica": (["TomaDecisiones", "Autoestima"], "exige orden, confianza en ti y decidir con criterio"),
    "Ingeniería": (["TomaDecisiones", "Comunicacion"], "se trabaja en equipo y se decide sobre problemas reales"),
    "Artística": (["Comunicacion", "Autoestima"], "exige expresar, exponerte y confiar en tu voz"),
    "Social": (["Comunicacion", "Asertividad"], "exige escuchar, comunicar y defender ideas con respeto"),
    "Emprendedora": (["Asertividad", "TomaDecisiones"], "exige iniciativa, negociar y decidir asumiendo riesgo"),
    "Salud": (["Comunicacion", "TomaDecisiones"], "exige trato con personas y decisiones responsables"),
    "Gastronómica": (["Asertividad", "TomaDecisiones"], "exige trabajar bajo presión, en equipo y con servicio"),
    "Estética": (["Comunicacion", "Asertividad"], "exige trato con clientes y proponer con seguridad"),
    "Deportiva": (["Comunicacion", "TomaDecisiones"], "exige trabajo en equipo, constancia y decidir bajo presión"),
    "Seguridad, defensa y orden público": (["Asertividad", "TomaDecisiones"], "exige disciplina, valor y decidir en situaciones difíciles"),
    "Aeronáutica y servicios de vuelo": (["TomaDecisiones", "Autoestima"], "exige serenidad, precisión y responsabilidad"),
}

AVANZAR = ("Conversa con alguien que trabaje en tus áreas y busca tus carreras en Ponte en Carrera; "
           "practica lectura y matemática 20 minutos al día.")

CORTO = {"pronabec_com": "Comunicación", "pronabec_mat": "Matemática", "coar": "COAR"}
MOTIV = "Con constancia y las oportunidades correctas, este perfil puede convertirse en tu proyecto de vida."

# Lenguaje claro para el estudiante (reemplaza terminos tecnicos en el cierre del cruce).
DIM_FRASE = {"Asertividad": "poner límites con respeto", "Comunicacion": "comunicarte mejor",
             "Autoestima": "confiar más en ti", "TomaDecisiones": "decidir con más seguridad"}
ACAD_SKILL = {NOMBRE_PRUEBA["pronabec_com"]: "leer y comprender textos",
              NOMBRE_PRUEBA["pronabec_mat"]: "resolver problemas con números",
              NOMBRE_PRUEBA["coar"]: "las pruebas del COAR"}
ACAD_NOMBRE = {NOMBRE_PRUEBA["pronabec_com"]: "comunicación",
               NOMBRE_PRUEBA["pronabec_mat"]: "matemática",
               NOMBRE_PRUEBA["coar"]: "las pruebas COAR"}


def _lista(items):
    """Une en lenguaje natural: A, B y C (nunca 'A y B y C')."""
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " y " + items[-1]


def _hse_resumen(niveles):
    if not niveles:
        return ""
    deb = [DIM_FRASE[d] for d in DIM_DISPLAY if niveles.get(d) in HSE_DEBIL]
    if deb:
        return ("En tu forma de relacionarte y tomar decisiones, lo que más puedes entrenar es "
                + _lista(deb) + ".")
    med = [DIM_FRASE[d] for d in DIM_DISPLAY if niveles.get(d) == "PROMEDIO ALTO"]
    if med:
        return ("En tu forma de relacionarte y tomar decisiones vas bien; puedes afinar "
                + _lista(med) + ".")
    return "En tu forma de relacionarte y tomar decisiones, tus habilidades se ven sólidas."


def _sintesis(e, pruebas, niveles):
    """Cierre del cruce: TOV + HSE + academico en lenguaje claro para el estudiante."""
    partes = ["<b>En pocas palabras:</b>"]
    ta = list(e.get("tops") or [])[:2]
    if ta:
        partes.append(f"te atrae {ta[0]}." if len(ta) == 1 else f"te atraen {_lista(ta)}.")
    hr = _hse_resumen(niveles)
    if hr:
        partes.append(hr)
    if pruebas:
        mejor = max(pruebas, key=lambda p: p["pct"])
        peor = min(pruebas, key=lambda p: p["pct"])
        skill = ACAD_SKILL.get(mejor["label"], CORTO.get(mejor["label"], mejor["label"]))
        if mejor["label"] == peor["label"]:
            partes.append(f"En tus pruebas, {skill} es tu punto más fuerte, "
                          f"y también donde más puedes crecer.")
        else:
            nombre = ACAD_NOMBRE.get(peor["label"], CORTO.get(peor["label"], peor["label"]))
            partes.append(f"En tus pruebas, tu punto más fuerte es {skill}; en {nombre} todavía "
                          f"tienes camino por recorrer: con práctica puede subir.")
    else:
        partes.append("Todavía no contamos con tus pruebas académicas.")
    partes.append(MOTIV)
    return " ".join(partes)


def _txt_hse(niveles, dims):
    if not niveles or not dims:
        return ""
    debiles = [DIM_DISPLAY[d] for d in dims if niveles.get(d) in HSE_DEBIL]
    medios = [DIM_DISPLAY[d] for d in dims if niveles.get(d) in HSE_MEDIO]
    fuertes = [DIM_DISPLAY[d] for d in dims if niveles.get(d) in HSE_FUERTE]
    if debiles:
        return "en lo socioemocional, refuerza " + " y ".join(debiles) + " (van en proceso)"
    if medios and not fuertes:
        return "en lo socioemocional, sigue afinando " + " y ".join(medios)
    if fuertes and all(niveles.get(d) in HSE_FUERTE for d in dims):
        return "en lo socioemocional ya cuentas con " + " y ".join(fuertes)
    return "en lo socioemocional, trabaja " + " y ".join(DIM_DISPLAY[d] for d in dims)


def _txt_acad(idx, area, hay_pruebas):
    if not hay_pruebas:
        return "aún no tenemos tus pruebas académicas: refuerza lectura y matemática, base de cualquier área"
    debiles, faltan = [], []
    for h in AREA_CLAVE.get(area, []):
        if h in idx:
            c, t = idx[h]
            if t and (c / t) < 0.6:
                debiles.append(f"{h.lower()} ({c}/{t})")
        else:
            faltan.append(h)
    if debiles:
        return "en lo académico, refuerza " + ", ".join(debiles)
    if faltan:
        return ("en lo académico, tu prueba no midió " +
                ", ".join("«" + h.lower() + "»" for h in faltan) + ", conviene trabajarlo igual")
    return "en lo académico vas bien en los temas que esa área pide"


def cruce(e, tops):
    """Cruce de 2 áreas top: área TOV + HSE + académico (con escalera de ausencia)."""
    pruebas = pruebas_estudiante(e)
    idx = {}
    for p in pruebas:
        for f in p["filas"]:
            if f["hab"] not in idx:
                idx[f["hab"]] = (f["c"], f["t"])
    niveles = (e.get("hse_proceso") or {}).get("niveles", {}) or {}
    mensajes = []
    for area in tops[:2]:
        dims, porque = AREA_HSE.get(area, ([], ""))
        partes = [p for p in (_txt_hse(niveles, dims), _txt_acad(idx, area, bool(pruebas))) if p]
        mensajes.append({"area": area, "texto": f"<b>{area}</b> — {porque}: " + "; ".join(partes) + "."})
    return {"mensajes": mensajes, "pruebas": pruebas, "avanzar": AVANZAR,
            "sintesis": _sintesis(e, pruebas, niveles)}
