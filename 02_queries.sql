-- Consultas del análisis (parte 3 del notebook). Base de datos: bikeshare (MySQL 8).

USE bikeshare;

-- 24a_resumen_por_anio
SELECT anio,
           COUNT(*)                                          AS dias,
           ROUND(AVG(total))                                 AS media,
           MIN(total)                                        AS minimo,
           MAX(total)                                        AS maximo,
           ROUND(STDDEV_SAMP(total))                         AS desviacion,
           ROUND(100 * STDDEV_SAMP(total) / AVG(total), 1)   AS coef_variacion_pct
    FROM v_dia
    GROUP BY anio
    ORDER BY anio;

-- 24b_resumen_por_estacion
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
                           WHEN 'verano' THEN 3 ELSE 4 END;

-- 25a_demanda_hora_dia
SELECT c.dia_semana,
           c.nombre_dia,
           a.hora,
           ROUND(AVG(a.total), 1)        AS media_total,
           ROUND(AVG(a.registrados), 1)  AS media_registrados,
           ROUND(AVG(a.ocasionales), 1)  AS media_ocasionales
    FROM alquileres_hora AS a
    JOIN calendario AS c ON c.fecha = a.fecha
    GROUP BY c.dia_semana, c.nombre_dia, a.hora
    ORDER BY c.dia_semana, a.hora;

-- 25b_perfil_horario_tipo_dia
SELECT CASE WHEN c.es_laborable = 1 THEN 'laborable'
                ELSE 'fin de semana o festivo' END  AS tipo_dia,
           a.hora,
           ROUND(AVG(a.registrados))                AS media_registrados,
           ROUND(AVG(a.ocasionales))                AS media_ocasionales,
           ROUND(AVG(a.total))                      AS media_total
    FROM alquileres_hora AS a
    JOIN calendario AS c ON c.fecha = a.fecha
    GROUP BY tipo_dia, a.hora
    ORDER BY tipo_dia, a.hora;

-- 26a_lluvia_por_tramos
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
    ORDER BY tramo_lluvia;

-- 26b_lluvia_seco_por_anio_tipo_dia
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
    ORDER BY anio, tipo_dia;

-- 27_demanda_por_temperatura
SELECT FLOOR(temp_media_c / 5) * 5       AS desde_c,
           FLOOR(temp_media_c / 5) * 5 + 5   AS hasta_c,
           COUNT(*)                          AS dias,
           ROUND(AVG(total))                 AS media_total,
           ROUND(AVG(registrados))           AS media_registrados,
           ROUND(AVG(ocasionales))           AS media_ocasionales
    FROM v_dia
    GROUP BY desde_c, hasta_c
    ORDER BY desde_c;

-- 28a_horas_mantenimiento
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
             tipo_dia, puesto;

-- 28b_peso_madrugada
SELECT ROUND(100 * SUM(CASE WHEN hora BETWEEN 1 AND 5 THEN total ELSE 0 END)
                     / SUM(total), 2)                                          AS pct_alquileres_1_a_6h,
           ROUND(100 * SUM(CASE WHEN hora BETWEEN 7 AND 9 OR hora BETWEEN 16 AND 19
                                THEN total ELSE 0 END) / SUM(total), 1)        AS pct_alquileres_horas_punta
    FROM alquileres_hora;

-- 29_dias_de_refuerzo
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
    ORDER BY grupo;

-- 30_crecimiento_mensual
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
    ORDER BY anio, mes;

-- 30b_crecimiento_anual_por_usuario
SELECT ROUND(100 * (AVG(CASE WHEN anio = 2012 THEN registrados END)
                      / AVG(CASE WHEN anio = 2011 THEN registrados END) - 1), 1)  AS crec_registrados_pct,
           ROUND(100 * (AVG(CASE WHEN anio = 2012 THEN ocasionales END)
                      / AVG(CASE WHEN anio = 2011 THEN ocasionales END) - 1), 1)  AS crec_ocasionales_pct,
           ROUND(100 * (AVG(CASE WHEN anio = 2012 THEN total END)
                      / AVG(CASE WHEN anio = 2011 THEN total END) - 1), 1)        AS crec_total_pct
    FROM v_dia;

-- 31a_media_movil_7_dias
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
    ORDER BY d.fecha;

-- 31b_dias_atipicos
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
    ORDER BY fecha;

-- 32_momentos_ocasionales
SELECT c.estacion,
           CASE WHEN c.es_laborable = 1 THEN 'laborable'
                ELSE 'fin de semana o festivo' END           AS tipo_dia,
           a.hora,
           ROUND(100 * SUM(a.ocasionales) / SUM(a.total), 1) AS pct_ocasionales,
           ROUND(AVG(a.ocasionales))                         AS media_ocasionales
    FROM alquileres_hora AS a
    JOIN calendario AS c ON c.fecha = a.fecha
    GROUP BY c.estacion, tipo_dia, a.hora
    ORDER BY media_ocasionales DESC;
