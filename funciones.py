# -*- coding: utf-8 -*-
"""Capital Bikeshare y meteorología de Washington D. C. (2011-2012).

Código del proyecto organizado en funciones.
Los textos explicativos y las conclusiones permanecen en el notebook.
Este módulo se importa desde el notebook; importarlo no descarga ni carga datos.
Las consultas se ejecutan sobre la base MySQL bikeshare ya creada.
"""

import io
import zipfile
from decimal import Decimal
from pathlib import Path

import pandas as pd


# 1. Adquisición de datos.

def descargar_meteorologia():
    """Descargamos los datos diarios de Open-Meteo."""
    import requests

    url_api = "https://archive-api.open-meteo.com/v1/archive"

    parametros = {
        "latitude": 38.8951,             # Washington D. C.
        "longitude": -77.0364,
        "start_date": "2011-01-01",      # mismo periodo que los datos de bicicletas
        "end_date": "2012-12-31",
        "daily": "temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
        "timezone": "America/New_York",  # cada día va de 00:00 a 24:00 en hora de Washington
    }

    response = requests.get(url_api, params=parametros, timeout=60)

    print(response.status_code)

    print(response.url)

    if response.status_code != 200:
        print("Motivo:", response.json().get("reason"))

    response.raise_for_status()

    print("Petición correcta")

    data = response.json()

    weather_df = pd.DataFrame(data["daily"])
    return weather_df


def descargar_bicicletas():
    """Descargamos y leemos day.csv y hour.csv de UCI."""
    import requests

    url_uci = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"

    response_uci = requests.get(url_uci, timeout=60)

    response_uci.raise_for_status()

    print("Código:", response_uci.status_code, "| Tamaño:", round(len(response_uci.content) / 1024), "KB")

    zip_uci = zipfile.ZipFile(io.BytesIO(response_uci.content))

    bikes_day_df = pd.read_csv(zip_uci.open("day.csv"))
    bikes_hour_df = pd.read_csv(zip_uci.open("hour.csv"))
    return bikes_day_df, bikes_hour_df


def leer_bicicletas(ruta_day, ruta_hour):
    """Leemos los CSV de bicicletas si ya están descargados."""
    bikes_day_df = pd.read_csv(ruta_day)
    bikes_hour_df = pd.read_csv(ruta_hour)
    return bikes_day_df, bikes_hour_df


# 2. Fechas y comprobaciones de calidad.

def preparar_fechas(bikes_day_df, bikes_hour_df, weather_df):
    """Convertimos las fechas de las tres tablas con pandas."""
    bikes_day_df = bikes_day_df.copy()
    bikes_hour_df = bikes_hour_df.copy()
    weather_df = weather_df.copy()

    bikes_day_df["dteday"] = pd.to_datetime(bikes_day_df["dteday"])

    bikes_hour_df["dteday"] = pd.to_datetime(bikes_hour_df["dteday"])

    weather_df["time"] = pd.to_datetime(weather_df["time"])

    return bikes_day_df, bikes_hour_df, weather_df


def revisar_datos(bikes_day_df, bikes_hour_df, weather_df):
    """Revisamos fechas, nulos, horas ausentes, totales y códigos."""
    print("Filas y columnas:", weather_df.shape)

    print("Primera fecha:", weather_df["time"].min())

    print("Última fecha:", weather_df["time"].max())

    print("Valores nulos:")

    print(weather_df.isna().sum())

    print(weather_df.describe().round(1))

    print("Día más lluvioso:")

    print(weather_df.loc[weather_df["precipitation_sum"].idxmax()])

    print("Nulos en day.csv:")
    print(bikes_day_df.isna().sum())
    print("Nulos en hour.csv:")
    print(bikes_hour_df.isna().sum())

    print("Fechas duplicadas en bicicletas:",
          bikes_day_df["dteday"].duplicated().sum())

    print("Fechas duplicadas en meteorología:",
          weather_df["time"].duplicated().sum())

    fechas_bicis = set(bikes_day_df["dteday"])

    fechas_tiempo = set(weather_df["time"])

    print("Días en bicicletas:", len(fechas_bicis))

    print("Días en meteorología:", len(fechas_tiempo))

    print("Solo en bicicletas:", sorted(fechas_bicis - fechas_tiempo))

    print("Solo en meteorología:", sorted(fechas_tiempo - fechas_bicis))

    horas_por_dia = bikes_hour_df.groupby("dteday").size()

    print("Filas en hour.csv:", len(bikes_hour_df), "de", 731 * 24)

    print("Días con las 24 horas:", (horas_por_dia == 24).sum())

    print("Días con menos de 24 horas:", (horas_por_dia < 24).sum())

    horas_por_dia.sort_values().head(10)

    dias_sin_esa_hora = len(bikes_day_df) - bikes_hour_df.groupby("hr").size()

    dias_sin_esa_hora.sort_values(ascending=False).head(8)

    dias_incompletos = horas_por_dia[horas_por_dia < 20].rename("horas").reset_index()

    print(dias_incompletos.merge(weather_df, left_on="dteday", right_on="time")[
        ["dteday", "horas", "precipitation_sum", "wind_speed_10m_max", "temperature_2m_mean"]
    ])

    print("day.csv, filas donde casual + registered ≠ cnt:",
          (bikes_day_df["casual"] + bikes_day_df["registered"] != bikes_day_df["cnt"]).sum())

    print("hour.csv, filas donde casual + registered ≠ cnt:",
          (bikes_hour_df["casual"] + bikes_hour_df["registered"] != bikes_hour_df["cnt"]).sum())

    suma_horas = bikes_hour_df.groupby("dteday")["cnt"].sum()

    total_dia = bikes_day_df.set_index("dteday")["cnt"]

    print("Días donde la suma de las horas ≠ day.csv:", (suma_horas != total_dia).sum())

    pd.crosstab(bikes_day_df["mnth"], bikes_day_df["season"])

    weekday_desde_fecha = (bikes_day_df["dteday"].dt.dayofweek + 1) % 7

    print("Días donde weekday no coincide con la fecha:", (weekday_desde_fecha != bikes_day_df["weekday"]).sum())

    bikes_hour_df["weathersit"].value_counts().sort_index()

    comparacion = bikes_day_df[["dteday", "temp"]].merge(weather_df, left_on="dteday", right_on="time")

    print("Correlación entre temp de UCI y temperatura de Open-Meteo:",
          round(comparacion["temp"].corr(comparacion["temperature_2m_mean"]), 3))

    print()

    opciones = {
        "temp × 41 (Readme del zip)": comparacion["temp"] * 41,
        "temp × 47 - 8 (web de UCI)": comparacion["temp"] * 47 - 8,
    }

    for nombre, estimada in opciones.items():
        diferencia = estimada - comparacion["temperature_2m_mean"]
        print(f"{nombre}: diferencia media {diferencia.mean():+.1f} °C | error medio absoluto {diferencia.abs().mean():.1f} °C")


# 3. Preparación de las cuatro tablas relacionadas.

def crear_situacion_meteo():
    """Preparamos los cuatro códigos meteorológicos y su descripción."""
    situacion_meteo = pd.DataFrame({
        "situacion_id": [1, 2, 3, 4],
        "descripcion": [
            "Despejado o poco nuboso",
            "Niebla o nublado",
            "Lluvia o nieve ligera, tormenta",
            "Lluvia fuerte, granizo o nieve",
        ],
    })
    return situacion_meteo


def crear_calendario(bikes_day_df):
    """Preparamos una fila por fecha con sus características."""
    NOMBRES_DIA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

    ESTACIONES = {1: "invierno", 2: "primavera", 3: "verano", 4: "otoño"}

    fecha = bikes_day_df["dteday"]

    calendario = pd.DataFrame({
        "fecha": fecha.dt.strftime("%Y-%m-%d"),
        "anio": fecha.dt.year,
        "mes": fecha.dt.month,
        "dia_semana": fecha.dt.dayofweek + 1,                     # 1 = lunes ... 7 = domingo
        "nombre_dia": fecha.dt.dayofweek.map(dict(enumerate(NOMBRES_DIA))),
        "es_fin_de_semana": (fecha.dt.dayofweek >= 5).astype(int),
        "es_festivo": bikes_day_df["holiday"],
        "es_laborable": bikes_day_df["workingday"],
        "estacion": bikes_day_df["season"].map(ESTACIONES),
    })

    print(calendario.shape)
    return calendario


def crear_meteorologia_dia(weather_df, umbral_lluvia_mm=1.0):
    """Preparamos el tiempo diario y el indicador de precipitación."""
    UMBRAL_LLUVIA_MM = umbral_lluvia_mm

    meteorologia_dia = pd.DataFrame({
        "fecha": weather_df["time"].dt.strftime("%Y-%m-%d"),
        "temp_media_c": weather_df["temperature_2m_mean"],
        "precipitacion_mm": weather_df["precipitation_sum"],
        "viento_max_kmh": weather_df["wind_speed_10m_max"],
        "dia_lluvioso": (weather_df["precipitation_sum"] >= UMBRAL_LLUVIA_MM).astype(int),
    })
    return meteorologia_dia


def crear_alquileres_hora(bikes_hour_df):
    """Preparamos los alquileres por hora y recuperamos las unidades de UCI."""
    TEMP_MIN, TEMP_MAX = -8, 39

    ATEMP_MIN, ATEMP_MAX = -16, 50

    alquileres_hora = pd.DataFrame({
        "fecha": bikes_hour_df["dteday"].dt.strftime("%Y-%m-%d"),
        "hora": bikes_hour_df["hr"],
        "situacion_id": bikes_hour_df["weathersit"],
        "temp_c": (bikes_hour_df["temp"] * (TEMP_MAX - TEMP_MIN) + TEMP_MIN).round(1),
        "sensacion_c": (bikes_hour_df["atemp"] * (ATEMP_MAX - ATEMP_MIN) + ATEMP_MIN).round(1),
        "humedad_pct": (bikes_hour_df["hum"] * 100).round().astype(int),
        "viento": (bikes_hour_df["windspeed"] * 67).round(1),        # UCI no indica la unidad
        "ocasionales": bikes_hour_df["casual"],
        "registrados": bikes_hour_df["registered"],
        "total": bikes_hour_df["cnt"],
    })
    return alquileres_hora


def preparar_tablas(bikes_day_df, bikes_hour_df, weather_df):
    """Reunimos las cuatro tablas en el orden de carga."""
    situacion_meteo = crear_situacion_meteo()
    calendario = crear_calendario(bikes_day_df)
    meteorologia_dia = crear_meteorologia_dia(weather_df)
    alquileres_hora = crear_alquileres_hora(bikes_hour_df)

    return [
        ("situacion_meteo", situacion_meteo),
        ("calendario", calendario),
        ("meteorologia_dia", meteorologia_dia),
        ("alquileres_hora", alquileres_hora),
    ]


def comprobar_claves(tablas):
    """Contamos claves repetidas o referencias inexistentes."""
    datos = dict(tablas)
    situacion_meteo = datos["situacion_meteo"]
    calendario = datos["calendario"]
    meteorologia_dia = datos["meteorologia_dia"]
    alquileres_hora = datos["alquileres_hora"]
    fechas = set(calendario["fecha"])

    comprobaciones = {
        "calendario: fecha repetida": calendario["fecha"].duplicated().sum(),
        "meteorologia_dia: fecha repetida": meteorologia_dia["fecha"].duplicated().sum(),
        "alquileres_hora: fecha y hora repetidas": alquileres_hora.duplicated(["fecha", "hora"]).sum(),
        "meteorologia_dia: fecha que no está en calendario": (~meteorologia_dia["fecha"].isin(fechas)).sum(),
        "alquileres_hora: fecha que no está en calendario": (~alquileres_hora["fecha"].isin(fechas)).sum(),
        "alquileres_hora: código de tiempo desconocido": (~alquileres_hora["situacion_id"].isin(situacion_meteo["situacion_id"])).sum(),
        "calendario: estación sin traducir": calendario["estacion"].isna().sum(),
    }

    pd.Series(comprobaciones, name="problemas")
    return pd.Series(comprobaciones, name="problemas")


def guardar_datos(bikes_day_df, bikes_hour_df, weather_df, tablas, carpeta_proyecto):
    """Guardamos los datos de origen y las cuatro tablas preparadas."""
    proyecto = Path(carpeta_proyecto)
    (proyecto / "data/raw").mkdir(parents=True, exist_ok=True)
    (proyecto / "data/clean").mkdir(parents=True, exist_ok=True)

    for nombre, tabla in [
        ("day", bikes_day_df),
        ("hour", bikes_hour_df),
        ("weather_daily", weather_df),
    ]:
        tabla.to_csv(proyecto / "data/raw" / f"{nombre}.csv", index=False)

    for nombre, tabla in tablas:
        tabla.to_csv(proyecto / "data/clean" / f"{nombre}.csv", index=False)
    return proyecto


# 4. Conexión, esquema y carga en MySQL.

def conectar_mysql(url_conexion):
    """Creamos el engine con la URL de nuestra conexión MySQL."""
    from sqlalchemy import create_engine

    return create_engine(url_conexion)


def obtener_esquema():
    """Devolvemos el esquema SQL original del proyecto."""
    ESQUEMA = """
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
    """
    return ESQUEMA


def guardar_esquema(carpeta_proyecto):
    """Guardamos el esquema en sql/01_schema.sql."""
    carpeta_sql = Path(carpeta_proyecto) / "sql"
    carpeta_sql.mkdir(parents=True, exist_ok=True)
    ruta = carpeta_sql / "01_schema.sql"
    ruta.write_text(obtener_esquema(), encoding="utf-8")
    return ruta


def crear_esquema(engine):
    """Recreamos las tablas: esta función elimina su contenido anterior."""
    from sqlalchemy import text

    with engine.begin() as conexion:
        for instruccion in obtener_esquema().split(";"):
            if instruccion.strip():
                conexion.execute(text(instruccion))


def cargar_tablas(engine, tablas):
    """Añadimos las filas a tablas vacías que ya tienen sus claves definidas."""
    with engine.begin() as conexion:
        for nombre, tabla in tablas:
            tabla.to_sql(
                nombre, conexion, if_exists="append", index=False, chunksize=1000
            )
    return comprobar_carga(engine)


def comprobar_carga(engine):
    """Consultamos cuántas filas contiene cada tabla."""
    return pd.read_sql_query("""
        SELECT 'situacion_meteo' AS tabla, COUNT(*) AS filas FROM situacion_meteo
        UNION ALL SELECT 'calendario',       COUNT(*) FROM calendario
        UNION ALL SELECT 'meteorologia_dia', COUNT(*) FROM meteorologia_dia
        UNION ALL SELECT 'alquileres_hora',  COUNT(*) FROM alquileres_hora
    """, engine)


def probar_clave_foranea(engine):
    """Probamos una referencia inválida y deshacemos siempre la inserción de prueba."""
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    # La prueba es opcional y no forma parte de ejecutar_analisis().
    with engine.connect() as conexion:
        transaccion = conexion.begin()
        try:
            conexion.execute(text(
                "INSERT INTO alquileres_hora "
                "(fecha, hora, situacion_id, ocasionales, registrados, total) "
                "VALUES ('2030-01-01', 8, 1, 1, 1, 2)"
            ))
            print("Cuidado: la clave foránea no se está comprobando.")
        except IntegrityError as error:
            print("Rechazado, como debe ser:", error.orig)
        finally:
            transaccion.rollback()


# 5. Las 15 consultas SQL del análisis.

def ejecutar_consultas(engine):
    """Ejecutamos las mismas 15 consultas y devolvemos resultados y textos SQL."""
    CONSULTAS = {}
    resultados = {}

    def consulta(nombre, sql):
        CONSULTAS[nombre] = sql.strip()
        df = pd.read_sql_query(sql, engine)
        for columna in df.columns:
            if df[columna].map(lambda valor: isinstance(valor, Decimal)).any():
                df[columna] = df[columna].astype(float)
        resultados[nombre] = df
        return df

    resumen_anio = consulta("24a_resumen_por_anio", """
        SELECT anio,
               COUNT(*)                                          AS dias,
               ROUND(AVG(total))                                 AS media,
               MIN(total)                                        AS minimo,
               MAX(total)                                        AS maximo,
               ROUND(STDDEV_SAMP(total))                         AS desviacion,
               ROUND(100 * STDDEV_SAMP(total) / AVG(total), 1)   AS coef_variacion_pct
        FROM v_dia
        GROUP BY anio
        ORDER BY anio
    """)

    resumen_anio

    resumen_estacion = consulta("24b_resumen_por_estacion", """
        SELECT estacion,
               ROUND(AVG(total))             AS media_total,
               ROUND(AVG(registrados))       AS media_registrados,
               ROUND(AVG(ocasionales))       AS media_ocasionales,
               MIN(total)                    AS minimo,
               MAX(total)                    AS maximo,
               ROUND(STDDEV_SAMP(total))     AS desviacion
        FROM v_dia
        GROUP BY estacion
        ORDER BY CASE estacion WHEN 'invierno' THEN 1 WHEN 'primavera' THEN 2
                               WHEN 'verano' THEN 3 ELSE 4 END
    """)

    resumen_estacion

    demanda_hora_dia = consulta("25a_demanda_hora_dia", """
        SELECT c.dia_semana,
               c.nombre_dia,
               a.hora,
               ROUND(AVG(a.total), 1)        AS media_total,
               ROUND(AVG(a.registrados), 1)  AS media_registrados,
               ROUND(AVG(a.ocasionales), 1)  AS media_ocasionales
        FROM alquileres_hora AS a
        JOIN calendario AS c ON c.fecha = a.fecha
        GROUP BY c.dia_semana, c.nombre_dia, a.hora
        ORDER BY c.dia_semana, a.hora
    """)

    print(demanda_hora_dia.shape)

    demanda_hora_dia.head()

    perfil_horario = consulta("25b_perfil_horario_tipo_dia", """
        SELECT CASE WHEN c.es_laborable = 1 THEN 'laborable'
                    ELSE 'fin de semana o festivo' END  AS tipo_dia,
               a.hora,
               ROUND(AVG(a.registrados))                AS media_registrados,
               ROUND(AVG(a.ocasionales))                AS media_ocasionales,
               ROUND(AVG(a.total))                      AS media_total
        FROM alquileres_hora AS a
        JOIN calendario AS c ON c.fecha = a.fecha
        GROUP BY tipo_dia, a.hora
        ORDER BY tipo_dia, a.hora
    """)

    for usuario in ["media_registrados", "media_ocasionales"]:
        print(f"\nHoras con más demanda ({usuario.replace('media_', '')}):")
        print(perfil_horario.sort_values(usuario, ascending=False)
                              .groupby("tipo_dia").head(3)[["tipo_dia", "hora", usuario]]
                              .sort_values(["tipo_dia", usuario], ascending=[True, False]))

    lluvia_tramos = consulta("26a_lluvia_por_tramos", """
        SELECT CASE
                   WHEN precipitacion_mm = 0  THEN '1. 0 mm'
                   WHEN precipitacion_mm < 1  THEN '2. menos de 1 mm'
                   WHEN precipitacion_mm < 5  THEN '3. de 1 a 5 mm'
                   WHEN precipitacion_mm < 10 THEN '4. de 5 a 10 mm'
                   ELSE '5. 10 mm o más'
               END                          AS tramo_lluvia,
               COUNT(*)                     AS dias,
               ROUND(AVG(total))            AS media_total,
               ROUND(AVG(registrados))      AS media_registrados,
               ROUND(AVG(ocasionales))      AS media_ocasionales,
               ROUND(STDDEV_SAMP(total))    AS desviacion_total
        FROM v_dia
        GROUP BY tramo_lluvia
        ORDER BY tramo_lluvia
    """)

    lluvia_tramos

    lluvia_seco = consulta("26b_lluvia_seco_por_anio_tipo_dia", """
        SELECT anio,
               CASE WHEN es_laborable = 1 THEN 'laborable'
                    ELSE 'fin de semana o festivo' END                          AS tipo_dia,
               ROUND(AVG(CASE WHEN dia_lluvioso = 0 THEN registrados END))      AS registrados_seco,
               ROUND(AVG(CASE WHEN dia_lluvioso = 1 THEN registrados END))      AS registrados_lluvia,
               ROUND(100 * (AVG(CASE WHEN dia_lluvioso = 1 THEN registrados END)
                          / AVG(CASE WHEN dia_lluvioso = 0 THEN registrados END) - 1), 1)
                                                                                 AS dif_registrados_pct,
               ROUND(AVG(CASE WHEN dia_lluvioso = 0 THEN ocasionales END))      AS ocasionales_seco,
               ROUND(AVG(CASE WHEN dia_lluvioso = 1 THEN ocasionales END))      AS ocasionales_lluvia,
               ROUND(100 * (AVG(CASE WHEN dia_lluvioso = 1 THEN ocasionales END)
                          / AVG(CASE WHEN dia_lluvioso = 0 THEN ocasionales END) - 1), 1)
                                                                                 AS dif_ocasionales_pct
        FROM v_dia
        GROUP BY anio, tipo_dia
        ORDER BY anio, tipo_dia
    """)

    lluvia_seco

    temperatura = consulta("27_demanda_por_temperatura", """
        SELECT FLOOR(temp_media_c / 5) * 5       AS desde_c,
               FLOOR(temp_media_c / 5) * 5 + 5   AS hasta_c,
               COUNT(*)                          AS dias,
               ROUND(AVG(total))                 AS media_total,
               ROUND(AVG(registrados))           AS media_registrados,
               ROUND(AVG(ocasionales))           AS media_ocasionales
        FROM v_dia
        GROUP BY desde_c, hasta_c
        ORDER BY desde_c
    """)

    temperatura

    mantenimiento = consulta("28a_horas_mantenimiento", """
        WITH media_hora AS (
            SELECT c.estacion,
                   CASE WHEN c.es_laborable = 1 THEN 'laborable'
                        ELSE 'fin de semana o festivo' END  AS tipo_dia,
                   a.hora,
                   AVG(a.total)                             AS media_total
            FROM alquileres_hora AS a
            JOIN calendario AS c ON c.fecha = a.fecha
            GROUP BY c.estacion, tipo_dia, a.hora
        ),
        ranking AS (
            SELECT estacion, tipo_dia, hora,
                   ROUND(media_total, 1)                                                  AS media_total,
                   RANK() OVER (PARTITION BY estacion, tipo_dia ORDER BY media_total)     AS puesto
            FROM media_hora
        )
        SELECT estacion, tipo_dia, puesto, hora, media_total
        FROM ranking
        WHERE puesto <= 3
        ORDER BY CASE estacion WHEN 'invierno' THEN 1 WHEN 'primavera' THEN 2
                               WHEN 'verano' THEN 3 ELSE 4 END,
                 tipo_dia, puesto
    """)

    (mantenimiento.assign(hora_y_media=mantenimiento["hora"].astype(str) + " h (" +
                                       mantenimiento["media_total"].astype(str) + ")")
                  .pivot(index=["estacion", "tipo_dia"], columns="puesto", values="hora_y_media")
                  .reindex(["invierno", "primavera", "verano", "otoño"], level=0))

    consulta("28b_peso_madrugada", """
        SELECT ROUND(100 * SUM(CASE WHEN hora BETWEEN 1 AND 5 THEN total ELSE 0 END)
                         / SUM(total), 2)                                          AS pct_alquileres_1_a_6h,
               ROUND(100 * SUM(CASE WHEN hora BETWEEN 7 AND 9 OR hora BETWEEN 16 AND 19
                                    THEN total ELSE 0 END) / SUM(total), 1)        AS pct_alquileres_horas_punta
        FROM alquileres_hora
    """)

    refuerzo = consulta("29_dias_de_refuerzo", """
        WITH dias AS (
            SELECT fecha, anio, estacion, es_laborable, dia_lluvioso, temp_media_c, total,
                   RANK() OVER (PARTITION BY anio ORDER BY total DESC) AS puesto
            FROM v_dia
        )
        SELECT CASE WHEN puesto <= 37 THEN 'los 37 días de más demanda de cada año'
                    ELSE 'resto de días' END                                           AS grupo,
               COUNT(*)                                                                 AS dias,
               ROUND(AVG(total))                                                        AS media_total,
               ROUND(AVG(temp_media_c), 1)                                              AS temp_media_c,
               ROUND(100 * AVG(dia_lluvioso), 1)                                        AS pct_dias_lluvia,
               ROUND(100 * AVG(es_laborable), 1)                                        AS pct_laborables,
               ROUND(100 * AVG(CASE WHEN estacion = 'invierno' THEN 1 ELSE 0 END), 1)   AS pct_invierno,
               ROUND(100 * AVG(CASE WHEN estacion = 'primavera' THEN 1 ELSE 0 END), 1)  AS pct_primavera,
               ROUND(100 * AVG(CASE WHEN estacion = 'verano' THEN 1 ELSE 0 END), 1)     AS pct_verano,
               ROUND(100 * AVG(CASE WHEN estacion = 'otoño' THEN 1 ELSE 0 END), 1)      AS pct_otono
        FROM dias
        GROUP BY grupo
        ORDER BY grupo
    """)

    refuerzo

    crecimiento = consulta("30_crecimiento_mensual", """
        WITH mensual AS (
            SELECT anio, mes,
                   SUM(total)        AS total,
                   SUM(registrados)  AS registrados,
                   SUM(ocasionales)  AS ocasionales
            FROM v_dia
            GROUP BY anio, mes
        )
        SELECT anio, mes, total, registrados, ocasionales,
               LAG(total, 12) OVER (ORDER BY anio, mes)                                        AS total_anio_anterior,
               ROUND(100 * (total / LAG(total, 12) OVER (ORDER BY anio, mes) - 1), 1)             AS crec_total_pct,
               ROUND(100 * (registrados / LAG(registrados, 12) OVER (ORDER BY anio, mes) - 1), 1) AS crec_registrados_pct,
               ROUND(100 * (ocasionales / LAG(ocasionales, 12) OVER (ORDER BY anio, mes) - 1), 1) AS crec_ocasionales_pct
        FROM mensual
        ORDER BY anio, mes
    """)

    crecimiento[crecimiento["anio"] == 2012]

    consulta("30b_crecimiento_anual_por_usuario", """
        SELECT ROUND(100 * (AVG(CASE WHEN anio = 2012 THEN registrados END)
                          / AVG(CASE WHEN anio = 2011 THEN registrados END) - 1), 1)  AS crec_registrados_pct,
               ROUND(100 * (AVG(CASE WHEN anio = 2012 THEN ocasionales END)
                          / AVG(CASE WHEN anio = 2011 THEN ocasionales END) - 1), 1)  AS crec_ocasionales_pct,
               ROUND(100 * (AVG(CASE WHEN anio = 2012 THEN total END)
                          / AVG(CASE WHEN anio = 2011 THEN total END) - 1), 1)        AS crec_total_pct
        FROM v_dia
    """)

    media_movil = consulta("31a_media_movil_7_dias", """
        WITH dias AS (
            SELECT fecha, total
            FROM v_dia
        )
        SELECT d.fecha,
               d.total,
               ROUND((SELECT AVG(d2.total)
                      FROM dias AS d2
                      WHERE DATEDIFF(d.fecha, d2.fecha) BETWEEN 0 AND 6)) AS media_movil_7d
        FROM dias AS d
        ORDER BY d.fecha
    """)

    media_movil["fecha"] = pd.to_datetime(media_movil["fecha"])

    media_movil.tail()

    atipicos = consulta("31b_dias_atipicos", """
        WITH dias AS (
            SELECT fecha, nombre_dia, es_laborable, total,
                   precipitacion_mm, temp_media_c, viento_max_kmh
            FROM v_dia
        ),
        con_media AS (
            SELECT d.*,
                   (SELECT AVG(d2.total)
                    FROM dias AS d2
                    WHERE DATEDIFF(d.fecha, d2.fecha) BETWEEN 1 AND 7) AS media_7d_previa
            FROM dias AS d
        )
        SELECT fecha, nombre_dia, es_laborable, total,
               ROUND(media_7d_previa)                AS media_7d_previa,
               ROUND(100 * total / media_7d_previa)  AS pct_de_la_media,
               precipitacion_mm, temp_media_c, viento_max_kmh
        FROM con_media
        WHERE total < 0.5 * media_7d_previa
        ORDER BY fecha
    """)

    atipicos["fecha"] = pd.to_datetime(atipicos["fecha"])

    print("Días atípicos:", len(atipicos))

    atipicos

    ocasionales = consulta("32_momentos_ocasionales", """
        SELECT c.estacion,
               CASE WHEN c.es_laborable = 1 THEN 'laborable'
                    ELSE 'fin de semana o festivo' END           AS tipo_dia,
               a.hora,
               ROUND(100 * SUM(a.ocasionales) / SUM(a.total), 1) AS pct_ocasionales,
               ROUND(AVG(a.ocasionales))                         AS media_ocasionales
        FROM alquileres_hora AS a
        JOIN calendario AS c ON c.fecha = a.fecha
        GROUP BY c.estacion, tipo_dia, a.hora
        ORDER BY media_ocasionales DESC
    """)

    print("Los 10 momentos con más usuarios ocasionales:")

    ocasionales.head(10)

    return resultados, CONSULTAS


def guardar_consultas(consultas, carpeta_proyecto):
    """Guardamos la recopilación de consultas en sql/02_queries.sql."""
    carpeta_sql = Path(carpeta_proyecto) / "sql"
    carpeta_sql.mkdir(parents=True, exist_ok=True)
    texto_sql = "-- Consultas del proyecto Bikeshare. MySQL 8.\n\nUSE bikeshare;\n"
    for nombre, sql in consultas.items():
        texto_sql += f"\n-- {nombre}\n{sql};\n"
    ruta = carpeta_sql / "02_queries.sql"
    ruta.write_text(texto_sql, encoding="utf-8")
    print(len(consultas), "consultas guardadas en", ruta)
    return ruta


# 6. Los siete gráficos del proyecto.

def crear_graficos(resultados, carpeta_proyecto):
    """Creamos y guardamos los siete gráficos con el diseño original."""
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import seaborn as sns
    from matplotlib.colors import LinearSegmentedColormap

    demanda_hora_dia = resultados['25a_demanda_hora_dia']
    perfil_horario = resultados['25b_perfil_horario_tipo_dia']
    lluvia_tramos = resultados['26a_lluvia_por_tramos']
    temperatura = resultados['27_demanda_por_temperatura']
    crecimiento = resultados['30_crecimiento_mensual']
    media_movil = resultados['31a_media_movil_7_dias']
    atipicos = resultados['31b_dias_atipicos']
    ocasionales = resultados['32_momentos_ocasionales']

    AZUL = "#2a78d6"

    NARANJA = "#eb6834"

    GRIS = "#b3b2ad"

    ROJO = "#d03b3b"

    TINTA = "#0b0b0b"

    TINTA_2 = "#52514e"

    AZULES = LinearSegmentedColormap.from_list(
        "azules", ["#f4f8fd", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])

    NARANJAS = LinearSegmentedColormap.from_list(
        "naranjas", ["#fdf5f1", "#fbd9c9", "#f5a47f", "#eb6834", "#b8461c", "#7a2d10"])

    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150, "figure.facecolor": "white",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#d6d5d0", "axes.linewidth": 0.8,
        "axes.grid": True, "grid.color": "#ecebe7", "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelcolor": TINTA_2, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
        "text.color": TINTA, "lines.linewidth": 2, "lines.solid_capstyle": "round",
        "legend.frameon": False,
    })

    carpeta_figuras = Path(carpeta_proyecto) / "figuras"
    carpeta_figuras.mkdir(parents=True, exist_ok=True)

    def guardar(figura, nombre):
        """Guarda la figura en figuras/ con márgenes ajustados."""
        figura.savefig(carpeta_figuras / f"{nombre}.png", bbox_inches="tight")

    miles = mticker.FuncFormatter(lambda valor, _: f"{valor:,.0f}".replace(",", "."))

    matriz = demanda_hora_dia.pivot(index="nombre_dia", columns="hora", values="media_total")

    matriz = matriz.reindex(["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"])

    fig, ax = plt.subplots(figsize=(13, 4.2))

    sns.heatmap(matriz, cmap=AZULES, linewidths=1, linecolor="white",
                cbar_kws={"label": "Alquileres medios por hora", "shrink": 0.8}, ax=ax)

    ax.set_title("Laborables: picos a las 8 h y a las 17-18 h. Fines de semana: demanda de mediodía")

    ax.set_xlabel("Hora del día")

    ax.set_ylabel("")

    ax.tick_params(axis="y", rotation=0)

    ax.grid(False)

    guardar(fig, "01_mapa_calor_hora_dia")

    plt.show()

    fig, ejes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)

    for ax, tipo in zip(ejes, ["laborable", "fin de semana o festivo"]):
        datos = perfil_horario[perfil_horario["tipo_dia"] == tipo]
        ax.plot(datos["hora"], datos["media_registrados"], color=AZUL, label="Registrados")
        ax.plot(datos["hora"], datos["media_ocasionales"], color=NARANJA, label="Ocasionales")
        ax.set_title(tipo.capitalize())
        ax.set_xlabel("Hora del día")
        ax.set_xticks(range(0, 24, 2))
        # Etiqueta directa en el máximo de cada serie
        for columna, color in [("media_registrados", AZUL), ("media_ocasionales", NARANJA)]:
            fila = datos.loc[datos[columna].idxmax()]
            ax.scatter(fila["hora"], fila[columna], color=color, s=40, zorder=3, edgecolor="white", linewidth=2)
            ax.annotate(f"{fila[columna]:.0f} a las {fila['hora']:.0f} h", (fila["hora"], fila[columna]),
                        xytext=(6, 6), textcoords="offset points", fontsize=9, color=TINTA_2)
        if tipo == "laborable":   # el pico de la mañana también se etiqueta
            fila = datos[datos["hora"] == 8].iloc[0]
            ax.scatter(8, fila["media_registrados"], color=AZUL, s=40, zorder=3, edgecolor="white", linewidth=2)
            ax.annotate(f"{fila['media_registrados']:.0f} a las 8 h", (8, fila["media_registrados"]),
                        xytext=(-70, 4), textcoords="offset points", fontsize=9, color=TINTA_2)

    ejes[0].set_ylabel("Alquileres medios por hora")

    ejes[1].legend(loc="upper right")

    fig.suptitle("Registrados: picos de ida y vuelta al trabajo. Ocasionales: tardes de fin de semana",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")

    fig.tight_layout()

    guardar(fig, "02_perfil_horario_usuarios")

    plt.show()

    base = lluvia_tramos.iloc[0]

    indice = lluvia_tramos.assign(
        registrados=100 * lluvia_tramos["media_registrados"] / base["media_registrados"],
        ocasionales=100 * lluvia_tramos["media_ocasionales"] / base["media_ocasionales"],
        etiqueta=lluvia_tramos["tramo_lluvia"].str[3:] + "\n(" + lluvia_tramos["dias"].astype(int).astype(str) + " días)",
    )

    posiciones = range(len(indice))

    ancho = 0.36

    fig, ax = plt.subplots(figsize=(11, 4.5))

    for desplazamiento, columna, color, nombre in [(-ancho / 2, "registrados", AZUL, "Registrados"),
                                                   (ancho / 2, "ocasionales", NARANJA, "Ocasionales")]:
        barras = ax.bar([p + desplazamiento for p in posiciones], indice[columna], width=ancho - 0.03,
                        color=color, label=nombre)
        ax.bar_label(barras, fmt="%.0f %%", padding=3, fontsize=9, color=TINTA_2)

    ax.axhline(100, color=TINTA_2, linewidth=1)

    ax.set_xticks(list(posiciones), indice["etiqueta"])

    ax.set_ylabel("% de la media de un día sin lluvia")

    ax.set_ylim(0, 120)

    ax.set_title("La lluvia fuerte (10 mm o más) resta un 36 % de registrados y un 43 % de ocasionales")

    ax.legend(loc="upper right")

    guardar(fig, "03_efecto_lluvia")

    plt.show()

    centro = temperatura["desde_c"] + 2.5

    fig, ax = plt.subplots(figsize=(11, 4.5))

    ax.plot(centro, temperatura["media_registrados"], color=AZUL, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=2, label="Registrados")

    ax.plot(centro, temperatura["media_ocasionales"], color=NARANJA, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=2, label="Ocasionales")

    for x, y, dias in zip(centro, temperatura["media_registrados"], temperatura["dias"]):
        ax.annotate(f"{dias:.0f} d", (x, y), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8, color=TINTA_2)

    ax.set_xticks(list(centro), [f"{d:.0f} a {h:.0f}" for d, h in zip(temperatura["desde_c"], temperatura["hasta_c"])])

    ax.set_xlabel("Temperatura media del día (°C)")

    ax.set_ylabel("Alquileres medios por día")

    ax.yaxis.set_major_formatter(miles)

    ax.set_title("La demanda sube hasta los 15 °C, se mantiene hasta los 30 °C y baja con más calor")

    ax.legend(loc="upper left")

    guardar(fig, "04_temperatura")

    plt.show()

    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

    datos_2011 = crecimiento[crecimiento["anio"] == 2011]

    datos_2012 = crecimiento[crecimiento["anio"] == 2012]

    fig, ax = plt.subplots(figsize=(12, 4.5))

    ax.plot(datos_2011["mes"], datos_2011["total"], color=GRIS, marker="o", markersize=6, label="2011")

    ax.plot(datos_2012["mes"], datos_2012["total"], color=AZUL, marker="o", markersize=7,
            markeredgecolor="white", markeredgewidth=2, label="2012")

    for mes, total, crec in zip(datos_2012["mes"], datos_2012["total"], datos_2012["crec_total_pct"]):
        ax.annotate(f"+{crec:.0f} %", (mes, total), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8, color=TINTA_2)

    ax.set_xticks(range(1, 13), meses)

    ax.set_ylabel("Alquileres del mes")

    ax.yaxis.set_major_formatter(miles)

    ax.set_title("2012 supera a 2011 todos los meses; los mayores saltos, de enero a marzo")

    ax.legend(loc="upper left")

    guardar(fig, "05_crecimiento_mensual")

    plt.show()

    fig, ax = plt.subplots(figsize=(13, 4.8))

    ax.plot(media_movil["fecha"], media_movil["total"], color=GRIS, linewidth=0.8, label="Alquileres del día")

    ax.plot(media_movil["fecha"], media_movil["media_movil_7d"], color=AZUL, label="Media móvil de 7 días")

    ax.scatter(atipicos["fecha"], atipicos["total"], color=ROJO, s=36, zorder=3,
               edgecolor="white", linewidth=1.5, label="Día atípico (< 50 % de la semana previa)")

    eventos = {"2011-01-26": ("Temporal de invierno", (0, 62)),
               "2011-08-27": ("Huracán Irene", (-70, -10)),
               "2012-10-29": ("Huracán Sandy", (-85, 8)),
               "2012-12-25": ("Navidad", (-55, -18))}

    for fecha, (nombre, desplazamiento) in eventos.items():
        fila = atipicos[atipicos["fecha"] == fecha].iloc[0]
        ax.annotate(f"{nombre}\n{fila['precipitacion_mm']:.0f} mm", (fila["fecha"], fila["total"]),
                    xytext=desplazamiento, textcoords="offset points", fontsize=8, color=TINTA_2,
                    arrowprops={"arrowstyle": "-", "color": TINTA_2, "linewidth": 0.6})

    ax.set_ylabel("Alquileres por día")

    ax.yaxis.set_major_formatter(miles)

    ax.set_title("La tendencia crece; las caídas bruscas coinciden con temporales y con Navidad")

    ax.legend(loc="upper left", fontsize=9)

    guardar(fig, "06_tendencia_atipicos")

    plt.show()

    finde = ocasionales[ocasionales["tipo_dia"] == "fin de semana o festivo"]

    matriz_oca = (finde.pivot(index="estacion", columns="hora", values="media_ocasionales")
                       .reindex(["invierno", "primavera", "verano", "otoño"]))

    fig, ax = plt.subplots(figsize=(13, 3.4))

    sns.heatmap(matriz_oca, cmap=NARANJAS, linewidths=1, linecolor="white",
                cbar_kws={"label": "Ocasionales medios por hora", "shrink": 0.8}, ax=ax)

    ax.set_title("Fines de semana de primavera y verano, de 12 a 17 h: el momento para captar abonados")

    ax.set_xlabel("Hora del día")

    ax.set_ylabel("")

    ax.tick_params(axis="y", rotation=0)

    ax.grid(False)

    guardar(fig, "07_momentos_ocasionales")

    plt.show()

    return sorted(carpeta_figuras.glob("*.png"))


# 7. Funciones que reúnen los pasos anteriores.

def preparar_datos(carpeta_proyecto):
    """Descargamos, revisamos, transformamos y guardamos los datos del proyecto."""
    weather_df = descargar_meteorologia()
    bikes_day_df, bikes_hour_df = descargar_bicicletas()
    bikes_day_df, bikes_hour_df, weather_df = preparar_fechas(
        bikes_day_df, bikes_hour_df, weather_df
    )
    revisar_datos(bikes_day_df, bikes_hour_df, weather_df)
    tablas = preparar_tablas(bikes_day_df, bikes_hour_df, weather_df)
    problemas = comprobar_claves(tablas)
    print(problemas)
    if problemas.sum() != 0:
        raise ValueError("Hay problemas en las claves. Revisamos los datos antes de cargar.")
    guardar_datos(bikes_day_df, bikes_hour_df, weather_df, tablas, carpeta_proyecto)
    guardar_esquema(carpeta_proyecto)
    return tablas


def ejecutar_analisis(engine, carpeta_proyecto):
    """Analizamos la base ya cargada y guardamos consultas, resultados y gráficos."""
    print(comprobar_carga(engine))
    resultados, consultas = ejecutar_consultas(engine)
    guardar_consultas(consultas, carpeta_proyecto)
    carpeta_resultados = Path(carpeta_proyecto) / "resultados"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(carpeta_resultados / f"{nombre}.csv", index=False)
    crear_graficos(resultados, carpeta_proyecto)
    return resultados


# Uso desde el notebook, después de crear la conexión engine:
# import funciones as proyecto
# resultados = proyecto.ejecutar_analisis(engine, "ruta/a/nuestro/proyecto")
#
# Si se reconstruye la base desde cero, en este orden:
# tablas = proyecto.preparar_datos("ruta/a/nuestro/proyecto")
# proyecto.crear_esquema(engine)  # Borra y recrea las tablas.
# proyecto.cargar_tablas(engine, tablas)
# proyecto.ejecutar_analisis(engine, "ruta/a/nuestro/proyecto")
#
# La instalación de MySQL, la conexión de Colab con Drive y mysqldump
# se ejecutan en Colab o desde las herramientas de MySQL, no en este módulo.
# El volcado 03_bikeshare_dump.sql y el informe se entregan por separado.
