-- ============================================================================
-- CCA Sistema — Esquema de Base de Datos
-- Motor: PostgreSQL 14+ / SQLite 3 (compatible)
-- Versión: 1.0
-- Fecha: 2026-06-25
-- ============================================================================

-- 0. Drop existente si recargamos
DROP TABLE IF EXISTS asignacion CASCADE;
DROP TABLE IF EXISTS iiee_ugt CASCADE;
DROP TABLE IF EXISTS facilitador CASCADE;
DROP TABLE IF EXISTS iiee CASCADE;
DROP TABLE IF EXISTS tipo_iiee CASCADE;
DROP TABLE IF EXISTS ugt CASCADE;
DROP TABLE IF EXISTS centro_poblado CASCADE;
DROP TABLE IF EXISTS distrito CASCADE;
DROP TABLE IF EXISTS provincia CASCADE;

-- ============================================================================
-- 1. Catálogos geográficos
-- ============================================================================

CREATE TABLE provincia (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE distrito (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    provincia_id INTEGER NOT NULL REFERENCES provincia(id),
    UNIQUE(nombre, provincia_id)
);

CREATE TABLE centro_poblado (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(200) NOT NULL,
    distrito_id  INTEGER NOT NULL REFERENCES distrito(id)
);

-- ============================================================================
-- 2. Catálogo UGT
-- ============================================================================

CREATE TABLE ugt (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    codigo      VARCHAR(20)          -- código interno opcional
);

-- ============================================================================
-- 3. Tipo de IIEE (para Inicial - Jardín vs No Escolarizado)
-- ============================================================================

CREATE TABLE tipo_iiee (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO tipo_iiee (nombre) VALUES
    ('INICIAL_JARDIN'),
    ('NO_ESCOLARIZADO');

-- ============================================================================
-- 4. IIEE (Instituciones Educativas)
-- ============================================================================

CREATE TABLE iiee (
    id                SERIAL PRIMARY KEY,
    cod_inst          VARCHAR(20),          -- NULL para No Escolarizado
    cod_modular       VARCHAR(20) NOT NULL UNIQUE,
    cod_local         VARCHAR(20),          -- NULL para No Escolarizado
    nombre            VARCHAR(300) NOT NULL,
    tipo_iiee_id      INTEGER NOT NULL REFERENCES tipo_iiee(id),
    centro_poblado_id INTEGER NOT NULL REFERENCES centro_poblado(id),
    activo            BOOLEAN NOT NULL DEFAULT TRUE,
    observaciones     TEXT,
    creado_en         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_iiee_cod_inst     ON iiee(cod_inst);
CREATE INDEX idx_iiee_cod_modular  ON iiee(cod_modular);

-- ============================================================================
-- 5. Relación IIEE ↔ UGT (N:M — una IIEE puede pertenecer a N UGTs)
--    Ej: Carhuayoc pertenece a UGT Mina y UGT San Marcos
-- ============================================================================

CREATE TABLE iiee_ugt (
    iiee_id INTEGER NOT NULL REFERENCES iiee(id),
    ugt_id  INTEGER NOT NULL REFERENCES ugt(id),
    PRIMARY KEY (iiee_id, ugt_id)
);

-- ============================================================================
-- 6. Facilitadores
-- ============================================================================

CREATE TABLE facilitador (
    id          SERIAL PRIMARY KEY,
    nombres     VARCHAR(200) NOT NULL,
    apellidos   VARCHAR(200) NOT NULL,
    email       VARCHAR(200),
    telefono    VARCHAR(20),
    ugt_id      INTEGER NOT NULL REFERENCES ugt(id),  -- UGT de pertenencia
    activo      BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_facilitador_ugt ON facilitador(ugt_id);

-- ============================================================================
-- 7. Asignaciones (históricas: facilitador → IIEE en una UGT específica)
-- ============================================================================

CREATE TABLE asignacion (
    id            SERIAL PRIMARY KEY,
    facilitador_id INTEGER NOT NULL REFERENCES facilitador(id),
    iiee_id        INTEGER NOT NULL REFERENCES iiee(id),
    ugt_id         INTEGER NOT NULL REFERENCES ugt(id),
    fecha_inicio   DATE NOT NULL,
    fecha_fin      DATE,              -- NULL = vigente
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(facilitador_id, iiee_id, ugt_id, fecha_inicio)
);

CREATE INDEX idx_asignacion_facilitador ON asignacion(facilitador_id);
CREATE INDEX idx_asignacion_iiee        ON asignacion(iiee_id);
CREATE INDEX idx_asignacion_vigente     ON asignacion(activo) WHERE activo = TRUE;

-- ============================================================================
-- 8. ★ Vista: carga actual por facilitador
-- ============================================================================

CREATE OR REPLACE VIEW v_carga_facilitador AS
SELECT
    f.id               AS facilitador_id,
    f.nombres || ' ' || f.apellidos AS facilitador_nombre,
    u.nombre           AS ugt,
    COUNT(a.id)        AS total_iiee_asignadas
FROM facilitador f
JOIN ugt u ON u.id = f.ugt_id
LEFT JOIN asignacion a ON a.facilitador_id = f.id AND a.activo = TRUE
GROUP BY f.id, f.nombres, f.apellidos, u.nombre
ORDER BY u.nombre, f.nombres;

-- ============================================================================
-- 9. ★ Vista: IIEE sin facilitador
-- ============================================================================

CREATE OR REPLACE VIEW v_iiee_sin_facilitador AS
SELECT
    i.id               AS iiee_id,
    COALESCE(i.cod_inst, 'NOESCO-' || i.cod_modular) AS cod_inst_visible,
    i.cod_modular,
    i.nombre           AS iiee_nombre,
    t.nombre           AS tipo,
    cp.nombre          AS centro_poblado,
    d.nombre           AS distrito,
    p.nombre           AS provincia,
    u.nombre           AS ugt
FROM iiee i
JOIN tipo_iiee t        ON t.id = i.tipo_iiee_id
JOIN centro_poblado cp  ON cp.id = i.centro_poblado_id
JOIN distrito d         ON d.id = cp.distrito_id
JOIN provincia p        ON p.id = d.provincia_id
JOIN iiee_ugt iu        ON iu.iiee_id = i.id
JOIN ugt u              ON u.id = iu.ugt_id
WHERE NOT EXISTS (
    SELECT 1 FROM asignacion a
    WHERE a.iiee_id = i.id AND a.ugt_id = iu.ugt_id AND a.activo = TRUE
)
ORDER BY u.nombre, i.nombre;

-- ============================================================================
-- 10. ★ Vista: resumen por UGT
-- ============================================================================

CREATE OR REPLACE VIEW v_resumen_ugt AS
SELECT
    u.nombre              AS ugt,
    COUNT(DISTINCT i.id)  AS total_iiee,
    COUNT(DISTINCT f.id)  AS total_facilitadores,
    COUNT(DISTINCT CASE WHEN i.tipo_iiee_id = 2 THEN i.id END) AS no_escolarizados
FROM ugt u
LEFT JOIN iiee_ugt iu  ON iu.ugt_id = u.id
LEFT JOIN iiee i       ON i.id = iu.iiee_id
LEFT JOIN facilitador f ON f.ugt_id = u.id AND f.activo = TRUE
GROUP BY u.nombre
ORDER BY u.nombre;
