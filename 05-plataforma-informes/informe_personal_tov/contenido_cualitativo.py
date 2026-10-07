# -*- coding: utf-8 -*-
"""
Contenido cualitativo TOV — Academia Juvenil Áncash 2026
Texto en español neutro, dirigido a estudiantes (14–17 años).
Carreras del Perú (base de conocimiento; verificar en vivo con Ponte en Carrera si se requiere).
"""

ICONO = {
    "Ciencias": "🔬",
    "Numérica": "🔢",
    "Ingeniería": "⚙️",
    "Artística": "🎨",
    "Social": "🤝",
    "Emprendedora": "💼",
    "Salud": "🩺",
    "Gastronómica": "🍳",
    "Estética": "💅",
    "Deportiva": "🏅",
    "Seguridad, defensa y orden público": "🛡️",
    "Aeronáutica y servicios de vuelo": "✈️",
}

COLOR = {
    "Ciencias": "#1B7F79",
    "Numérica": "#2E5FA3",
    "Ingeniería": "#3A6073",
    "Artística": "#B23A8F",
    "Social": "#D97706",
    "Emprendedora": "#0F766E",
    "Salud": "#C0392B",
    "Gastronómica": "#B45309",
    "Estética": "#BE185D",
    "Deportiva": "#15803D",
    "Seguridad, defensa y orden público": "#334155",
    "Aeronáutica y servicios de vuelo": "#1E40AF",
}

# Contenido por área
AREAS = {
    "Ciencias": {
        "desc": "Si te gusta hacerte preguntas y entender cómo funcionan la vida, la naturaleza y el mundo que te rodea, esta es tu área. Aquí encajan quienes disfrutan observar, experimentar y descubrir el «por qué» de las cosas.",
        "evalua": "Tu interés por la investigación, la biología, la química y la física: entender la naturaleza con método y evidencia.",
        "carreras": ["Biología", "Química", "Física", "Biotecnología", "Ciencias Ambientales", "Geología", "Ingeniería Ambiental", "Bioquímica", "Meteorología"],
        "donde": "UNMSM, UNI, UNALM, PUCP, UNASAM",
        "campos": "Laboratorios, institutos de investigación, universidades, empresas ambientales y mineras.",
        "fortalezas": ["Curiosidad", "Pensamiento crítico", "Paciencia", "Rigor", "Análisis"],
        "frase": "Tu curiosidad puede convertirse en descubrimientos que ayuden a tu comunidad.",
    },
    "Numérica": {
        "desc": "Si los números, los cálculos y los acertijos de lógica no te asustan —y hasta te divierten—, aquí tienes ventaja. Es el área de quienes piensan con orden, patrones y precisión.",
        "evalua": "Tu afinidad con las matemáticas, el cálculo, la estadística y el razonamiento lógico.",
        "carreras": ["Matemática", "Estadística", "Economía", "Contabilidad", "Administración", "Ingeniería (todas)", "Ciencias de la Computación", "Finanzas", "Actuaría"],
        "donde": "UNI, UNMSM, PUCP, UNAC, U. del Pacífico, UNASAM",
        "campos": "Banca y finanzas, consultoría, análisis de datos, contabilidad, investigación.",
        "fortalezas": ["Lógica", "Orden", "Precisión", "Concentración", "Resolución de problemas"],
        "frase": "Los números son un idioma: quien lo domina, resuelve más rápido.",
    },
    "Ingeniería": {
        "desc": "Si te gusta armar, desarmar, construir o imaginar cómo mejorar máquinas, edificios o sistemas, esta área es para ti. Aquí se piensa en soluciones concretas a problemas reales.",
        "evalua": "Tu interés por diseñar, construir y aplicar la tecnología para resolver problemas prácticos.",
        "carreras": ["Ingeniería Civil", "Mecánica", "Mecatrónica", "Eléctrica", "Electrónica", "Industrial", "de Sistemas", "de Minas", "Agroindustrial"],
        "donde": "UNI, UNASAM, PUCP, UNT · Institutos: SENATI, TECSUP",
        "campos": "Construcción, minería, manufactura, energía, tecnología, transporte y agroindustria.",
        "fortalezas": ["Creatividad técnica", "Pensamiento práctico", "Trabajo en equipo", "Disciplina"],
        "frase": "Todo lo que se construye nació de alguien que se atrevió a diseñarlo.",
    },
    "Artística": {
        "desc": "Si te expresas con el dibujo, la música, la danza, el teatro o las palabras, y sientes que crear es tu forma de decir cosas, esta área te representa.",
        "evalua": "Tu interés por la expresión creativa y artística en sus distintas formas.",
        "carreras": ["Arte", "Diseño Gráfico", "Música", "Teatro / Artes Escénicas", "Danza", "Comunicación Audiovisual", "Animación Digital", "Literatura", "Diseño de Interiores"],
        "donde": "PUCP, ENSABAP (Bellas Artes), ESFAP, USIL, UPC",
        "campos": "Estudios creativos, medios, publicidad, cultura, educación artística y producción audiovisual.",
        "fortalezas": ["Imaginación", "Sensibilidad", "Comunicación", "Originalidad", "Disciplina creativa"],
        "frase": "Tu forma de crear también es una manera de pensar.",
    },
    "Social": {
        "desc": "Si te nace ayudar a los demás, escuchar, mediar y trabajar con personas, esta área es para ti. Aquí se construye con empatía y compromiso.",
        "evalua": "Tu interés por lo social, la comunicación, la justicia y el servicio a las personas.",
        "carreras": ["Derecho", "Psicología", "Educación", "Sociología", "Comunicación Social", "Trabajo Social", "Ciencia Política", "Antropología"],
        "donde": "PUCP, UNMSM, UNASAM, UNT, UARM",
        "campos": "ONG, sector público, educación, justicia, programas sociales y trabajo comunitario.",
        "fortalezas": ["Empatía", "Escucha", "Liderazgo", "Comunicación", "Compromiso"],
        "frase": "Ayudar a otros también es una forma de cambiar el mundo.",
    },
    "Emprendedora": {
        "desc": "Si sueñas con crear tu propio negocio, liderar un proyecto o convertir una idea en realidad, esta área te llama.",
        "evalua": "Tu interés por el liderazgo, los negocios, la innovación y la iniciativa propia.",
        "carreras": ["Administración", "Negocios Internacionales", "Marketing", "Gestión", "Contabilidad", "Agronegocios", "Turismo", "Ingeniería Comercial"],
        "donde": "UNI, UNMSM, PUCP, U. del Pacífico, USIL, SENATI",
        "campos": "Emprendimientos, empresas, banca, ventas, comercio y turismo.",
        "fortalezas": ["Iniciativa", "Liderazgo", "Visión", "Tolerancia al riesgo", "Organización"],
        "frase": "Toda gran empresa empezó con una persona que se atrevió a empezar.",
    },
    "Salud": {
        "desc": "Si te interesa cuidar a las personas, entender el cuerpo humano y ayudar a sanar, esta área es la tuya.",
        "evalua": "Tu interés por la salud, el cuidado de las personas y las ciencias médicas.",
        "carreras": ["Medicina", "Enfermería", "Obstetricia", "Odontología", "Nutrición", "Tecnología Médica", "Farmacia", "Psicología", "Medicina Veterinaria"],
        "donde": "UNMSM, UNASAM, UNT, UPCH (Cayetano), UCSUR",
        "campos": "Hospitales, postas, clínicas, salud pública, laboratorios y trabajo comunitario.",
        "fortalezas": ["Vocación de servicio", "Empatía", "Responsabilidad", "Resistencia", "Atención"],
        "frase": "Cuidar la vida de otros es una de las misiones más valiosas.",
    },
    "Gastronómica": {
        "desc": "Si cocinar te apasiona, si te gusta probar, crear recetas o alimentar bien a los demás, esta área es tu lugar.",
        "evalua": "Tu interés por la cocina, los alimentos y el servicio gastronómico.",
        "carreras": ["Gastronomía", "Arte Culinario", "Administración de Restaurantes", "Industria Alimentaria", "Nutrición", "Pastelería"],
        "donde": "USIL, UCSUR, SENATI, institutos gastronómicos",
        "campos": "Restaurantes, hoteles, turismo, catering, industria alimentaria y emprendimiento.",
        "fortalezas": ["Creatividad", "Disciplina", "Trabajo bajo presión", "Sentido del gusto", "Servicio"],
        "frase": "Cocinar es crear con las manos y compartir con el corazón.",
    },
    "Estética": {
        "desc": "Si te gusta el cuidado personal, la imagen, la moda y la belleza, y quisieras trabajar en eso, esta área te apunta.",
        "evalua": "Tu interés por la estética, el cuidado de la imagen y la moda.",
        "carreras": ["Cosmetología", "Estilismo", "Alta Peluquería", "Diseño de Moda", "Maquillaje Profesional", "Estética Integral", "Imagen Personal"],
        "donde": "SENATI, institutos de belleza y de moda",
        "campos": "Salones, spas, moda, publicidad, belleza y emprendimiento propio.",
        "fortalezas": ["Detalle", "Creatividad", "Trato con clientes", "Sensibilidad estética"],
        "frase": "Cuidar la imagen también es una forma de arte y de negocio.",
    },
    "Deportiva": {
        "desc": "Si el deporte, el movimiento y la actividad física son tu energía diaria, esta área es donde brillas.",
        "evalua": "Tu interés por el deporte, la actividad física y la vida saludable.",
        "carreras": ["Educación Física", "Ciencias del Deporte", "Entrenamiento Deportivo", "Fisioterapia", "Nutrición Deportiva", "Recreación"],
        "donde": "UNASAM, UNT, UNMSM, UPCH",
        "campos": "Escuelas, clubes, academias, gimnasios, selecciones, recreación y salud.",
        "fortalezas": ["Disciplina", "Trabajo en equipo", "Constancia", "Liderazgo", "Salud"],
        "frase": "El deporte también forma profesionales: no solo atletas.",
    },
    "Seguridad, defensa y orden público": {
        "desc": "Si te atrae servir a tu país, proteger a las personas y trabajar con orden y disciplina, esta área es para ti.",
        "evalua": "Tu interés por la seguridad, la defensa, el orden público y el servicio al país.",
        "carreras": ["Oficial de las FF.AA. (EP, MGP, FAP)", "Suboficial de las FF.AA.", "PNP", "Bombero", "Ingeniería Militar", "Seguridad Ciudadana"],
        "donde": "Escuela Militar de Chorrillos, Escuela Naval, EO PNP, INBP",
        "campos": "FF.AA., PNP, serenazgo, seguridad privada, bomberos y gestión de riesgos.",
        "fortalezas": ["Disciplina", "Valor", "Trabajo en equipo", "Liderazgo", "Servicio"],
        "frase": "Servir a tu país es una vocación que deja huella.",
    },
    "Aeronáutica y servicios de vuelo": {
        "desc": "Si te fascina volar, los aviones y todo lo que ocurre en el aire, esta área te espera.",
        "evalua": "Tu interés por la aviación, el vuelo y los servicios aeronáuticos.",
        "carreras": ["Piloto Comercial / Civil", "Tripulante de Cabina", "Controlador Aéreo", "Técnico en Mantenimiento Aeronáutico", "Administración Aeronáutica"],
        "donde": "Escuela de Aviación Civil, FAP, CORPAC, SENATI",
        "campos": "Aerolíneas, aeropuertos, FAP, CORPAC, aviación general y logística aeroportuaria.",
        "fortalezas": ["Responsabilidad", "Precisión", "Serenidad", "Disciplina", "Inglés"],
        "frase": "El cielo también es un campo de trabajo.",
    },
}

# Bloque -> interpretación por nivel (alto >= umbral)
BLOQUES = {
    "Claridad subjetiva": {
        "icono": "🧭",
        "que": "Qué tan claro tienes quién eres y qué te gusta.",
        "alto": "Tienes bastante claro lo que te gusta y hacia dónde quieres ir.",
        "bajo": "Todavía estás descubriendo lo que te gusta. Es normal: se aclara explorando.",
    },
    "Confianza decisional": {
        "icono": "💪",
        "que": "Qué tan seguro te sientes al tomar decisiones.",
        "alto": "Confías en ti al momento de decidir.",
        "bajo": "Decidir te genera dudas. Conversar con personas de confianza ayuda mucho.",
    },
    "Metas personales": {
        "icono": "🎯",
        "que": "Si tienes metas y sueños definidos.",
        "alto": "Tienes metas claras y eso te da dirección.",
        "bajo": "Tus metas están tomando forma; ponerles fecha las hace más reales.",
    },
    "Influencia familiar": {
        "icono": "👨‍👩‍👧",
        "que": "Cuánto pesa la opinión de tu familia en tus decisiones.",
        "alto": "La opinión de tu familia pesa mucho en lo que decides (no es bueno ni malo: es tu contexto).",
        "bajo": "Decides más desde ti mismo, tomando en cuenta a tu familia cuando lo necesitas.",
    },
    "Apoyo familiar": {
        "icono": "🤗",
        "que": "Si sientes que tu familia te respalda.",
        "alto": "Sientes el respaldo de tu familia para seguir adelante.",
        "bajo": "Quizá no sientes ese respaldo; busca aliados: docentes, tutores, personas que te impulsen.",
    },
    "Barreras percibidas": {
        "icono": "🚧",
        "que": "Los obstáculos que sientes que te frenan.",
        "alto": "Sientes varios obstáculos en el camino; conversar y planificar te ayuda a superarlos.",
        "bajo": "Ves pocos obstáculos por delante: buena señal para avanzar con confianza.",
    },
}

# Orden de bloques en el informe
ORDEN_BLOQUES = [
    "Claridad subjetiva", "Confianza decisional", "Metas personales",
    "Apoyo familiar", "Influencia familiar", "Barreras percibidas",
]

MENSAJE_EXPLORAR = {
    "Ciencias": "Está en todo: explorarla te ayuda a entender el mundo.",
    "Numérica": "Muchísimas carreras la usan como herramienta; no necesitas ser «el mejor en mate».",
    "Ingeniería": "Es amplia: del software a los alimentos. Siempre puedes explorarla.",
    "Artística": "El arte no es «solo hobby»: es una profesión con muchas salidas.",
    "Social": "Trabajar con personas se aprende: nunca es tarde para esa habilidad.",
    "Emprendedora": "Emprender también es proponer ideas y liderar donde estés.",
    "Salud": "La salud es un abanico enorme: siempre hay un rol donde encajar.",
    "Gastronómica": "La gastronomía peruana es potencia mundial: una gran oportunidad.",
    "Estética": "Es un mundo amplio: de la moda al bienestar.",
    "Deportiva": "Moverte y enseñar a otros a moverse es una profesión con futuro.",
    "Seguridad, defensa y orden público": "El servicio y la seguridad también abren espacio a muchas profesiones.",
    "Aeronáutica y servicios de vuelo": "La aviación crece en el Perú: es una meta alcanzable con preparación.",
}
