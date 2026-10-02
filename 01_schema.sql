
-- Capital Bikeshare y el tiempo en Washington D. C. (2011-2012). Esquema para MySQL 8.
-- Se borra primero lo que depende de otras tablas, para poder ejecutarlo varias veces.

DROP VIEW IF EXISTS v_dia;
DROP TABLE IF EXISTS alquileres_hora;
DROP TABLE IF EXISTS meteorologia_dia;
DROP TABLE IF EXISTS calendario;
DROP TABLE IF EXISTS situacion_meteo;

CREATE TABLE situacion_meteo (
    situacion_id  TINYINT      NOT NULL,
    descripcion   VARCHAR(60)  NOT NULL,
    PRIMARY KEY (situacion_id)
) ENGINE = InnoDB;

CREATE TABLE calendario (
    fecha             DATE         NOT NULL,
    anio              SMALLINT     NOT NULL,
    mes               TINYINT      NOT NULL,
    dia_semana        TINYINT      NOT NULL,   -- 1 = lunes ... 7 = domingo
    nombre_dia        VARCHAR(10)  NOT NULL,
    es_fin_de_semana  TINYINT      NOT NULL,   -- 0 / 1
    es_festivo        TINYINT      NOT NULL,   -- 0 / 1
    es_laborable      TINYINT      NOT NULL,   -- 1 si no es fin de semana ni festivo
    estacion          VARCHAR(10)  NOT NULL,
    PRIMARY KEY (fecha),
    CHECK (dia_semana BETWEEN 1 AND 7)
) ENGINE = InnoDB;

CREATE TABLE meteorologia_dia (
    fecha             DATE          NOT NULL,
    temp_media_c      DECIMAL(4,1),
    precipitacion_mm  DECIMAL(5,1),
    viento_max_kmh    DECIMAL(5,1),
    dia_lluvioso      TINYINT       NOT NULL,  -- 1 si precipitacion_mm >= 1
    PRIMARY KEY (fecha),
    FOREIGN KEY (fecha) REFERENCES calendario (fecha)
) ENGINE = InnoDB;

CREATE TABLE alquileres_hora (
    fecha          DATE          NOT NULL,
    hora           TINYINT       NOT NULL,     -- 0 a 23, hora local de Washington
    situacion_id   TINYINT       NOT NULL,
    temp_c         DECIMAL(4,1),
    sensacion_c    DECIMAL(4,1),
    humedad_pct    TINYINT,
    viento         DECIMAL(4,1),
    ocasionales    SMALLINT      NOT NULL,
    registrados    SMALLINT      NOT NULL,
    total          SMALLINT      NOT NULL,
    PRIMARY KEY (fecha, hora),
    FOREIGN KEY (fecha) REFERENCES calendario (fecha),
    FOREIGN KEY (situacion_id) REFERENCES situacion_meteo (situacion_id),
    CHECK (hora BETWEEN 0 AND 23),
    CHECK (total = ocasionales + registrados)
) ENGINE = InnoDB;

CREATE VIEW v_dia AS
SELECT
    c.fecha, c.anio, c.mes, c.dia_semana, c.nombre_dia,
    c.es_fin_de_semana, c.es_festivo, c.es_laborable, c.estacion,
    m.temp_media_c, m.precipitacion_mm, m.viento_max_kmh, m.dia_lluvioso,
    SUM(a.ocasionales) AS ocasionales,
    SUM(a.registrados) AS registrados,
    SUM(a.total)       AS total
FROM calendario AS c
JOIN meteorologia_dia AS m ON m.fecha = c.fecha
JOIN alquileres_hora  AS a ON a.fecha = c.fecha
GROUP BY
    c.fecha, c.anio, c.mes, c.dia_semana, c.nombre_dia,
    c.es_fin_de_semana, c.es_festivo, c.es_laborable, c.estacion,
    m.temp_media_c, m.precipitacion_mm, m.viento_max_kmh, m.dia_lluvioso;
